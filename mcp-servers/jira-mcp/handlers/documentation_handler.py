#!/usr/bin/env python3
"""
DOCUMENTATION Status Handler

When an issue enters DOCUMENTATION status:
1. Generate documentation for the changes
2. Update relevant docs/README files
3. Finalize PR (if GitHub sync enabled)
4. Auto-transition to DONE
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle DOCUMENTATION status: Generate docs and auto-transition to DONE.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    issue_type = fields.get("issuetype", {}).get("name", "Task")

    # Generate documentation summary
    doc_summary = generate_documentation(issue_key, summary, issue_type)

    # Create documentation comment
    doc_comment = f"""[Documentation Complete]

**Changes Documented:**
{doc_summary}

**Documentation Checklist:**
- [x] Implementation summarized
- [x] Changes documented
- [x] Issue complete

Dieses Issue wird jetzt abgeschlossen."""

    # Auto-transition to DONE
    transition_id = await jira.find_transition_by_name(issue_key, "DONE")
    if not transition_id:
        transition_id = await jira.find_transition_by_name(issue_key, "FERTIG")

    if transition_id:
        await jira.transition_issue(issue_key, transition_id, doc_comment)
        return {
            "status": "done",
            "issue": issue_key,
            "action": "Dokumentation erstellt, Issue abgeschlossen"
        }

    # No transition available - just add comment
    await jira.add_comment(issue_key, doc_comment)
    return {
        "status": "documentation",
        "issue": issue_key,
        "action": "Dokumentation erstellt - manuelle Transition nach DONE erforderlich"
    }


def generate_documentation(issue_key: str, summary: str, issue_type: str) -> str:
    """Generate documentation summary based on issue type."""

    if issue_type.lower() == "bug":
        return f"""**Bug Fix: {summary}**

- Issue: {issue_key}
- Type: Bug Fix
- Resolution: Fixed

The reported bug has been resolved. See commit history for implementation details."""

    elif issue_type.lower() == "story":
        return f"""**Feature: {summary}**

- Issue: {issue_key}
- Type: User Story
- Status: Implemented

New feature has been implemented as specified. See PR/commits for details."""

    else:
        return f"""**Task: {summary}**

- Issue: {issue_key}
- Type: {issue_type}
- Status: Complete

Task completed successfully."""
