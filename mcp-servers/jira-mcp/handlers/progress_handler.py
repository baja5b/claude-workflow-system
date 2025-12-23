#!/usr/bin/env python3
"""
IN PROGRESS Status Handler

When an issue is in IN PROGRESS status:
1. Work is being done (by Claude or developer)
2. Monitor for questions or blockers
3. Send Telegram notification if blocked
4. Wait for completion (manual transition to REVIEW)

This handler primarily monitors for blockers.
"""

from typing import Dict, Any, List
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


# Keywords that indicate a blocker or question
BLOCKER_KEYWORDS = [
    "blocked",
    "blocker",
    "waiting for",
    "need",
    "question",
    "unclear",
    "help needed",
    "stuck",
    "cannot proceed",
    "dependency"
]


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle IN PROGRESS status: Monitor for blockers.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")

    # Check for blockers in recent comments
    comments = await jira.get_comments(issue_key)
    blockers = find_blockers(comments)

    if blockers:
        # There are blockers - might need attention
        latest_blocker = blockers[-1]
        return {
            "status": "in_progress",
            "issue": issue_key,
            "action": "Blocker detected - may need attention",
            "blocked": True,
            "blocker_info": latest_blocker.get("text", "")[:200],
            "notification_recommended": True
        }

    return {
        "status": "in_progress",
        "issue": issue_key,
        "action": "Work in progress",
        "blocked": False
    }


def find_blockers(comments: List[Dict]) -> List[Dict]:
    """Find comments that indicate blockers or questions."""
    blockers = []

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

        # Check for blocker keywords
        body_lower = body_text.lower()
        for keyword in BLOCKER_KEYWORDS:
            if keyword in body_lower:
                blockers.append({
                    "id": comment.get("id"),
                    "author": comment.get("author", {}).get("displayName", "Unknown"),
                    "created": comment.get("created"),
                    "text": body_text,
                    "keyword": keyword
                })
                break

    return blockers
