#!/usr/bin/env python3
"""
GitHub Sync Module for Jira Integration

Provides bidirectional synchronization between Jira and GitHub:
- Jira → GitHub: Issues, branches, PRs
- GitHub → Jira: PR status, comments

Uses GitHub CLI (gh) for all operations.
"""

import asyncio
import re
import subprocess
import json
from typing import Optional, Dict, Any, List


class GitHubSync:
    """
    Handles GitHub operations via gh CLI.

    Sync Flow:
    - TO DO → GitHub Issue created
    - PLANNED AND CONFIRMED → Branch created
    - REVIEW → Draft PR created
    - DONE ← PR merged
    """

    def __init__(self, repo: Optional[str] = None):
        """
        Initialize GitHub sync.

        Args:
            repo: GitHub repo in format "owner/repo". If None, uses current repo.
        """
        self.repo = repo
        self._check_gh_installed()

    def _check_gh_installed(self):
        """Check if gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("GitHub CLI not authenticated. Run: gh auth login")
        except FileNotFoundError:
            raise RuntimeError("GitHub CLI not installed. Install from: https://cli.github.com")

    def _run_gh(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run gh command with optional repo flag."""
        cmd = ["gh"] + args
        if self.repo:
            cmd.extend(["--repo", self.repo])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if check and result.returncode != 0:
            raise RuntimeError(f"gh command failed: {result.stderr}")

        return result

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run git command."""
        cmd = ["git"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)

        if check and result.returncode != 0:
            raise RuntimeError(f"git command failed: {result.stderr}")

        return result

    # --- Issue Operations ---

    def create_github_issue(
        self,
        jira_key: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a GitHub issue linked to Jira.

        Args:
            jira_key: Jira issue key (e.g., PROJ-123)
            title: Issue title
            body: Issue body (will include Jira link)
            labels: Optional list of labels

        Returns:
            Dict with issue number and URL
        """
        # Add Jira reference to body
        full_body = f"{body}\n\n---\nJira: {jira_key}"

        args = [
            "issue", "create",
            "--title", f"{jira_key}: {title}",
            "--body", full_body
        ]

        if labels:
            for label in labels:
                args.extend(["--label", label])

        result = self._run_gh(args)

        # Parse issue URL from output
        url = result.stdout.strip()
        issue_number = url.split("/")[-1] if url else None

        return {
            "success": True,
            "issue_number": issue_number,
            "url": url,
            "jira_key": jira_key
        }

    def get_github_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get GitHub issue details."""
        result = self._run_gh([
            "issue", "view", str(issue_number),
            "--json", "number,title,state,body,url"
        ])
        return json.loads(result.stdout)

    def add_github_comment(
        self,
        issue_number: int,
        comment: str,
        jira_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a GitHub issue.

        Args:
            issue_number: GitHub issue number
            comment: Comment text
            jira_key: Optional Jira key to reference
        """
        body = comment
        if jira_key:
            body = f"{comment}\n\n_From Jira: {jira_key}_"

        self._run_gh([
            "issue", "comment", str(issue_number),
            "--body", body
        ])

        return {"success": True, "issue_number": issue_number}

    def close_github_issue(self, issue_number: int) -> Dict[str, Any]:
        """Close a GitHub issue."""
        self._run_gh(["issue", "close", str(issue_number)])
        return {"success": True, "issue_number": issue_number, "state": "closed"}

    # --- Branch Operations ---

    def create_branch(
        self,
        jira_key: str,
        title: str,
        base_branch: str = "develop"
    ) -> Dict[str, Any]:
        """
        Create a feature branch for a Jira issue.

        Args:
            jira_key: Jira issue key (e.g., PROJ-123)
            title: Issue title (used in branch name)
            base_branch: Base branch to create from

        Returns:
            Dict with branch name
        """
        # Generate branch name
        branch_name = self._generate_branch_name(jira_key, title)

        # Fetch and checkout base branch
        self._run_git(["fetch", "origin", base_branch])
        self._run_git(["checkout", base_branch])
        self._run_git(["pull", "origin", base_branch])

        # Create and checkout new branch
        self._run_git(["checkout", "-b", branch_name])

        return {
            "success": True,
            "branch": branch_name,
            "base_branch": base_branch,
            "jira_key": jira_key
        }

    def _generate_branch_name(self, jira_key: str, title: str) -> str:
        """Generate a branch name from Jira key and title."""
        # Clean title for branch name
        clean_title = title.lower()
        clean_title = re.sub(r'[^a-z0-9\s-]', '', clean_title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip())

        # Limit length
        if len(clean_title) > 40:
            clean_title = clean_title[:40].rsplit('-', 1)[0]

        return f"feature/{jira_key}-{clean_title}"

    def get_current_branch(self) -> str:
        """Get current git branch name."""
        result = self._run_git(["branch", "--show-current"])
        return result.stdout.strip()

    def push_branch(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Push branch to remote."""
        branch = branch or self.get_current_branch()
        self._run_git(["push", "-u", "origin", branch])
        return {"success": True, "branch": branch}

    # --- Pull Request Operations ---

    def create_pull_request(
        self,
        jira_key: str,
        title: str,
        body: str,
        base_branch: str = "develop",
        draft: bool = True
    ) -> Dict[str, Any]:
        """
        Create a pull request linked to Jira.

        Args:
            jira_key: Jira issue key
            title: PR title
            body: PR body
            base_branch: Target branch
            draft: Create as draft PR

        Returns:
            Dict with PR number and URL
        """
        # Ensure branch is pushed
        current_branch = self.get_current_branch()
        self.push_branch(current_branch)

        # Add Jira reference to body
        full_body = f"{body}\n\n---\nJira: {jira_key}"

        args = [
            "pr", "create",
            "--title", f"{jira_key}: {title}",
            "--body", full_body,
            "--base", base_branch
        ]

        if draft:
            args.append("--draft")

        result = self._run_gh(args)

        # Parse PR URL from output
        url = result.stdout.strip()
        pr_number = url.split("/")[-1] if url else None

        return {
            "success": True,
            "pr_number": pr_number,
            "url": url,
            "jira_key": jira_key,
            "draft": draft
        }

    def get_pr_status(self, pr_number: int) -> Dict[str, Any]:
        """Get PR status including checks."""
        result = self._run_gh([
            "pr", "view", str(pr_number),
            "--json", "number,title,state,mergeable,reviews,statusCheckRollup"
        ])
        return json.loads(result.stdout)

    def mark_pr_ready(self, pr_number: int) -> Dict[str, Any]:
        """Mark a draft PR as ready for review."""
        self._run_gh(["pr", "ready", str(pr_number)])
        return {"success": True, "pr_number": pr_number, "draft": False}

    def merge_pr(
        self,
        pr_number: int,
        method: str = "squash",
        delete_branch: bool = True
    ) -> Dict[str, Any]:
        """
        Merge a pull request.

        Args:
            pr_number: PR number
            method: Merge method (merge, squash, rebase)
            delete_branch: Delete branch after merge
        """
        args = ["pr", "merge", str(pr_number), f"--{method}"]

        if delete_branch:
            args.append("--delete-branch")

        self._run_gh(args)

        return {
            "success": True,
            "pr_number": pr_number,
            "merged": True,
            "method": method
        }

    def add_pr_comment(self, pr_number: int, comment: str) -> Dict[str, Any]:
        """Add a comment to a PR."""
        self._run_gh([
            "pr", "comment", str(pr_number),
            "--body", comment
        ])
        return {"success": True, "pr_number": pr_number}

    # --- Search Operations ---

    def find_issue_by_jira_key(self, jira_key: str) -> Optional[Dict[str, Any]]:
        """Find GitHub issue by Jira key reference."""
        result = self._run_gh([
            "issue", "list",
            "--search", f"{jira_key} in:title,body",
            "--json", "number,title,state,url",
            "--limit", "1"
        ], check=False)

        if result.returncode != 0:
            return None

        issues = json.loads(result.stdout)
        return issues[0] if issues else None

    def find_pr_by_jira_key(self, jira_key: str) -> Optional[Dict[str, Any]]:
        """Find GitHub PR by Jira key reference."""
        result = self._run_gh([
            "pr", "list",
            "--search", f"{jira_key} in:title,body",
            "--json", "number,title,state,url",
            "--limit", "1"
        ], check=False)

        if result.returncode != 0:
            return None

        prs = json.loads(result.stdout)
        return prs[0] if prs else None

    def find_pr_by_branch(self, branch: str) -> Optional[Dict[str, Any]]:
        """Find PR by branch name."""
        result = self._run_gh([
            "pr", "list",
            "--head", branch,
            "--json", "number,title,state,url",
            "--limit", "1"
        ], check=False)

        if result.returncode != 0:
            return None

        prs = json.loads(result.stdout)
        return prs[0] if prs else None


# Async wrapper for use in async handlers
async def create_github_issue_async(
    jira_key: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Async wrapper for create_github_issue."""
    sync = GitHubSync()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: sync.create_github_issue(jira_key, title, body, labels)
    )


