"""State Store for persisting project and agent state."""

import copy
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from backend.core.workflow_profiles import DEFAULT_PROFILE


def _default_artifact_status() -> dict:
    return {
        "type": "none",
        "status": "unknown",
        "preview_url": "",
        "issues": [],
    }


class WorkflowState(Enum):
    """States of the overall workflow."""

    IDLE = "idle"
    PLANNING = "planning"
    DESIGNING = "designing"
    CODING = "coding"
    REVIEWING = "reviewing"
    DONE = "done"


class AgentStatus(Enum):
    """Status of an individual agent."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProjectState:
    """The state of a single project."""

    id: str
    state: WorkflowState = WorkflowState.IDLE
    requirement: str = ""
    agent_statuses: dict = field(default_factory=dict)
    iteration_count: int = 0
    max_iterations: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outputs: dict = field(default_factory=dict)
    workflow_profile: str = DEFAULT_PROFILE
    artifact_status: dict = field(default_factory=_default_artifact_status)

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "id": self.id,
            "state": self.state.value,
            "requirement": self.requirement,
            "agent_statuses": self.agent_statuses,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "outputs": self.outputs,
            "workflow_profile": self.workflow_profile,
            "artifact_status": copy.deepcopy(self.artifact_status),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        """Deserialize from a dictionary."""
        return cls(
            id=data["id"],
            state=WorkflowState(data["state"]),
            requirement=data.get("requirement", ""),
            agent_statuses=data.get("agent_statuses", {}),
            iteration_count=data.get("iteration_count", 0),
            max_iterations=data.get("max_iterations", 3),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            outputs=data.get("outputs", {}),
            workflow_profile=data.get("workflow_profile", DEFAULT_PROFILE),
            artifact_status=copy.deepcopy(
                data.get("artifact_status", _default_artifact_status())
            ),
        )


class StateStore:
    """Persistent store for project state, backed by JSON files."""

    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._cache: dict[str, ProjectState] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all existing project JSON files into the cache."""
        if not os.path.isdir(self._base_dir):
            return
        for filename in os.listdir(self._base_dir):
            if filename.endswith(".json"):
                project_id = filename[:-5]
                filepath = os.path.join(self._base_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                self._cache[project_id] = ProjectState.from_dict(data)

    def _save(self, project_id: str) -> None:
        """Persist a project to disk."""
        project = self._cache[project_id]
        filepath = os.path.join(self._base_dir, f"{project_id}.json")
        with open(filepath, "w") as f:
            json.dump(project.to_dict(), f, indent=2)

    def create_project(self, project_id: str, requirement: str = "") -> ProjectState:
        """Create a new project and persist it."""
        project = ProjectState(id=project_id, requirement=requirement)
        self._cache[project_id] = project
        self._save(project_id)
        return project

    def get_project(self, project_id: str) -> Optional[ProjectState]:
        """Retrieve a project by ID."""
        return self._cache.get(project_id)

    def update_state(self, project_id: str, state: WorkflowState) -> None:
        """Update the workflow state of a project."""
        project = self._cache[project_id]
        project.state = state
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def update_agent_status(
        self, project_id: str, agent_name: str, status: dict
    ) -> None:
        """Update the status of an agent for a project."""
        project = self._cache[project_id]
        project.agent_statuses[agent_name] = status
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def increment_iteration(self, project_id: str) -> None:
        """Increment the iteration count for a project."""
        project = self._cache[project_id]
        project.iteration_count += 1
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def update_output(self, project_id: str, key: str, value: str) -> None:
        """Update an output key-value pair for a project."""
        project = self._cache[project_id]
        project.outputs[key] = value
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def update_workflow_profile(self, project_id: str, profile: str) -> None:
        """Update the workflow profile for a project."""
        project = self._cache[project_id]
        project.workflow_profile = profile
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def update_artifact_status(self, project_id: str, status: dict) -> None:
        """Update artifact validation and preview status for a project."""
        project = self._cache[project_id]
        project.artifact_status = copy.deepcopy(status)
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def list_projects(self) -> list[str]:
        """List all project IDs in the store."""
        return list(self._cache.keys())

    def list_projects_detailed(self) -> list[dict]:
        """List all projects with metadata, newest-updated first."""
        projects = []
        for project in self._cache.values():
            requirement = project.requirement
            projects.append(
                {
                    "project_id": project.id,
                    "state": project.state.value,
                    "requirement": requirement,
                    "requirement_preview": requirement[:50],
                    "iteration_count": project.iteration_count,
                    "workflow_profile": project.workflow_profile,
                    "artifact_status": copy.deepcopy(project.artifact_status),
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                }
            )
        projects.sort(key=lambda p: p["updated_at"], reverse=True)
        return projects
