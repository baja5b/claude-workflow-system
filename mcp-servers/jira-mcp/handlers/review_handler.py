#!/usr/bin/env python3
"""
REVIEW Status Handler

When an issue enters REVIEW status:
1. Summarize what was implemented
2. Create/update Pull Request (if GitHub sync enabled)
3. Add review checklist comment
4. Transition to TESTING
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle REVIEW status: Summarize and prepare for testing.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")

    # Get implementation comments
    comments = await jira.get_comments(issue_key)
    implementation_summary = extract_implementation_summary(comments)

    # Create review comment
    review_comment = f"""[Code Review]

**Implementation Summary:**
{implementation_summary}

**Review Checklist:**
- [ ] Code follows project conventions
- [ ] No hardcoded values or secrets
- [ ] Error handling is appropriate
- [ ] Changes are documented
- [ ] No unnecessary complexity

**Next:** Automated tests will run after review approval."""

    # Transition to TESTING
    transition_id = await jira.find_transition_by_name(issue_key, "TESTING")

    if transition_id:
        await jira.transition_issue(issue_key, transition_id, review_comment)
        return {
            "status": "testing",
            "issue": issue_key,
            "action": "Review complete, transitioned to TESTING"
        }

    # No transition available - just add comment
    await jira.add_comment(issue_key, review_comment)
    return {
        "status": "review",
        "issue": issue_key,
        "action": "Review comment added, no transition available"
    }


def extract_implementation_summary(comments: list) -> str:
    """Extract implementation details from comments."""
    implementation_notes = []

    for comment in comments:
        body = comment.get("body", {})

        # Extract text from ADF
        body_text = ""
        if isinstance(body, dict):
            for block in body.get("content", []):
                if block.get("type") == "paragraph":
                    for item in block.get("content", []):
                        if item.get("type") == "text":
                            body_text += item.get("text", "")

        # Look for implementation-related comments
        if any(keyword in body_text.lower() for keyword in [
            "implemented", "added", "created", "fixed", "updated",
            "changed", "modified", "refactored", "completed"
        ]):
            # Get first 200 chars of relevant comment
            implementation_notes.append(body_text[:200])

    if implementation_notes:
        return "\n".join(f"- {note}" for note in implementation_notes[-3:])

    return "Implementation completed. See commit history for details."
