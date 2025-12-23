#!/usr/bin/env python3
"""
TO DO Status Handler

When an issue enters TO DO status:
1. Analyze the issue description
2. Create an implementation plan
3. Add plan as comment
4. Transition to PLANNED
"""

from typing import Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jira_client import JiraClient


async def handle(issue: Dict[str, Any], jira: JiraClient) -> Dict[str, Any]:
    """
    Handle TO DO status: Create implementation plan.
    """
    issue_key = issue.get("key")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    description = fields.get("description", {})
    issue_type = fields.get("issuetype", {}).get("name", "Task")

    # Extract description text from ADF format
    desc_text = extract_description_text(description)

    # Create implementation plan
    plan = create_plan(summary, desc_text, issue_type)

    # Add plan as comment
    await jira.add_comment(issue_key, plan)

    # Transition to PLANNED
    transition_id = await jira.find_transition_by_name(issue_key, "PLANNED")
    if transition_id:
        await jira.transition_issue(issue_key, transition_id)
        return {
            "status": "planned",
            "issue": issue_key,
            "action": "Created plan and transitioned to PLANNED"
        }

    return {
        "status": "plan_created",
        "issue": issue_key,
        "action": "Plan created, no transition available to PLANNED"
    }


def extract_description_text(description: Any) -> str:
    """Extract plain text from Jira ADF description."""
    if not description or not isinstance(description, dict):
        return ""

    text_parts = []
    content = description.get("content", [])

    for block in content:
        block_type = block.get("type", "")

        if block_type == "paragraph":
            for item in block.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

        elif block_type == "bulletList" or block_type == "orderedList":
            for list_item in block.get("content", []):
                for para in list_item.get("content", []):
                    for item in para.get("content", []):
                        if item.get("type") == "text":
                            text_parts.append(f"- {item.get('text', '')}")

        elif block_type == "codeBlock":
            for item in block.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(f"```\n{item.get('text', '')}\n```")

    return "\n".join(text_parts)


def create_plan(summary: str, description: str, issue_type: str) -> str:
    """Create an implementation plan based on issue details."""

    # Determine plan type based on issue type
    if issue_type.lower() == "bug":
        plan_template = """[Auto-Plan: Bug Fix]

**Issue:** {summary}

**Analysis:**
{description}

**Plan:**
1. Reproduce the bug
2. Identify root cause
3. Implement fix
4. Write regression test
5. Verify fix

**Next Steps:**
- Review and confirm this plan
- Add any additional context as comments
- Move to "PLANNED AND CONFIRMED" when ready to proceed"""

    elif issue_type.lower() == "story":
        plan_template = """[Auto-Plan: User Story]

**Issue:** {summary}

**Requirements:**
{description}

**Plan:**
1. Break down into tasks
2. Design solution architecture
3. Implement core functionality
4. Add UI components (if needed)
5. Write tests
6. Documentation

**Next Steps:**
- Review and confirm this plan
- Add acceptance criteria if missing
- Move to "PLANNED AND CONFIRMED" when ready to proceed"""

    else:  # Task or other
        plan_template = """[Auto-Plan: Task]

**Issue:** {summary}

**Description:**
{description}

**Plan:**
1. Analyze requirements
2. Identify affected files/components
3. Implement changes
4. Write/update tests
5. Review and refactor

**Next Steps:**
- Review and confirm this plan
- Add any clarifications as comments
- Move to "PLANNED AND CONFIRMED" when ready to proceed"""

    return plan_template.format(
        summary=summary,
        description=description if description else "(No description provided)"
    )
