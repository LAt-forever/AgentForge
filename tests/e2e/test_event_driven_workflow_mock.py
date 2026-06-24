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
from backend.orchestrator.state_machine import StateMachine
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.tools.file_manager import FileManager


class FakeLLMClient(LLMClient):
    """LLM client that returns canned responses instead of calling real APIs."""

    def __init__(self):
        # Bypass parent init (no real keys needed)
        self.calls = []

    async def call(self, prompt, config):
        from backend.llm.models import LLMResponse

        self.calls.append({
            "prompt": prompt,
            "system_prompt": config.system_prompt,
        })

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
    ws_messages = []
    original_send_message = ws_manager.send_message

    async def recording_send_message(project_id, message):
        ws_messages.append((project_id, message))
        await original_send_message(project_id, message)

    ws_manager.send_message = recording_send_message

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
        "llm_client": llm_client,
        "ws_messages": ws_messages,
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


@pytest.mark.asyncio
async def test_mock_follow_up_triggers_iteration(mock_deps):
    """User follow-up continues iterating on a completed project."""
    project_id = "mock-e2e-followup"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    event_bus = mock_deps["event_bus"]

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
    assert completion_event.is_set(), "Initial workflow did not complete"

    initial_iterations = state_store.get_project(project_id).iteration_count

    # Reset completion event and trigger follow-up
    completion_event.clear()
    await orchestrator.start_followup(project_id, "Add a greeting argument")

    done, pending = await asyncio.wait(
        [asyncio.create_task(completion_event.wait())],
        timeout=30,
    )
    assert completion_event.is_set(), "Follow-up iteration did not complete"

    project = state_store.get_project(project_id)
    assert project.state == WorkflowState.DONE
    assert project.iteration_count > initial_iterations, "Expected iteration count to increase"

    history = event_bus.get_history(project_id)
    followup_events = [
        e for e in history
        if e.type == EventType.ITERATION_STARTED and e.payload.get("reason") == "user_followup"
    ]
    assert len(followup_events) >= 1


@pytest.mark.asyncio
async def test_static_web_workflow_profile_completes(mock_deps):
    """Static web requirements use the web workflow profile and validator."""
    project_id = "mock-e2e-static-web"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    output_dir = mock_deps["output_dir"]
    event_bus = mock_deps["event_bus"]
    llm_client = mock_deps["llm_client"]
    ws_messages = mock_deps["ws_messages"]

    async def static_web_call(prompt, config):
        from backend.llm.models import LLMResponse

        llm_client.calls.append({
            "prompt": prompt,
            "system_prompt": config.system_prompt,
        })

        sys = config.system_prompt.lower()
        lowered_prompt = prompt.lower()
        if "product manager" in sys:
            assert "browser-ready static files" in lowered_prompt
            assert "index.html" in lowered_prompt
            return LLMResponse(
                content="# Spec\n\nBuild an interactive pomodoro web page.",
                model="mock",
            )
        if "system architect" in sys or ("architect" in sys and "developer" not in sys):
            assert "browser-ready static files" in lowered_prompt
            return LLMResponse(
                content="# Architecture\n\nFiles: index.html, style.css, script.js",
                model="mock",
            )
        if "software developer" in sys or "developer" in sys:
            assert "index.html" in lowered_prompt
            assert "interactive web page" in lowered_prompt
            assert "generate all code in python" not in lowered_prompt
            return LLMResponse(content="""### FILE: index.html
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>番茄钟</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <main class="app">
      <h1>番茄钟</h1>
      <p id="status">准备开始</p>
      <button id="toggle" type="button">开始</button>
    </main>
    <script src="script.js"></script>
  </body>
</html>
```

### FILE: style.css
```css
body {
  font-family: sans-serif;
}
```

### FILE: script.js
```javascript
const status = document.getElementById("status");
const toggle = document.getElementById("toggle");
let running = false;

toggle.addEventListener("click", () => {
  running = !running;
  status.textContent = running ? "专注中" : "准备开始";
  toggle.textContent = running ? "暂停" : "开始";
});
```
""", model="mock")
        if "code reviewer" in sys or "reviewer" in sys:
            assert "browser-ready static files" in lowered_prompt
            assert "index.html" in lowered_prompt
            assert "style.css" in lowered_prompt
            return LLMResponse(
                content='{"passed": true, "issues": [], "summary": "LGTM"}',
                model="mock",
            )
        return LLMResponse(content="OK", model="mock")

    llm_client.call = static_web_call

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

    await orchestrator.start_workflow(project_id, "做一个番茄钟网页工具")

    done, pending = await asyncio.wait(
        [
            asyncio.create_task(completion_event.wait()),
            asyncio.create_task(error_event.wait()),
        ],
        timeout=30,
        return_when=asyncio.FIRST_COMPLETED,
    )

    assert completion_event.is_set(), "Static web workflow did not complete (or errored)"
    assert not error_event.is_set(), "Static web workflow hit an error"

    project = state_store.get_project(project_id)
    assert project is not None
    assert project.state == WorkflowState.DONE
    assert project.workflow_profile == "static_web"
    assert project.artifact_status["status"] == "ready"
    assert (
        project.artifact_status["preview_url"]
        == f"/api/projects/{project_id}/preview/"
    )
    matching_messages = [
        message for pid, message in ws_messages
        if pid == project_id
        and message.get("type") == "workflow_state"
        and message.get("artifact_status", {}).get("status") == "ready"
    ]
    assert matching_messages
    assert (
        matching_messages[-1]["artifact_status"]["preview_url"]
        == f"/api/projects/{project_id}/preview/"
    )

    fm = FileManager(base_dir=os.path.join(output_dir, project_id))
    assert fm.exists("index.html")
    assert fm.exists("style.css")
    assert fm.exists("script.js")


