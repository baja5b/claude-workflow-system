#!/usr/bin/env python3
"""
PLANNED AND CONFIRMED Status Handler

When an issue enters PLANNED AND CONFIRMED status:
1. Start work immediately
2. Create GitHub branch (if GitHub sync enabled)
3. Transition to IN PROGRESS
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle PLANNED AND CONFIRMED status: Start work.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")

    # Generate branch name
    branch_name = generate_branch_name(issue_key, summary)

    # Add start comment
    start_comment = f"""[Work Started]

Starting implementation for: {summary}

**Branch:** `{branch_name}`

Work is now in progress."""

    # Transition to IN PROGRESS
    transition_id = await jira.find_transition_by_name(issue_key, "IN PROGRESS")
    if not transition_id:
        # Try German variant
        transition_id = await jira.find_transition_by_name(issue_key, "IN ARBEIT")

    if transition_id:
        await jira.transition_issue(issue_key, transition_id, start_comment)
        return {
            "status": "in_progress",
            "issue": issue_key,
            "branch": branch_name,
            "action": "Started work and transitioned to IN PROGRESS"
        }

    # No transition available - just add comment
    await jira.add_comment(issue_key, start_comment)
    return {
        "status": "confirmed",
        "issue": issue_key,
        "branch": branch_name,
        "action": "Added start comment, no transition available"
    }


def generate_branch_name(issue_key: str, summary: str) -> str:
    """Generate a Git branch name from issue key and summary."""
    # Clean up summary for branch name
    clean_summary = summary.lower()

    # Remove special characters
    import re
    clean_summary = re.sub(r'[^a-z0-9\s-]', '', clean_summary)

    # Replace spaces with hyphens
    clean_summary = re.sub(r'\s+', '-', clean_summary.strip())

    # Limit length
    if len(clean_summary) > 40:
        clean_summary = clean_summary[:40].rsplit('-', 1)[0]

    return f"feature/{issue_key}-{clean_summary}"
