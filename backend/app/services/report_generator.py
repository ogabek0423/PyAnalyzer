"""Combines syntax and security results into a final AnalysisResult."""
from typing import List, Tuple

from app.models.analysis_result import AnalysisResult
from app.services.syntax_checker import check_syntax
from app.services.security_checker import check_security


def analyze_code(code: str, filename: str = "code.py") -> Tuple[list, list]:
    """Run all checks on a single code snippet and return (syntax_errors, security_warnings)."""
    syntax = check_syntax(code, filename)
    security = check_security(code, filename)
    return syntax, security


def build_result(files: List[Tuple[str, str]]) -> AnalysisResult:
    """
    Analyze a list of (filename, code) pairs and build the combined AnalysisResult.

    Args:
        files: List of (filename, source_code) tuples.

    Returns:
        Aggregated AnalysisResult.
    """
    all_syntax = []
    all_security = []

    for filename, code in files:
        syntax, security = analyze_code(code, filename)
        all_syntax.extend(syntax)
        all_security.extend(security)

    return AnalysisResult(
        status="success",
        syntax_errors=all_syntax,
        security_warnings=all_security,
        total_files_analyzed=len(files),
    )
