"""Tests for the StateStore."""

import os
import json
import pytest
from tempfile import TemporaryDirectory

from backend.core.state_store import StateStore, WorkflowState, ProjectState


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as td:
        yield td


@pytest.fixture
def state_store(temp_dir):
    return StateStore(base_dir=temp_dir)


class TestCreateAndGetProject:
    """Test creating and retrieving projects."""

    def test_create_and_get_project(self, state_store):
        """Create a project and verify it can be retrieved with IDLE state."""
        project = state_store.create_project("proj_1", requirement="Build a web app")

        assert project.id == "proj_1"
        assert project.state == WorkflowState.IDLE
        assert project.requirement == "Build a web app"

        retrieved = state_store.get_project("proj_1")
        assert retrieved is not None
        assert retrieved.id == "proj_1"
        assert retrieved.state == WorkflowState.IDLE


class TestUpdateState:
    """Test updating workflow state."""

    def test_update_state(self, state_store, temp_dir):
        """Update state to PLANNING and verify it's persisted."""
        state_store.create_project("proj_1")
        state_store.update_state("proj_1", WorkflowState.PLANNING)

        project = state_store.get_project("proj_1")
        assert project.state == WorkflowState.PLANNING

        # Verify persisted to disk
        with open(os.path.join(temp_dir, "proj_1.json")) as f:
            data = json.load(f)
        assert data["state"] == "planning"


class TestUpdateAgentStatus:
    """Test updating agent status."""

    def test_update_agent_status(self, state_store):
        """Update coder agent status and verify in project."""
        state_store.create_project("proj_1")
        state_store.update_agent_status("proj_1", "coder", {"status": "running", "detail": "coding"})

        project = state_store.get_project("proj_1")
        assert project.agent_statuses["coder"]["status"] == "running"
        assert project.agent_statuses["coder"]["detail"] == "coding"


class TestPersistence:
    """Test persistence across StateStore instances."""

    def test_persistence(self, temp_dir):
        """Create and update, then new StateStore with same dir loads state."""
        store1 = StateStore(base_dir=temp_dir)
        store1.create_project("proj_1")
        store1.update_state("proj_1", WorkflowState.CODING)
        store1.update_agent_status("proj_1", "reviewer", {"status": "completed"})
        store1.update_output("proj_1", "design_doc", "design.md")
        store1.increment_iteration("proj_1")

        # Create new store with same directory
        store2 = StateStore(base_dir=temp_dir)
        project = store2.get_project("proj_1")

        assert project is not None
        assert project.state == WorkflowState.CODING
        assert project.agent_statuses["reviewer"]["status"] == "completed"
        assert project.outputs["design_doc"] == "design.md"
        assert project.iteration_count == 1


class TestListProjects:
    """Test listing all projects."""

    def test_list_projects(self, state_store):
        """List all projects in the store."""
        state_store.create_project("proj_a")
        state_store.create_project("proj_b")

        projects = state_store.list_projects()
        assert sorted(projects) == ["proj_a", "proj_b"]


class TestIncrementIteration:
    """Test incrementing iteration count."""

    def test_increment_iteration(self, state_store):
        """Increment iteration count."""
        state_store.create_project("proj_1")
        assert state_store.get_project("proj_1").iteration_count == 0

        state_store.increment_iteration("proj_1")
        assert state_store.get_project("proj_1").iteration_count == 1

        state_store.increment_iteration("proj_1")
        assert state_store.get_project("proj_1").iteration_count == 2


class TestUpdateOutput:
    """Test updating outputs."""

    def test_update_output(self, state_store):
        """Update an output key-value pair."""
        state_store.create_project("proj_1")
        state_store.update_output("proj_1", "code", "print('hello')")

        project = state_store.get_project("proj_1")
        assert project.outputs["code"] == "print('hello')"

    def test_update_output_overwrite(self, state_store):
        """Overwrite an existing output key."""
        state_store.create_project("proj_1")
        state_store.update_output("proj_1", "code", "v1")
        state_store.update_output("proj_1", "code", "v2")

        project = state_store.get_project("proj_1")
        assert project.outputs["code"] == "v2"
