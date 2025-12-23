#!/usr/bin/env python3
"""
Jira Cloud REST API Client
Handles authentication and API requests to Jira Cloud.
"""

import os
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
from pathlib import Path
import httpx
from dotenv import load_dotenv


def find_repo_config() -> Optional[Dict[str, Any]]:
    """
    Find .claude-workflow.json in current directory or parent directories.
    Returns config dict or None if not found.
    """
    current = Path.cwd()

    # Search up to 10 levels
    for _ in range(10):
        config_file = current / ".claude-workflow.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


class JiraClient:
    """Client for Jira Cloud REST API v3."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None
    ):
        # Load from environment if not provided
        load_dotenv()

        # Check for repo-specific config
        repo_config = find_repo_config()

        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.username = username or os.getenv("JIRA_USERNAME", "")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", "")

        # Project key priority: parameter > repo config > env
        if project_key:
            self.project_key = project_key
        elif repo_config and repo_config.get("jira", {}).get("project_key"):
            self.project_key = repo_config["jira"]["project_key"]
        else:
            self.project_key = os.getenv("JIRA_PROJECT_KEY", "")

        self.repo_config = repo_config

        if not all([self.base_url, self.username, self.api_token]):
            raise ValueError(
                "Jira credentials not configured. "
                "Set JIRA_BASE_URL, JIRA_USERNAME, and JIRA_API_TOKEN."
            )

        self.auth = httpx.BasicAuth(self.username, self.api_token)
        self.api_url = f"{self.base_url}/rest/api/3"

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to Jira API."""
        url = f"{self.api_url}/{endpoint}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                auth=self.auth,
                json=data,
                params=params,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code >= 400:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }

            if response.status_code == 204:
                return {"success": True}

            return response.json()

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request."""
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Dict) -> Dict:
        """POST request."""
        return await self._request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: Dict) -> Dict:
        """PUT request."""
        return await self._request("PUT", endpoint, data=data)

    # --- Issue Operations ---

    async def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict:
        """Get a single issue by key."""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return await self.get(f"issue/{issue_key}", params=params)

    async def search_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """Search issues using JQL."""
        # Default fields for new /search/jql endpoint (required since Dec 2024)
        default_fields = [
            "key", "summary", "status", "description", "issuetype",
            "subtasks", "priority", "created", "updated", "assignee",
            "reporter", "comment", "parent"
        ]

        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields if fields else default_fields)
        }

        result = await self.get("search/jql", params=params)
        return result.get("issues", [])

    async def create_issue(
        self,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        project_key: Optional[str] = None
    ) -> Dict:
        """Create a new issue."""
        project = project_key or self.project_key

        data = {
            "fields": {
                "project": {"key": project},
                "summary": summary,
                "issuetype": {"name": issue_type}
            }
        }

        if description:
            # Jira Cloud uses Atlassian Document Format (ADF)
            data["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            }

        return await self.post("issue", data)

    async def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update issue fields."""
        return await self.put(f"issue/{issue_key}", {"fields": fields})

    # --- Transitions ---

    async def get_transitions(self, issue_key: str) -> List[Dict]:
        """Get available transitions for an issue."""
        result = await self.get(f"issue/{issue_key}/transitions")
        return result.get("transitions", [])

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None
    ) -> Dict:
        """Transition an issue to a new status."""
        data = {
            "transition": {"id": transition_id}
        }

        if comment:
            data["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {"type": "text", "text": comment}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }

        return await self.post(f"issue/{issue_key}/transitions", data)

    async def find_transition_by_name(
        self,
        issue_key: str,
        target_status: str
    ) -> Optional[str]:
        """Find transition ID by target status name."""
        transitions = await self.get_transitions(issue_key)
        for t in transitions:
            if t.get("to", {}).get("name", "").lower() == target_status.lower():
                return t["id"]
            if t.get("name", "").lower() == target_status.lower():
                return t["id"]
        return None

    # --- Comments ---

    async def get_comments(self, issue_key: str) -> List[Dict]:
        """Get all comments on an issue."""
        result = await self.get(f"issue/{issue_key}/comment")
        return result.get("comments", [])

    async def add_comment(self, issue_key: str, body: str) -> Dict:
        """Add a comment to an issue."""
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": body}
                        ]
                    }
                ]
            }
        }
        return await self.post(f"issue/{issue_key}/comment", data)

    # --- Project Helpers ---

    async def get_project_issues_by_status(
        self,
        statuses: List[str],
        project_key: Optional[str] = None
    ) -> List[Dict]:
        """Get all issues in specific statuses."""
        project = project_key or self.project_key
        status_list = ", ".join(f'"{s}"' for s in statuses)
        jql = f'project = "{project}" AND status IN ({status_list}) ORDER BY priority DESC, created ASC'
        return await self.search_issues(jql)

    async def get_issue_status(self, issue_key: str) -> Optional[str]:
        """Get current status of an issue."""
        issue = await self.get_issue(issue_key, fields=["status"])
        if "error" in issue:
            return None
        return issue.get("fields", {}).get("status", {}).get("name")

    # --- Subtask Operations ---

    async def create_subtask(
        self,
        parent_key: str,
        summary: str,
        description: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> Dict:
        """Create a subtask under a parent issue."""
        project = project_key or self.project_key

        data = {
            "fields": {
                "project": {"key": project},
                "parent": {"key": parent_key},
                "summary": summary,
                "issuetype": {"name": "Sub-task"}
            }
        }

        if description:
            data["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            }

        return await self.post("issue", data)

    async def get_subtasks(self, parent_key: str) -> List[Dict]:
        """Get all subtasks of an issue."""
        issue = await self.get_issue(parent_key, fields=["subtasks"])
        if "error" in issue:
            return []
        return issue.get("fields", {}).get("subtasks", [])

    async def update_description(self, issue_key: str, description: str) -> Dict:
        """Update issue description with plain text (converted to ADF)."""
        adf_description = {
            "type": "doc",
            "version": 1,
            "content": []
        }

        # Split by double newlines for paragraphs
        paragraphs = description.split("\n\n")
        for para in paragraphs:
            if para.strip():
                # Check if it's a heading (starts with **)
                if para.startswith("**") and "**" in para[2:]:
                    heading_end = para.index("**", 2)
                    heading_text = para[2:heading_end]
                    adf_description["content"].append({
                        "type": "heading",
                        "attrs": {"level": 3},
                        "content": [{"type": "text", "text": heading_text}]
                    })
                    rest = para[heading_end+2:].strip()
                    if rest:
                        adf_description["content"].append({
                            "type": "paragraph",
                            "content": [{"type": "text", "text": rest}]
                        })
                else:
                    adf_description["content"].append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": para}]
                    })

        return await self.update_issue(issue_key, {"description": adf_description})
