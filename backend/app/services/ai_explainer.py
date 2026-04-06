"""
AI Explainer — placeholder for future AI-powered explanations.

Future integration:
- Connect to Anthropic / OpenAI API
- Explain detected issues in plain language
- Suggest safer code alternatives
"""
from app.models.analysis_result import Issue


def explain_issue(issue: Issue) -> str:
    """
    Return a human-readable explanation for a code issue.

    Currently returns a placeholder. Replace with LLM API call.
    """
    return (
        f"[AI explanation coming soon] Issue '{issue.type}' on line {issue.line}: "
        f"{issue.message}"
    )
