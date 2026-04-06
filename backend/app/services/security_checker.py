"""Security scanning service using AST node inspection."""
import ast
import re
import logging
from typing import List

from app.models.analysis_result import Issue

logger = logging.getLogger(__name__)

# Dangerous function calls to detect
DANGEROUS_CALLS = {
    "eval": ("Dangerous use of eval() — can execute arbitrary code", "high"),
    "exec": ("Dangerous use of exec() — can execute arbitrary code", "high"),
    "compile": ("Use of compile() — potential code injection risk", "medium"),
    "__import__": ("Dynamic import via __import__() — verify necessity", "medium"),
}

# Subprocess-related names
SUBPROCESS_NAMES = {"subprocess", "os.system", "os.popen", "popen"}

# Unsafe file operations
UNSAFE_FILE_CALLS = {"open", "os.remove", "os.unlink", "shutil.rmtree"}

# Regex patterns for hardcoded secrets
SECRET_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']'), "Hardcoded password detected", "high"),
    (re.compile(r'(?i)(api_key|apikey|secret_key|token)\s*=\s*["\'][^"\']{6,}["\']'), "Hardcoded API key or secret detected", "high"),
    (re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*["\'][^"\']{6,}["\']'), "Hardcoded AWS credential detected", "high"),
]


class _SecurityVisitor(ast.NodeVisitor):
    """AST visitor that collects security issues."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.issues: List[Issue] = []

    def _add(self, node: ast.AST, type_: str, message: str, severity: str) -> None:
        self.issues.append(Issue(
            file=self.filename,
            line=getattr(node, "lineno", 0),
            type=type_,
            message=message,
            severity=severity,
        ))

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        """Check function calls for dangerous patterns."""
        # Direct function name check
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in DANGEROUS_CALLS:
                msg, sev = DANGEROUS_CALLS[name]
                self._add(node, "SecurityWarning", msg, sev)
            elif name == "open":
                self._add(node, "SecurityWarning", "File open() detected — verify path is not user-controlled", "low")

        # Attribute access (e.g. subprocess.call, os.system)
        elif isinstance(node.func, ast.Attribute):
            full = f"{getattr(node.func.value, 'id', '')}. {node.func.attr}".replace(" ", "")
            if "subprocess" in full or node.func.attr in {"system", "popen", "call", "run", "Popen"}:
                self._add(node, "SecurityWarning",
                          f"subprocess/os usage detected ({node.func.attr}) — avoid passing unsanitised input", "high")

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "subprocess":
                self._add(node, "SecurityWarning", "subprocess module imported — review all usage carefully", "medium")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module and "subprocess" in node.module:
            self._add(node, "SecurityWarning", "subprocess module imported — review all usage carefully", "medium")
        self.generic_visit(node)


def check_security(code: str, filename: str = "code.py") -> List[Issue]:
    """
    Scan Python code for common security anti-patterns.

    Args:
        code: Python source code string.
        filename: Name of the file being analyzed.

    Returns:
        List of security Issue objects.
    """
    issues: List[Issue] = []

    # AST-based checks
    try:
        tree = ast.parse(code, filename=filename)
        visitor = _SecurityVisitor(filename)
        visitor.visit(tree)
        issues.extend(visitor.issues)
    except SyntaxError:
        # Syntax errors handled by syntax_checker; skip AST security scan
        pass
    except Exception as e:
        logger.warning(f"Security scan failed for {filename}: {e}")

    # Regex-based checks on raw source lines
    for lineno, line in enumerate(code.splitlines(), start=1):
        for pattern, message, severity in SECRET_PATTERNS:
            if pattern.search(line):
                issues.append(Issue(
                    file=filename,
                    line=lineno,
                    type="SecurityWarning",
                    message=message,
                    severity=severity,
                ))

    return issues
