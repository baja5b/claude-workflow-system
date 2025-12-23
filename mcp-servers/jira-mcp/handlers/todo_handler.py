#!/usr/bin/env python3
"""
TO DO Status Handler - Minimal Processing

TO DO issues are handled by Claude Code directly, not by this handler.
This handler only logs that the issue is waiting for Claude Code processing.

The intelligent planning is done by /workflow:start-working in Claude Code,
which has access to the codebase and can create meaningful plans.
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle TO DO status: Skip automatic processing.

    TO DO issues should be processed by Claude Code via /workflow:start-working,
    not by this automated handler.
    """
    issue_key = issue.get("key")

    # Don't do anything - let Claude Code handle TO DO issues
    return {
        "status": "skipped",
        "issue": issue_key,
        "action": "TO DO - wartet auf Claude Code Verarbeitung via /workflow:start-working"
    }
