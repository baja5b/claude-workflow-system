#!/usr/bin/env python3
"""
PLANNED Status Handler

When an issue is in PLANNED status:
1. Check for new comments (user feedback)
2. Update plan if needed
3. Wait for user to confirm (transition to PLANNED AND CONFIRMED)

This handler primarily monitors for feedback.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle PLANNED status: Monitor for user feedback.
    """
    issue_key = issue.get("key")

    # Get comments
    comments = await jira.get_comments(issue_key)

    # Check for recent user comments (not from automation)
    user_feedback = get_user_feedback(comments)

    if user_feedback:
        # There's user feedback - acknowledge it
        latest_feedback = user_feedback[-1]
        return {
            "status": "awaiting_confirmation",
            "issue": issue_key,
            "action": "User feedback detected",
            "feedback_count": len(user_feedback),
            "latest_feedback": latest_feedback.get("body_text", "")[:200]
        }

    return {
        "status": "awaiting_confirmation",
        "issue": issue_key,
        "action": "Waiting for user to confirm plan (move to PLANNED AND CONFIRMED)"
    }


def get_user_feedback(comments: List[Dict]) -> List[Dict]:
    """Extract user comments (not automation comments)."""
    user_comments = []

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

        # Skip automation comments
        if body_text.startswith("[Auto-") or body_text.startswith("[Worker"):
            continue

        # Add to user comments
        user_comments.append({
            "id": comment.get("id"),
            "author": comment.get("author", {}).get("displayName", "Unknown"),
            "created": comment.get("created"),
            "body_text": body_text
        })

    return user_comments
