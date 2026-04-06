"""Pydantic models for analysis results."""
from pydantic import BaseModel
from typing import List, Optional


class Issue(BaseModel):
    """Represents a single code issue."""
    file: str
    line: int
    type: str
    message: str
    severity: str  # "high" | "medium" | "low"


class AnalysisResult(BaseModel):
    """Full analysis result returned to the client."""
    status: str
    filename: Optional[str] = None
    syntax_errors: List[Issue] = []
    security_warnings: List[Issue] = []
    total_files_analyzed: int = 1


class TextRequest(BaseModel):
    """Request body for text analysis."""
    code: str


class GithubRequest(BaseModel):
    """Request body for GitHub repo analysis."""
    repo_url: str