@pytest.mark.asyncio
async def test_static_web_validation_retries_are_bounded(mock_deps):
    """Repeated invalid static-web artifacts consume the shared iteration budget."""
    project_id = "mock-e2e-static-web-bounded"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    event_bus = mock_deps["event_bus"]
    llm_client = mock_deps["llm_client"]
    ws_messages = mock_deps["ws_messages"]

    original_max_iterations = app_settings.max_review_iterations
    app_settings.max_review_iterations = 1

    async def invalid_static_web_call(prompt, config):
        from backend.llm.models import LLMResponse

        llm_client.calls.append({
            "prompt": prompt,
            "system_prompt": config.system_prompt,
        })

        sys = config.system_prompt.lower()
        lowered_prompt = prompt.lower()
        if "product manager" in sys:
            assert "browser-ready static files" in lowered_prompt
            return LLMResponse(
                content="# Spec\n\nBuild an interactive pomodoro web page.",
                model="mock",
            )
        if "system architect" in sys or ("architect" in sys and "developer" not in sys):
            assert "browser-ready static files" in lowered_prompt
            return LLMResponse(
                content="# Architecture\n\nFiles: index.html and style.css only",
                model="mock",
            )
        if "software developer" in sys or "developer" in sys:
            assert "generate all code in python" not in lowered_prompt
            return LLMResponse(content="""### FILE: index.html
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>番茄钟</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <h1>番茄钟</h1>
    <script src="script.js"></script>
  </body>
</html>
```

### FILE: style.css
```css
body {
  font-family: sans-serif;
}
```
""", model="mock")
        if "code reviewer" in sys or "reviewer" in sys:
            return LLMResponse(
                content='{"passed": true, "issues": [], "summary": "LGTM"}',
                model="mock",
            )
        return LLMResponse(content="OK", model="mock")

    llm_client.call = invalid_static_web_call

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

    try:
        await orchestrator.start_workflow(project_id, "做一个番茄钟网页工具")

        done, pending = await asyncio.wait(
            [
                asyncio.create_task(completion_event.wait()),
                asyncio.create_task(error_event.wait()),
            ],
            timeout=30,
            return_when=asyncio.FIRST_COMPLETED,
        )

        assert completion_event.is_set(), "Bounded static web workflow did not complete"
        assert not error_event.is_set(), "Bounded static web workflow hit an error"

        project = state_store.get_project(project_id)
        assert project is not None
        assert project.state == WorkflowState.DONE
        assert project.iteration_count == 1
        assert project.artifact_status["status"] == "invalid_refs"
        assert project.artifact_status["preview_url"] == ""
        matching_messages = [
            message for pid, message in ws_messages
            if pid == project_id
            and message.get("type") == "workflow_state"
            and message.get("artifact_status", {}).get("status") == "invalid_refs"
        ]
        assert matching_messages
        assert matching_messages[-1]["artifact_status"]["preview_url"] == ""
        assert matching_messages[-1]["iteration_count"] == project.iteration_count

        history = event_bus.get_history(project_id)
        iteration_events = [e for e in history if e.type == EventType.ITERATION_STARTED]
        syntax_checked_events = [e for e in history if e.type == EventType.SYNTAX_CHECKED]
        assert len(iteration_events) == 1
        assert len(syntax_checked_events) == 1
    finally:
        app_settings.max_review_iterations = original_max_iterations


