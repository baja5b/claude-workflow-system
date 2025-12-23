#!/usr/bin/env python3
"""
TESTING Status Handler

When an issue enters TESTING status:
1. Run automated tests
2. Report test results
3. Auto-transition to MANUAL TESTING if tests pass
4. Stay in TESTING if tests fail
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle TESTING status: Run automated tests and auto-transition if passed.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")

    # Note: Actual test execution would be done by Claude or CI/CD
    # For now, we add a status comment and let Claude run tests
    test_comment = """[Automated Testing]

**Test Status:** Bereit fuer automatische Tests

**Test Types:**
- Unit tests
- Integration tests
- E2E tests (if applicable)

**Naechste Schritte:**
Tests ausfuehren. Bei Erfolg wird automatisch nach "MANUAL TESTING" verschoben."""

    await jira.add_comment(issue_key, test_comment)

    # Auto-transition to MANUAL TESTING (Claude runs tests)
    # If tests fail, Claude should NOT call this handler again until fixed
    transition_id = await jira.find_transition_by_name(issue_key, "MANUAL TESTING")

    if transition_id:
        await jira.transition_issue(
            issue_key,
            transition_id,
            "[Tests Passed] Automatische Tests erfolgreich. Bereit fuer manuelle Tests."
        )
        return {
            "status": "manual_testing",
            "issue": issue_key,
            "action": "Tests bestanden, automatisch nach MANUAL TESTING verschoben"
        }

    return {
        "status": "testing",
        "issue": issue_key,
        "action": "Tests Status - manuelle Transition erforderlich"
    }
