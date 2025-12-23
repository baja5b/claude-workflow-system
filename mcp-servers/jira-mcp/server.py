#!/usr/bin/env python3
"""
Jira MCP Server
Provides Jira Cloud integration for Claude Code workflows.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Optional

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    exit(1)

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Import Jira client
from jira_client import JiraClient
from worker import JiraWorker, create_default_worker
from github_sync import GitHubSync

# Initialize MCP server
server = Server("jira-mcp")

# Global clients (initialized on first use)
_jira_client: Optional[JiraClient] = None
_worker: Optional[JiraWorker] = None
_worker_task: Optional[asyncio.Task] = None
_github_sync: Optional[GitHubSync] = None


def get_github_sync() -> GitHubSync:
    """Get or create GitHub sync instance."""
    global _github_sync
    if _github_sync is None:
        _github_sync = GitHubSync()
    return _github_sync


def get_jira_client() -> JiraClient:
    """Get or create Jira client instance."""
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraClient()
    return _jira_client


@server.list_tools()
async def list_tools():
    """List available Jira tools."""
    return [
        Tool(
            name="jira_get_issue",
            description="Get a Jira issue by key (e.g., PROJ-123)",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key (e.g., PROJ-123)"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="jira_list_issues",
            description="Search Jira issues using JQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default 50)"
                    }
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="jira_list_by_status",
            description="List issues in specific statuses",
            inputSchema={
                "type": "object",
                "properties": {
                    "statuses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of status names"
                    }
                },
                "required": ["statuses"]
            }
        ),
        Tool(
            name="jira_create_issue",
            description="Create a new Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Issue title/summary"
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description"
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (Task, Bug, Story, etc.)"
                    }
                },
                "required": ["summary"]
            }
        ),
        Tool(
            name="jira_add_comment",
            description="Add a comment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "body": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["issue_key", "body"]
            }
        ),
        Tool(
            name="jira_get_comments",
            description="Get all comments on a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="jira_get_transitions",
            description="Get available status transitions for an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="jira_transition",
            description="Transition an issue to a new status",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "status": {
                        "type": "string",
                        "description": "Target status name"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment to add"
                    }
                },
                "required": ["issue_key", "status"]
            }
        ),
        Tool(
            name="jira_update_issue",
            description="Update issue fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "fields": {
                        "type": "object",
                        "description": "Fields to update"
                    }
                },
                "required": ["issue_key", "fields"]
            }
        ),
        Tool(
            name="jira_poll_once",
            description="Run a single poll cycle to process all workable issues",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="jira_process_issue",
            description="Process a single issue through its current status handler",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key to process"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="jira_get_workable",
            description="Get all issues that need automated processing",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        # GitHub Sync Tools
        Tool(
            name="github_create_issue",
            description="Create a GitHub issue linked to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "jira_key": {
                        "type": "string",
                        "description": "Jira issue key (e.g., PROJ-123)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue body/description"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional labels"
                    }
                },
                "required": ["jira_key", "title", "body"]
            }
        ),
        Tool(
            name="github_create_branch",
            description="Create a feature branch for a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "jira_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title (used in branch name)"
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "Base branch (default: develop)"
                    }
                },
                "required": ["jira_key", "title"]
            }
        ),
        Tool(
            name="github_create_pr",
            description="Create a pull request linked to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "jira_key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title"
                    },
                    "body": {
                        "type": "string",
                        "description": "PR description"
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "Target branch (default: develop)"
                    },
                    "draft": {
                        "type": "boolean",
                        "description": "Create as draft PR (default: true)"
                    }
                },
                "required": ["jira_key", "title", "body"]
            }
        ),
        Tool(
            name="github_pr_status",
            description="Get the status of a pull request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Pull request number"
                    }
                },
                "required": ["pr_number"]
            }
        ),
        Tool(
            name="github_merge_pr",
            description="Merge a pull request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Pull request number"
                    },
                    "method": {
                        "type": "string",
                        "description": "Merge method: merge, squash, rebase (default: squash)"
                    },
                    "delete_branch": {
                        "type": "boolean",
                        "description": "Delete branch after merge (default: true)"
                    }
                },
                "required": ["pr_number"]
            }
        ),
        Tool(
            name="github_find_by_jira",
            description="Find GitHub issue or PR by Jira key",
            inputSchema={
                "type": "object",
                "properties": {
                    "jira_key": {
                        "type": "string",
                        "description": "Jira issue key to search for"
                    },
                    "type": {
                        "type": "string",
                        "description": "Type to search: issue or pr (default: both)"
                    }
                },
                "required": ["jira_key"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    jira = get_jira_client()

    try:
        if name == "jira_get_issue":
            result = await jira.get_issue(arguments["issue_key"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_list_issues":
            max_results = arguments.get("max_results", 50)
            result = await jira.search_issues(arguments["jql"], max_results=max_results)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_list_by_status":
            result = await jira.get_project_issues_by_status(arguments["statuses"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_create_issue":
            result = await jira.create_issue(
                summary=arguments["summary"],
                description=arguments.get("description"),
                issue_type=arguments.get("issue_type", "Task")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_add_comment":
            result = await jira.add_comment(
                issue_key=arguments["issue_key"],
                body=arguments["body"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_get_comments":
            result = await jira.get_comments(arguments["issue_key"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_get_transitions":
            result = await jira.get_transitions(arguments["issue_key"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_transition":
            issue_key = arguments["issue_key"]
            target_status = arguments["status"]
            comment = arguments.get("comment")

            # Find transition ID by status name
            transition_id = await jira.find_transition_by_name(issue_key, target_status)
            if not transition_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": True,
                        "message": f"No transition found to status '{target_status}'"
                    })
                )]

            result = await jira.transition_issue(issue_key, transition_id, comment)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_update_issue":
            result = await jira.update_issue(
                issue_key=arguments["issue_key"],
                fields=arguments["fields"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_poll_once":
            global _worker
            if _worker is None:
                _worker = create_default_worker()
            results = await _worker.poll_once()
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "processed": len(results),
                "results": results
            }, indent=2))]

        elif name == "jira_process_issue":
            global _worker
            if _worker is None:
                _worker = create_default_worker()
            issue_key = arguments["issue_key"]
            issue_data = await jira.get_issue(issue_key)
            if "error" in issue_data:
                return [TextContent(type="text", text=json.dumps(issue_data, indent=2))]
            result = await _worker.process_issue(issue_data)
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "issue": issue_key,
                "result": result
            }, indent=2))]

        elif name == "jira_get_workable":
            global _worker
            if _worker is None:
                _worker = create_default_worker()
            issues = await _worker.get_workable_issues()
            return [TextContent(type="text", text=json.dumps({
                "count": len(issues),
                "issues": [
                    {
                        "key": i.get("key"),
                        "summary": i.get("fields", {}).get("summary"),
                        "status": i.get("fields", {}).get("status", {}).get("name")
                    }
                    for i in issues
                ]
            }, indent=2))]

        # GitHub Sync Tools
        elif name == "github_create_issue":
            github = get_github_sync()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: github.create_github_issue(
                    arguments["jira_key"],
                    arguments["title"],
                    arguments["body"],
                    arguments.get("labels")
                )
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "github_create_branch":
            github = get_github_sync()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: github.create_branch(
                    arguments["jira_key"],
                    arguments["title"],
                    arguments.get("base_branch", "develop")
                )
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "github_create_pr":
            github = get_github_sync()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: github.create_pull_request(
                    arguments["jira_key"],
                    arguments["title"],
                    arguments["body"],
                    arguments.get("base_branch", "develop"),
                    arguments.get("draft", True)
                )
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "github_pr_status":
            github = get_github_sync()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: github.get_pr_status(arguments["pr_number"])
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "github_merge_pr":
            github = get_github_sync()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: github.merge_pr(
                    arguments["pr_number"],
                    arguments.get("method", "squash"),
                    arguments.get("delete_branch", True)
                )
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "github_find_by_jira":
            github = get_github_sync()
            jira_key = arguments["jira_key"]
            search_type = arguments.get("type", "both")

            loop = asyncio.get_event_loop()
            result = {"jira_key": jira_key}

            if search_type in ["issue", "both"]:
                issue = await loop.run_in_executor(
                    None,
                    lambda: github.find_issue_by_jira_key(jira_key)
                )
                result["github_issue"] = issue

            if search_type in ["pr", "both"]:
                pr = await loop.run_in_executor(
                    None,
                    lambda: github.find_pr_by_jira_key(jira_key)
                )
                result["github_pr"] = pr

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": True, "message": str(e)})
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
