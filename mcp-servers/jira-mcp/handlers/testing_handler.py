#!/usr/bin/env python3
"""
TESTING Status Handler

When an issue enters TESTING status:
1. Run automated tests
2. Report test results
3. Transition to MANUAL TESTING if tests pass
4. Stay in TESTING if tests fail
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle TESTING status: Run automated tests.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")

    # Note: Actual test execution would be done by Claude or CI/CD
    # This handler reports test readiness

    # Create testing comment
    test_comment = """[Automated Testing]

**Test Status:** Ready for automated tests

**Test Types:**
- Unit tests
- Integration tests
- E2E tests (if applicable)

**Action Required:**
Run tests and report results. Move to "MANUAL TESTING" when automated tests pass."""

    # Add testing comment
    await jira.add_comment(issue_key, test_comment)

    # Check if we should auto-transition (for now, require manual)
    # In a full implementation, this would check CI/CD results

    return {
        "status": "testing",
        "issue": issue_key,
        "action": "Awaiting test execution",
        "tests_pending": True
    }


async def report_test_results(
    issue_key: str,
    jira: JiraClient,
    passed: bool,
    test_output: str = ""
) -> Dict[str, Any]:
    """Report test results and transition if passed."""

    if passed:
        result_comment = f"""[Test Results: PASSED]

All automated tests passed successfully.

{test_output if test_output else "No test output captured."}

**Ready for manual testing.**"""

        # Transition to MANUAL TESTING
        transition_id = await jira.find_transition_by_name(issue_key, "MANUAL TESTING")
        if transition_id:
            await jira.transition_issue(issue_key, transition_id, result_comment)
            return {
                "status": "manual_testing",
                "issue": issue_key,
                "tests_passed": True
            }

        await jira.add_comment(issue_key, result_comment)
        return {
            "status": "testing",
            "issue": issue_key,
            "tests_passed": True,
            "action": "Tests passed, manual transition needed"
        }

    else:
        result_comment = f"""[Test Results: FAILED]

Some tests failed. Please review and fix.

{test_output if test_output else "No test output captured."}

**Action:** Fix failing tests and re-run."""

        await jira.add_comment(issue_key, result_comment)
        return {
            "status": "testing",
            "issue": issue_key,
            "tests_passed": False,
            "action": "Tests failed, fixes needed"
        }
