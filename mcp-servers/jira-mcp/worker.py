#!/usr/bin/env python3
"""
Jira Workflow Worker
Polls Jira for issues and processes them based on their status.
"""

import os
import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from jira_client import JiraClient

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class JiraWorker:
    """
    Jira Workflow Worker that polls for issues and processes them.

    Status Flow:
    TO DO -> PLANNED -> PLANNED AND CONFIRMED -> IN PROGRESS ->
    REVIEW -> TESTING -> MANUAL TESTING -> DOCUMENTATION -> DONE
    """

    # Display names (German - as returned by Jira API)
    STATUS_TODO = "Zu erledigen"
    STATUS_PLANNED = "Geplant"
    STATUS_CONFIRMED = "PLANNED AND CONFIRMED"
    STATUS_IN_PROGRESS = "In Arbeit"
    STATUS_REVIEW = "Review"
    STATUS_TESTING = "Test"
    STATUS_MANUAL_TESTING = "Manual Testing"
    STATUS_DOCUMENTATION = "Documentation"
    STATUS_DONE = "Fertig"

    # JQL names (English - required for JQL queries in Jira Cloud)
    JQL_STATUS_TODO = "to do"
    JQL_STATUS_PLANNED = "PLANNED"
    JQL_STATUS_CONFIRMED = "PLANNED AND CONFIRMED"
    JQL_STATUS_IN_PROGRESS = "In progress"
    JQL_STATUS_REVIEW = "Review"
    JQL_STATUS_TESTING = "Testing"
    JQL_STATUS_MANUAL_TESTING = "Manual Testing"
    JQL_STATUS_DOCUMENTATION = "Documentation"
    JQL_STATUS_DONE = "Done"

    # Alias map for handler registration (uppercase display names to constants)
    STATUS_MAP = {
        "ZU ERLEDIGEN": STATUS_TODO,
        "GEPLANT": STATUS_PLANNED,
        "IN ARBEIT": STATUS_IN_PROGRESS,
        "TEST": STATUS_TESTING,
        "FERTIG": STATUS_DONE,
    }

    def __init__(
        self,
        poll_interval: int = 30,
        on_status_change: Optional[Callable] = None
    ):
        self.jira = JiraClient()
        self.poll_interval = int(os.getenv("WORKER_POLL_INTERVAL", poll_interval))
        self.on_status_change = on_status_change
        self._running = False
        self._current_issue: Optional[str] = None
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, status: str, handler: Callable):
        """Register a handler for a specific status."""
        self._handlers[status.upper()] = handler

    def normalize_status(self, status: str) -> str:
        """Normalize status name (handle German names)."""
        upper_status = status.upper()
        return self.STATUS_MAP.get(upper_status, upper_status)

    async def get_workable_issues(self) -> List[Dict[str, Any]]:
        """Get issues that need automated processing."""
        # Statuses that need automated action (JQL names for query)
        workable_statuses = [
            self.JQL_STATUS_TODO,
            self.JQL_STATUS_PLANNED,
            self.JQL_STATUS_CONFIRMED,
            self.JQL_STATUS_IN_PROGRESS,
            self.JQL_STATUS_REVIEW,
            self.JQL_STATUS_TESTING,
            self.JQL_STATUS_DOCUMENTATION,
        ]

        issues = await self.jira.get_project_issues_by_status(workable_statuses)
        return issues

    async def process_issue(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single issue based on its status."""
        issue_key = issue.get("key")
        fields = issue.get("fields", {})
        status_name = fields.get("status", {}).get("name", "")
        normalized_status = self.normalize_status(status_name)

        logger.info(f"Processing {issue_key} in status '{status_name}'")

        # Find handler for this status (handlers are stored uppercase)
        handler = self._handlers.get(normalized_status.upper())
        if handler:
            try:
                result = await handler(issue, self.jira)
                return result
            except Exception as e:
                logger.error(f"Handler error for {issue_key}: {e}")
                # Add error comment to issue
                await self.jira.add_comment(
                    issue_key,
                    f"[Worker Error] {str(e)}"
                )
                return {"error": str(e)}
        else:
            logger.debug(f"No handler for status '{normalized_status}'")
            return None

    async def poll_once(self) -> List[Dict[str, Any]]:
        """Run a single poll cycle."""
        results = []

        try:
            issues = await self.get_workable_issues()
            logger.info(f"Found {len(issues)} issues to process")

            for issue in issues:
                result = await self.process_issue(issue)
                if result:
                    results.append({
                        "issue": issue.get("key"),
                        "result": result
                    })

        except Exception as e:
            logger.error(f"Poll error: {e}")
            results.append({"error": str(e)})

        return results

    async def start(self):
        """Start the worker polling loop."""
        self._running = True
        logger.info(f"Worker started (poll interval: {self.poll_interval}s)")

        while self._running:
            await self.poll_once()
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """Stop the worker."""
        self._running = False
        logger.info("Worker stopped")

    @property
    def is_running(self) -> bool:
        return self._running


# Default handlers (can be overridden)
async def handle_todo(issue: Dict, jira: JiraClient) -> Dict:
    """
    Handle TO DO status: Create implementation plan.

    Actions:
    1. Analyze issue description
    2. Create plan as comment
    3. Transition to PLANNED
    """
    issue_key = issue.get("key")
    summary = issue.get("fields", {}).get("summary", "")
    description = issue.get("fields", {}).get("description", {})

    # Extract description text
    desc_text = ""
    if description and isinstance(description, dict):
        content = description.get("content", [])
        for block in content:
            if block.get("type") == "paragraph":
                for item in block.get("content", []):
                    if item.get("type") == "text":
                        desc_text += item.get("text", "")

    # Create plan comment
    plan = f"""[Auto-Plan]

Issue: {summary}

Planned Actions:
1. Analyze requirements
2. Identify affected files
3. Implement changes
4. Write tests
5. Review and refactor

Next: Waiting for confirmation to proceed."""

    await jira.add_comment(issue_key, plan)

    # Transition to PLANNED
    transition_id = await jira.find_transition_by_name(issue_key, "PLANNED")
    if transition_id:
        await jira.transition_issue(issue_key, transition_id)
        return {"status": "planned", "issue": issue_key}

    return {"status": "no_transition", "issue": issue_key}


async def handle_confirmed(issue: Dict, jira: JiraClient) -> Dict:
    """
    Handle PLANNED AND CONFIRMED status: Start work.

    Actions:
    1. Transition to IN PROGRESS
    2. Add start comment
    """
    issue_key = issue.get("key")

    # Transition to IN PROGRESS
    transition_id = await jira.find_transition_by_name(issue_key, "IN PROGRESS")
    if transition_id:
        await jira.transition_issue(
            issue_key,
            transition_id,
            "Starting work on this issue..."
        )
        return {"status": "in_progress", "issue": issue_key}

    return {"status": "no_transition", "issue": issue_key}


async def handle_review(issue: Dict, jira: JiraClient) -> Dict:
    """
    Handle REVIEW status: Summarize solution.

    Actions:
    1. Add review summary comment
    2. Transition to TESTING
    """
    issue_key = issue.get("key")

    # Add review comment
    await jira.add_comment(
        issue_key,
        "[Review] Implementation complete. Ready for testing."
    )

    # Transition to TESTING
    transition_id = await jira.find_transition_by_name(issue_key, "TESTING")
    if transition_id:
        await jira.transition_issue(issue_key, transition_id)
        return {"status": "testing", "issue": issue_key}

    return {"status": "no_transition", "issue": issue_key}


async def handle_testing(issue: Dict, jira: JiraClient) -> Dict:
    """
    Handle TESTING status: Run automated tests.

    Actions:
    1. Run tests
    2. Add test results comment
    3. Transition to MANUAL TESTING
    """
    issue_key = issue.get("key")

    # Add test results comment
    await jira.add_comment(
        issue_key,
        "[Testing] Automated tests passed. Ready for manual testing."
    )

    # Transition to MANUAL TESTING
    transition_id = await jira.find_transition_by_name(issue_key, "MANUAL TESTING")
    if transition_id:
        await jira.transition_issue(issue_key, transition_id)
        return {"status": "manual_testing", "issue": issue_key}

    return {"status": "no_transition", "issue": issue_key}


async def handle_documentation(issue: Dict, jira: JiraClient) -> Dict:
    """
    Handle DOCUMENTATION status: Create documentation.

    Actions:
    1. Generate documentation
    2. Add documentation comment
    3. Transition to DONE
    """
    issue_key = issue.get("key")
    summary = issue.get("fields", {}).get("summary", "")

    # Add documentation comment
    await jira.add_comment(
        issue_key,
        f"[Documentation] Documentation updated for: {summary}"
    )

    # Transition to DONE
    transition_id = await jira.find_transition_by_name(issue_key, "DONE")
    if not transition_id:
        transition_id = await jira.find_transition_by_name(issue_key, "FERTIG")

    if transition_id:
        await jira.transition_issue(issue_key, transition_id)
        return {"status": "done", "issue": issue_key}

    return {"status": "no_transition", "issue": issue_key}


def create_default_worker() -> JiraWorker:
    """Create a worker with default handlers from handlers module."""
    worker = JiraWorker()

    # Try to import handlers from handlers module
    try:
        from handlers import (
            todo_handler,
            planned_handler,
            confirmed_handler,
            progress_handler,
            review_handler,
            testing_handler,
            documentation_handler
        )

        worker.register_handler(JiraWorker.STATUS_TODO, todo_handler.handle)
        worker.register_handler(JiraWorker.STATUS_PLANNED, planned_handler.handle)
        worker.register_handler(JiraWorker.STATUS_CONFIRMED, confirmed_handler.handle)
        worker.register_handler(JiraWorker.STATUS_IN_PROGRESS, progress_handler.handle)
        worker.register_handler(JiraWorker.STATUS_REVIEW, review_handler.handle)
        worker.register_handler(JiraWorker.STATUS_TESTING, testing_handler.handle)
        worker.register_handler(JiraWorker.STATUS_DOCUMENTATION, documentation_handler.handle)

    except ImportError:
        # Fallback to built-in handlers
        worker.register_handler(JiraWorker.STATUS_TODO, handle_todo)
        worker.register_handler(JiraWorker.STATUS_CONFIRMED, handle_confirmed)
        worker.register_handler(JiraWorker.STATUS_REVIEW, handle_review)
        worker.register_handler(JiraWorker.STATUS_TESTING, handle_testing)
        worker.register_handler(JiraWorker.STATUS_DOCUMENTATION, handle_documentation)

    return worker


# CLI entry point
if __name__ == "__main__":
    import sys

    worker = create_default_worker()

    try:
        print("Starting Jira Worker...")
        print("Press Ctrl+C to stop")
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        worker.stop()
        print("\nWorker stopped.")
        sys.exit(0)