@pytest.mark.asyncio
async def test_workflow_state_message_uses_persisted_iteration_count(mock_deps):
    """Workflow state messages expose the shared persisted retry counter."""
    project_id = "mock-e2e-iteration-count"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    ws_messages = mock_deps["ws_messages"]

    state_store.create_project(project_id, "Build a static web app")
    state_store.increment_iteration(project_id)
    state_store.increment_iteration(project_id)
    sm = StateMachine(max_iterations=3)
    orchestrator._state_machines[project_id] = sm

    await orchestrator._notify_workflow_state(project_id, sm)

    workflow_messages = [
        message for pid, message in ws_messages
        if pid == project_id and message.get("type") == "workflow_state"
    ]
    assert workflow_messages[-1]["iteration_count"] == 2


@pytest.mark.asyncio
async def test_review_feedback_respects_exhausted_retry_budget(mock_deps):
    """A final failed review should complete instead of emitting another retry."""
    project_id = "mock-e2e-review-budget"
    orchestrator = mock_deps["orchestrator"]
    state_store = mock_deps["state_store"]
    event_bus = mock_deps["event_bus"]

    original_max_iterations = app_settings.max_review_iterations
    app_settings.max_review_iterations = 1

    class AlwaysFailingReviewer:
        name = "reviewer"
        consumes = [EventType.SYNTAX_CHECKED]
        produces = EventType.REVIEW_COMPLETED

        async def execute(self, context, event):
            from backend.agents.base_agent import AgentOutput

            return AgentOutput(
                content='{"passed": false, "issues": [{"severity": "error", "message": "Still broken"}], "summary": "Needs fix"}',
                metadata={"passed": False},
            )

    orchestrator.registry._plugins["reviewer"] = AlwaysFailingReviewer()

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

    try:
        await orchestrator.start_workflow(project_id, "Build a hello world CLI")

        done, pending = await asyncio.wait(
            [
                asyncio.create_task(completion_event.wait()),
                asyncio.create_task(error_event.wait()),
            ],
            timeout=30,
            return_when=asyncio.FIRST_COMPLETED,
        )

        assert completion_event.is_set(), "Exhausted review-budget workflow did not complete"
        assert not error_event.is_set(), "Exhausted review-budget workflow hit an error"

        project = state_store.get_project(project_id)
        assert project is not None
        assert project.state == WorkflowState.DONE
        assert project.iteration_count == 0

        history = event_bus.get_history(project_id)
        review_feedback_iterations = [
            e for e in history
            if e.type == EventType.ITERATION_STARTED
            and e.payload.get("reason") == "review_feedback"
        ]
        assert review_feedback_iterations == []
    finally:
        app_settings.max_review_iterations = original_max_iterations