async def create_branch_async(
    jira_key: str,
    title: str,
    base_branch: str = "develop"
) -> Dict[str, Any]:
    """Async wrapper for create_branch."""
    sync = GitHubSync()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: sync.create_branch(jira_key, title, base_branch)
    )


async def create_pr_async(
    jira_key: str,
    title: str,
    body: str,
    base_branch: str = "develop",
    draft: bool = True
) -> Dict[str, Any]:
    """Async wrapper for create_pull_request."""
    sync = GitHubSync()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: sync.create_pull_request(jira_key, title, body, base_branch, draft)
    )


async def check_pr_status_async(pr_number: int) -> Dict[str, Any]:
    """Async wrapper for get_pr_status."""
    sync = GitHubSync()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: sync.get_pr_status(pr_number)
    )


async def merge_pr_async(
    pr_number: int,
    method: str = "squash",
    delete_branch: bool = True
) -> Dict[str, Any]:
    """Async wrapper for merge_pr."""
    sync = GitHubSync()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: sync.merge_pr(pr_number, method, delete_branch)
    )


# CLI for testing
if __name__ == "__main__":
    import sys

    sync = GitHubSync()

    if len(sys.argv) < 2:
        print("Usage: python github_sync.py <command> [args]")
        print("Commands: issue, branch, pr, status")
        sys.exit(1)

    command = sys.argv[1]

    if command == "issue":
        if len(sys.argv) < 4:
            print("Usage: python github_sync.py issue <jira_key> <title>")
            sys.exit(1)
        result = sync.create_github_issue(sys.argv[2], sys.argv[3], "Created from Jira")
        print(json.dumps(result, indent=2))

    elif command == "branch":
        if len(sys.argv) < 4:
            print("Usage: python github_sync.py branch <jira_key> <title>")
            sys.exit(1)
        result = sync.create_branch(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2))

    elif command == "pr":
        if len(sys.argv) < 4:
            print("Usage: python github_sync.py pr <jira_key> <title>")
            sys.exit(1)
        result = sync.create_pull_request(sys.argv[2], sys.argv[3], "PR from Jira")
        print(json.dumps(result, indent=2))

    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: python github_sync.py status <pr_number>")
            sys.exit(1)
        result = sync.get_pr_status(int(sys.argv[2]))
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
