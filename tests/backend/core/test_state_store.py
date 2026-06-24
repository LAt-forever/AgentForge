"""Tests for the StateStore."""

import os
import json
import pytest
from tempfile import TemporaryDirectory

from backend.core.state_store import StateStore, WorkflowState, ProjectState
from backend.core.workflow_profiles import DEFAULT_PROFILE


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

    def test_create_project_has_workflow_profile_defaults(self, state_store):
        """Created projects default to the standard workflow profile."""
        project = state_store.create_project("proj_1", requirement="Build a CLI")

        assert project.workflow_profile == DEFAULT_PROFILE
        assert project.artifact_status == {
            "type": "none",
            "status": "unknown",
            "preview_url": "",
            "issues": [],
        }

    def test_project_state_from_dict_defaults_missing_profile_fields(self):
        """Older persisted state without new fields loads with defaults."""
        project = ProjectState.from_dict(
            {
                "id": "proj_legacy",
                "state": "idle",
                "requirement": "Legacy project",
            }
        )

        assert project.workflow_profile == DEFAULT_PROFILE
        assert project.artifact_status == {
            "type": "none",
            "status": "unknown",
            "preview_url": "",
            "issues": [],
        }


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


class TestUpdateWorkflowProfile:
    """Test updating workflow profile metadata."""

    def test_update_workflow_profile(self, state_store):
        """Update workflow profile and verify it is persisted in state."""
        state_store.create_project("proj_1")
        before = state_store.get_project("proj_1").updated_at

        state_store.update_workflow_profile("proj_1", "static_web")

        project = state_store.get_project("proj_1")
        assert project.workflow_profile == "static_web"
        assert project.updated_at >= before


class TestUpdateArtifactStatus:
    """Test updating artifact validation status."""

    def test_update_artifact_status(self, state_store):
        """Update artifact status and verify it is persisted in state."""
        state_store.create_project("proj_1")
        status = {
            "type": "web_artifact",
            "status": "valid",
            "preview_url": "/preview/proj_1/index.html",
            "issues": [],
        }

        state_store.update_artifact_status("proj_1", status)

        project = state_store.get_project("proj_1")
        assert project.artifact_status == status

    def test_update_artifact_status_defensively_copies_input(self, state_store):
        """Mutating the input status after update does not alter stored state."""
        state_store.create_project("proj_1")
        status = {
            "type": "web_artifact",
            "status": "valid",
            "preview_url": "/preview/proj_1/index.html",
            "issues": ["missing alt text"],
        }

        state_store.update_artifact_status("proj_1", status)
        status["status"] = "invalid"
        status["issues"].append("missing title")

        project = state_store.get_project("proj_1")
        assert project.artifact_status == {
            "type": "web_artifact",
            "status": "valid",
            "preview_url": "/preview/proj_1/index.html",
            "issues": ["missing alt text"],
        }


class TestPersistence:
    """Test persistence across StateStore instances."""

    def test_persistence(self, temp_dir):
        """Create and update, then new StateStore with same dir loads state."""
        store1 = StateStore(base_dir=temp_dir)
        store1.create_project("proj_1")
        store1.update_state("proj_1", WorkflowState.CODING)
        store1.update_agent_status("proj_1", "reviewer", {"status": "completed"})
        store1.update_output("proj_1", "design_doc", "design.md")
        store1.update_workflow_profile("proj_1", "static_web")
        store1.update_artifact_status(
            "proj_1",
            {
                "type": "web_artifact",
                "status": "invalid",
                "preview_url": "",
                "issues": ["missing index.html"],
            },
        )
        store1.increment_iteration("proj_1")

        # Create new store with same directory
        store2 = StateStore(base_dir=temp_dir)
        project = store2.get_project("proj_1")

        assert project is not None
        assert project.state == WorkflowState.CODING
        assert project.agent_statuses["reviewer"]["status"] == "completed"
        assert project.outputs["design_doc"] == "design.md"
        assert project.workflow_profile == "static_web"
        assert project.artifact_status == {
            "type": "web_artifact",
            "status": "invalid",
            "preview_url": "",
            "issues": ["missing index.html"],
        }
        assert project.iteration_count == 1


class TestListProjects:
    """Test listing all projects."""

    def test_list_projects(self, state_store):
        """List all projects in the store."""
        state_store.create_project("proj_a")
        state_store.create_project("proj_b")

        projects = state_store.list_projects()
        assert sorted(projects) == ["proj_a", "proj_b"]


class TestListProjectsDetailed:
    """Test detailed project listing for the history UI."""

    def test_list_projects_detailed(self, state_store):
        """Detailed listing returns metadata for each project."""
        state_store.create_project("p1", "build a calculator")
        state_store.create_project("p2", "build a todo app")
        state_store.update_state("p2", WorkflowState.DONE)

        detailed = state_store.list_projects_detailed()

        assert len(detailed) == 2
        by_id = {d["project_id"]: d for d in detailed}
        assert by_id["p1"]["requirement"] == "build a calculator"
        assert by_id["p1"]["state"] == "idle"
        assert by_id["p2"]["state"] == "done"
        assert by_id["p1"]["workflow_profile"] == DEFAULT_PROFILE
        assert by_id["p1"]["artifact_status"] == {
            "type": "none",
            "status": "unknown",
            "preview_url": "",
            "issues": [],
        }
        assert "updated_at" in by_id["p1"]
        assert "requirement_preview" in by_id["p1"]

    def test_list_projects_detailed_sorted_newest_first(self, state_store):
        """Detailed listing is sorted by updated_at, newest first."""
        state_store.create_project("old", "first")
        state_store.create_project("new", "second")
        # Force a newer updated_at on "new"
        state_store.update_output("new", "spec", "x")

        detailed = state_store.list_projects_detailed()
        assert detailed[0]["project_id"] == "new"

    def test_list_projects_detailed_returns_copied_artifact_status(self, state_store):
        """Mutating detailed-list results does not alter cached project state."""
        state_store.create_project("proj_1", "build a web page")
        state_store.update_artifact_status(
            "proj_1",
            {
                "type": "web_artifact",
                "status": "valid",
                "preview_url": "/preview/proj_1/index.html",
                "issues": ["missing alt text"],
            },
        )

        detailed = state_store.list_projects_detailed()
        detailed[0]["artifact_status"]["status"] = "invalid"
        detailed[0]["artifact_status"]["issues"].append("missing title")

        project = state_store.get_project("proj_1")
        assert project.artifact_status == {
            "type": "web_artifact",
            "status": "valid",
            "preview_url": "/preview/proj_1/index.html",
            "issues": ["missing alt text"],
        }


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
