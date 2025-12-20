"""
E2E Tests for Workflow API

Run with: pytest tests/test_api.py -v
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    import tempfile
    import os

    # Use temporary database for tests
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db = f.name

    os.environ['WORKFLOW_DB_PATH'] = test_db

    # Import after setting env var
    from main import app

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    try:
        os.unlink(test_db)
    except:
        pass


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestWorkflowCRUD:
    """Test workflow CRUD operations."""

    def test_create_workflow(self, client):
        """Should create a new workflow."""
        response = client.post("/workflows", json={
            "project": "test-project",
            "title": "Test Workflow",
            "requirements": '{"test": true}'
        })
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["workflow_id"].startswith("WF-")

    def test_get_workflow(self, client):
        """Should retrieve created workflow."""
        # Create first
        create_resp = client.post("/workflows", json={
            "project": "test-project",
            "title": "Test Workflow"
        })
        workflow_id = create_resp.json()["workflow_id"]

        # Then get
        response = client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["title"] == "Test Workflow"
        assert data["status"] == "PLANNING"

    def test_get_nonexistent_workflow(self, client):
        """Should return 404 for nonexistent workflow."""
        response = client.get("/workflows/WF-NONEXISTENT")
        assert response.status_code == 404

    def test_list_workflows(self, client):
        """Should list all workflows."""
        # Create a few workflows
        for i in range(3):
            client.post("/workflows", json={
                "project": "test-project",
                "title": f"Workflow {i}"
            })

        response = client.get("/workflows")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_list_active_workflows(self, client):
        """Should list only active workflows."""
        # Create and complete one
        create_resp = client.post("/workflows", json={
            "project": "test-project",
            "title": "Completed Workflow"
        })
        wf_id = create_resp.json()["workflow_id"]
        client.patch(f"/workflows/{wf_id}/status", json={"status": "COMPLETED"})

        # Create active one
        client.post("/workflows", json={
            "project": "test-project",
            "title": "Active Workflow"
        })

        response = client.get("/workflows/active")
        assert response.status_code == 200
        data = response.json()
        # Only active workflow should be in list
        assert all(wf["status"] != "COMPLETED" for wf in data)


class TestWorkflowStatus:
    """Test workflow status transitions."""

    def test_status_transition_planning_to_confirmed(self, client):
        """Should allow transition from PLANNING to CONFIRMED."""
        create_resp = client.post("/workflows", json={
            "project": "test-project",
            "title": "Test Workflow"
        })
        wf_id = create_resp.json()["workflow_id"]

        response = client.patch(f"/workflows/{wf_id}/status", json={
            "status": "CONFIRMED"
        })
        assert response.status_code == 200

        # Verify
        get_resp = client.get(f"/workflows/{wf_id}")
        assert get_resp.json()["status"] == "CONFIRMED"

    def test_status_transition_full_lifecycle(self, client):
        """Should handle full workflow lifecycle."""
        # Create
        create_resp = client.post("/workflows", json={
            "project": "test-project",
            "title": "Lifecycle Test"
        })
        wf_id = create_resp.json()["workflow_id"]

        # Progress through states
        for status in ["CONFIRMED", "EXECUTING", "TESTING", "COMPLETED"]:
            response = client.patch(f"/workflows/{wf_id}/status", json={
                "status": status
            })
            assert response.status_code == 200

        # Verify final state
        get_resp = client.get(f"/workflows/{wf_id}")
        assert get_resp.json()["status"] == "COMPLETED"


class TestWorkflowPlan:
    """Test workflow plan management."""

    def test_update_plan(self, client):
        """Should update workflow plan."""
        create_resp = client.post("/workflows", json={
            "project": "test-project",
            "title": "Plan Test"
        })
        wf_id = create_resp.json()["workflow_id"]

        plan_content = "# Implementation Plan\n\n1. Step one\n2. Step two"
        response = client.patch(f"/workflows/{wf_id}/plan", json={
            "plan": plan_content
        })
        assert response.status_code == 200

        # Verify
        get_resp = client.get(f"/workflows/{wf_id}")
        assert get_resp.json()["plan"] == plan_content


class TestStats:
    """Test statistics endpoint."""

    def test_stats_endpoint(self, client):
        """Should return workflow statistics."""
        # Create some workflows with different statuses
        for title, status in [("Active", "PLANNING"), ("Done", "COMPLETED")]:
            resp = client.post("/workflows", json={
                "project": "test-project",
                "title": title
            })
            if status != "PLANNING":
                wf_id = resp.json()["workflow_id"]
                client.patch(f"/workflows/{wf_id}/status", json={"status": status})

        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_workflows" in data
        assert "completed" in data
        assert "active" in data
