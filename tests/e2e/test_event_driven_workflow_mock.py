"""End-to-end test for the event-driven workflow with mocked LLM.

Verifies that the event-driven orchestrator correctly routes events
through the full workflow (PM → Architect → Coder → Reviewer) without
relying on a real LLM.
"""

import asyncio
import os
import shutil

import pytest

from backend.agents.built_in import register_built_in_plugins
from backend.agents.coder_agent import CoderAgent
from backend.config import settings as app_settings
from backend.core.event_bus import EventBus, EventType
from backend.core.plugin_registry import PluginRegistry
from backend.core.state_store import StateStore, WorkflowState
from backend.llm.client import LLMClient
from backend.orchestrator.event_driven_orchestrator import EventDrivenOrchestrator
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.tools.file_manager import FileManager


class FakeLLMClient(LLMClient):
    """LLM client that returns canned responses instead of calling real APIs."""

    def __init__(self):
        # Bypass parent init (no real keys needed)
        pass

    async def call(self, prompt, config):
        from backend.llm.models import LLMResponse

        sys = config.system_prompt.lower()
        if "product manager" in sys:
            return LLMResponse(content="# Spec\n\nBuild a hello world CLI.", model="mock")
        elif "system architect" in sys or ("architect" in sys and "developer" not in sys):
            return LLMResponse(content="# Architecture\n\nSingle file: main.py", model="mock")
        elif "software developer" in sys or "developer" in sys:
            return LLMResponse(content="""### FILE: main.py
```python
GREETING = "Hello, World!"

def main():
    print(GREETING)

if __name__ == "__main__":
    main()
```
""", model="mock")
        elif "code reviewer" in sys or "reviewer" in sys:
            return LLMResponse(content='{"passed": true, "issues": [], "summary": "LGTM"}', model="mock")
        return LLMResponse(content="OK", model="mock")


@pytest.fixture
def mock_deps(tmp_path_factory):
    """Set up orchestrator with mocked LLM."""
    output_dir = str(tmp_path_factory.mktemp("mock_e2e_output"))
    app_settings.output_dir = output_dir
    app_settings.use_docker_sandbox = False

    llm_client = FakeLLMClient()
    state_store = StateStore(base_dir=os.path.join(output_dir, "states"))
    ws_manager = WebSocketManager()

    event_bus = EventBus()
    plugin_registry = PluginRegistry()
    register_built_in_plugins(plugin_registry, llm_client)

    orchestrator = EventDrivenOrchestrator(
        event_bus=event_bus,
        plugin_registry=plugin_registry,
        ws_manager=ws_manager,
        state_store=state_store,
    )

    yield {
        "output_dir": output_dir,
        "state_store": state_store,
        "orchestrator": orchestrator,
        "event_bus": event_bus,
    }

    shutil.rmtree(output_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_mock_workflow_completes(mock_deps):
    """Full workflow completes with mock LLM."""
    project_id = "mock-e2e-001"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    output_dir = mock_deps["output_dir"]
    event_bus = mock_deps["event_bus"]

    completion_event = asyncio.Event()
    error_event = asyncio.Event()

    async def on_complete(event):
        if event.project_id == project_id:
            completion_event.set()

    async def on_error(event):
        if event.project_id == project_id:
            error_event.set()

    event_bus.subscribe(EventType.WORKFLOW_COMPLETED, on_complete)
    event_bus.subscribe(EventType.ERROR, on_error)

    await orchestrator.start_workflow(project_id, "Build a hello world CLI")

    # Wait up to 30 seconds for completion
    done, pending = await asyncio.wait(
        [
            asyncio.create_task(completion_event.wait()),
            asyncio.create_task(error_event.wait()),
        ],
        timeout=30,
        return_when=asyncio.FIRST_COMPLETED,
    )

    assert completion_event.is_set(), "Workflow did not complete (or errored)"
    assert not error_event.is_set(), "Workflow hit an error"

    # Verify state
    project = state_store.get_project(project_id)
    assert project is not None
    assert project.state == WorkflowState.DONE

    # Verify files
    fm = FileManager(base_dir=os.path.join(output_dir, project_id))
    files = fm.list_files()
    print(f"Generated files: {files}")

    assert any("spec" in f.lower() for f in files)
    assert any("arch" in f.lower() for f in files)
    assert any(f.endswith(".py") for f in files)

    # Verify entry point has no relative imports
    for f in files:
        if "main" in f.lower() and f.endswith(".py"):
            content = fm.read_file(f)
            assert "from ." not in content, f"Relative import found in {f}"

    # Verify event history
    history = event_bus.get_history(project_id)
    event_types = [e.type for e in history]
    assert EventType.PROJECT_CREATED in event_types
    assert EventType.SPEC_GENERATED in event_types
    assert EventType.ARCHITECTURE_GENERATED in event_types
    assert EventType.CODE_GENERATED in event_types
    assert EventType.SYNTAX_CHECKED in event_types
    assert EventType.REVIEW_COMPLETED in event_types
    assert EventType.WORKFLOW_COMPLETED in event_types


@pytest.mark.asyncio
async def test_mock_workflow_iteration(mock_deps):
    """Workflow with review failure and iteration."""
    project_id = "mock-e2e-002"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    event_bus = mock_deps["event_bus"]

    # Override the reviewer to always fail on first pass
    original_reviewer = orchestrator.registry.get("reviewer")

    class FailingReviewer:
        name = "reviewer"
        consumes = [EventType.SYNTAX_CHECKED]
        produces = EventType.REVIEW_COMPLETED

        async def execute(self, context, event):
            from backend.agents.base_agent import AgentOutput
            iteration = getattr(context, "iteration", 0)
            if iteration == 0:
                return AgentOutput(
                    content='{"passed": false, "issues": [{"severity": "error", "message": "Missing error handling"}], "summary": "Needs fix"}',
                    metadata={"passed": False},
                )
            return AgentOutput(
                content='{"passed": true, "issues": [], "summary": "LGTM"}',
                metadata={"passed": True},
            )

    # Replace reviewer plugin
    orchestrator.registry._plugins["reviewer"] = FailingReviewer()

    completion_event = asyncio.Event()

    async def on_complete(event):
        if event.project_id == project_id:
            completion_event.set()

    event_bus.subscribe(EventType.WORKFLOW_COMPLETED, on_complete)

    await orchestrator.start_workflow(project_id, "Build a hello world CLI")

    done, pending = await asyncio.wait(
        [asyncio.create_task(completion_event.wait())],
        timeout=30,
    )

    assert completion_event.is_set(), "Workflow with iteration did not complete"

    project = state_store.get_project(project_id)
    assert project.state == WorkflowState.DONE
    assert project.iteration_count >= 1, "Expected at least one iteration"

    # Verify iteration events in history
    history = event_bus.get_history(project_id)
    iteration_events = [e for e in history if e.type == EventType.ITERATION_STARTED]
    assert len(iteration_events) >= 1
