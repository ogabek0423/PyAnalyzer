"""Syntax checking service using Python's AST module."""
import ast
import logging
from typing import List

from app.models.analysis_result import Issue

logger = logging.getLogger(__name__)


def check_syntax(code: str, filename: str = "code.py") -> List[Issue]:
    """
    Parse Python code using AST and return any syntax errors.

    Args:
        code: Python source code string.
        filename: Name of the file being analyzed.

    Returns:
        List of Issue objects for syntax errors found.
    """
    issues: List[Issue] = []
    try:
        ast.parse(code, filename=filename)
    except SyntaxError as e:
        logger.debug(f"Syntax error in {filename}: {e}")
        issues.append(Issue(
            file=filename,
            line=e.lineno or 0,
            type="SyntaxError",
            message=e.msg or str(e),
            severity="high",
        ))
    except Exception as e:
        logger.warning(f"Unexpected parse error in {filename}: {e}")
        issues.append(Issue(
            file=filename,
            line=0,
            type="ParseError",
            message=str(e),
            severity="high",
        ))
    return issues
