#!/usr/bin/env python3
"""
Workflow API Server
Runs on Raspberry Pi, manages workflow state in SQLite.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Workflow API", version="1.0.0")

DB_PATH = os.getenv("WORKFLOW_DB_PATH", "/opt/workflow-system/workflows.db")


@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# --- Models ---

class WorkflowCreate(BaseModel):
    project: str
    project_path: Optional[str] = None
    title: str
    requirements: Optional[str] = None


class WorkflowUpdate(BaseModel):
    status: Optional[str] = None
    plan: Optional[str] = None
    requirements: Optional[str] = None
    github_issue_number: Optional[int] = None


class TaskCreate(BaseModel):
    workflow_id: str
    sequence: int
    description: str


class TaskUpdate(BaseModel):
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None


class NotificationCreate(BaseModel):
    workflow_id: str
    notification_type: str
    channel: str = "telegram"
    message: str


class TestResultCreate(BaseModel):
    workflow_id: str
    test_type: str
    test_name: str
    passed: bool
    output: Optional[str] = None


# --- Helper Functions ---

def generate_workflow_id() -> str:
    """Generate workflow ID: WF-YYYY-NNN"""
    year = datetime.now().year
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM workflows WHERE workflow_id LIKE ?",
            (f"WF-{year}-%",)
        )
        count = cursor.fetchone()[0] + 1
    return f"WF-{year}-{count:03d}"


# --- Workflow Endpoints ---

@app.get("/")
def root():
    return {"status": "ok", "service": "Workflow API"}


@app.get("/health")
def health():
    """Health check endpoint."""
    with get_db() as conn:
        cursor = conn.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "healthy", "version": "1.0.0", "database": "connected"}


@app.get("/workflows")
def list_workflows(status: Optional[str] = None, project: Optional[str] = None):
    """List all workflows, optionally filtered."""
    with get_db() as conn:
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if project:
            query += " AND project = ?"
            params.append(project)
        query += " ORDER BY created_at DESC LIMIT 50"

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


@app.get("/workflows/active")
def get_active_workflows():
    """Get all active (non-completed) workflows."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM active_workflows
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    """Get a specific workflow by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM workflows WHERE workflow_id = ?",
            (workflow_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return dict(row)


@app.post("/workflows")
def create_workflow(workflow: WorkflowCreate):
    """Create a new workflow."""
    workflow_id = generate_workflow_id()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO workflows (workflow_id, project, project_path, title, requirements, status)
            VALUES (?, ?, ?, ?, ?, 'PLANNING')
        """, (workflow_id, workflow.project, workflow.project_path, workflow.title, workflow.requirements))
        conn.commit()
    return {"workflow_id": workflow_id, "status": "PLANNING"}


@app.patch("/workflows/{workflow_id}")
def update_workflow(workflow_id: str, update: WorkflowUpdate):
    """Update a workflow."""
    with get_db() as conn:
        # Check exists
        cursor = conn.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Workflow not found")

        updates = []
        params = []
        if update.status:
            updates.append("status = ?")
            params.append(update.status)
            if update.status == "EXECUTING":
                updates.append("started_at = CURRENT_TIMESTAMP")
            elif update.status in ("COMPLETED", "FAILED", "REJECTED"):
                updates.append("completed_at = CURRENT_TIMESTAMP")
        if update.plan:
            updates.append("plan = ?")
            params.append(update.plan)
        if update.requirements:
            updates.append("requirements = ?")
            params.append(update.requirements)
        if update.github_issue_number:
            updates.append("github_issue_number = ?")
            params.append(update.github_issue_number)

        if updates:
            params.append(workflow_id)
            conn.execute(f"""
                UPDATE workflows SET {', '.join(updates)}
                WHERE workflow_id = ?
            """, params)
            conn.commit()

    return get_workflow(workflow_id)


# --- Task Endpoints ---

@app.get("/workflows/{workflow_id}/tasks")
def list_tasks(workflow_id: str):
    """List all tasks for a workflow."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM tasks WHERE workflow_id = ?
            ORDER BY sequence
        """, (workflow_id,))
        return [dict(row) for row in cursor.fetchall()]


@app.post("/workflows/{workflow_id}/tasks")
def create_task(workflow_id: str, task: TaskCreate):
    """Create a task for a workflow."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO tasks (workflow_id, sequence, description, status)
            VALUES (?, ?, ?, 'PENDING')
        """, (workflow_id, task.sequence, task.description))
        conn.commit()
    return {"status": "created"}


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    """Update a task."""
    with get_db() as conn:
        updates = ["status = ?"]
        params = [update.status]

        if update.status == "IN_PROGRESS":
            updates.append("started_at = CURRENT_TIMESTAMP")
        elif update.status in ("COMPLETED", "FAILED", "SKIPPED"):
            updates.append("completed_at = CURRENT_TIMESTAMP")

        if update.result:
            updates.append("result = ?")
            params.append(update.result)
        if update.error_message:
            updates.append("error_message = ?")
            params.append(update.error_message)

        params.append(task_id)
        conn.execute(f"""
            UPDATE tasks SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()
    return {"status": "updated"}


# --- Notification Endpoints ---

@app.post("/notifications")
def create_notification(notification: NotificationCreate):
    """Record a sent notification."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO notifications (workflow_id, notification_type, channel, message, delivered)
            VALUES (?, ?, ?, ?, TRUE)
        """, (notification.workflow_id, notification.notification_type,
              notification.channel, notification.message))
        conn.commit()
    return {"status": "recorded"}


# --- Test Result Endpoints ---

@app.post("/test-results")
def create_test_result(result: TestResultCreate):
    """Record a test result."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO test_results (workflow_id, test_type, test_name, passed, output)
            VALUES (?, ?, ?, ?, ?)
        """, (result.workflow_id, result.test_type, result.test_name,
              result.passed, result.output))
        conn.commit()
    return {"status": "recorded"}


@app.get("/workflows/{workflow_id}/test-results")
def list_test_results(workflow_id: str):
    """List test results for a workflow."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM test_results WHERE workflow_id = ?
            ORDER BY executed_at
        """, (workflow_id,))
        return [dict(row) for row in cursor.fetchall()]


# --- Stats ---

@app.get("/stats")
def get_stats():
    """Get workflow statistics."""
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM workflows")
        total = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM workflows WHERE status = 'COMPLETED'")
        completed = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM workflows WHERE status NOT IN ('COMPLETED', 'FAILED', 'REJECTED')")
        active = cursor.fetchone()[0]

        return {
            "total_workflows": total,
            "completed": completed,
            "active": active
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
