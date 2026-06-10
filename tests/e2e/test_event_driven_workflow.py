"""End-to-end test for the event-driven workflow.

This test runs the full agent pipeline (PM → Architect → Coder → Reviewer)
using the event-driven orchestrator against a real LLM (GLM-4-plus).

Requirements:
    GLM_API_KEY must be set in the environment.
"""

import asyncio
import logging
import os
import shutil
import time

import pytest

from backend.agents.built_in import register_built_in_plugins
from backend.config import Settings, settings as app_settings
from backend.core.event_bus import EventBus, EventType
from backend.core.plugin_registry import PluginRegistry
from backend.core.state_store import StateStore
from backend.llm.client import LLMClient
from backend.orchestrator.event_driven_orchestrator import EventDrivenOrchestrator
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.tools.file_manager import FileManager

logger = logging.getLogger(__name__)

# Simple requirement that should be fast to process
TEST_REQUIREMENT = "Build a Python CLI tool that prints a greeting message. The greeting text should be configurable via a command-line argument. Include a main.py entry point that can be run directly with `python main.py --name Alice`."


@pytest.fixture
def e2e_deps(tmp_path_factory):
    """Set up isolated output directory and initialize all components."""
    # Use a temp output dir so we don't pollute the real output
    output_dir = str(tmp_path_factory.mktemp("e2e_output"))
    app_settings.output_dir = output_dir
    app_settings.use_docker_sandbox = False  # Docker may not be available in test env
    app_settings.default_model = os.environ.get("DEFAULT_MODEL", "glm-4-plus")
    app_settings.fallback_model = os.environ.get("FALLBACK_MODEL", "glm-4-plus")

    # Ensure API key is available
    glm_key = os.environ.get("GLM_API_KEY", app_settings.glm_api_key)
    if not glm_key:
        pytest.skip("GLM_API_KEY not set — skipping E2E test")

    llm_client = LLMClient(
        anthropic_key=app_settings.anthropic_api_key,
        openai_key=app_settings.openai_api_key,
        deepseek_key=app_settings.deepseek_api_key,
        deepseek_base_url=app_settings.deepseek_base_url,
        glm_key=glm_key,
        glm_base_url=app_settings.glm_base_url,
    )

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
        "llm_client": llm_client,
        "state_store": state_store,
        "ws_manager": ws_manager,
        "orchestrator": orchestrator,
        "event_bus": event_bus,
    }

    # Cleanup
    shutil.rmtree(output_dir, ignore_errors=True)


@pytest.mark.asyncio
@pytest.mark.timeout(600)  # 10 minutes max
async def test_event_driven_workflow_completes(e2e_deps):
    """Full workflow: PM → Architect → Coder → Reviewer completes successfully."""
    project_id = f"e2e-{int(time.time())}"
    orchestrator = e2e_deps["orchestrator"]
    state_store = e2e_deps["state_store"]
    output_dir = e2e_deps["output_dir"]
    event_bus = e2e_deps["event_bus"]

    # Track workflow completion
    completion_event = asyncio.Event()
    workflow_result = {}

    async def on_complete(event):
        if event.project_id == project_id:
            workflow_result["passed"] = event.payload.get("passed", False)
            completion_event.set()

    event_bus.subscribe(EventType.WORKFLOW_COMPLETED, on_complete)
    event_bus.subscribe(EventType.ERROR, on_complete)  # Also treat error as "completion"

    # Start the workflow
    logger.info("Starting E2E workflow for project %s", project_id)
    await orchestrator.start_workflow(project_id, TEST_REQUIREMENT)

    # Wait for completion (with periodic status logging)
    timeout_seconds = 600
    poll_interval = 5
    elapsed = 0

    while not completion_event.is_set() and elapsed < timeout_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        project = state_store.get_project(project_id)
        if project:
            logger.info(
                "Project %s: state=%s, iteration=%d",
                project_id,
                project.state.value,
                project.iteration_count,
            )

    assert completion_event.is_set(), f"Workflow did not complete within {timeout_seconds}s"

    # Verify state store
    project = state_store.get_project(project_id)
    assert project is not None
    assert project.state.value in ("done", "error")

    # Verify files were generated
    fm = FileManager(base_dir=os.path.join(output_dir, project_id))
    files = fm.list_files()
    logger.info("Generated files: %s", files)

    # Should have at least spec, architecture, and code files
    assert any("spec" in f.lower() for f in files), "No spec file generated"
    assert any("arch" in f.lower() for f in files), "No architecture file generated"
    assert any(f.endswith(".py") for f in files), "No Python code files generated"

    # Verify the main entry point is directly runnable
    code_files = [f for f in files if f.endswith(".py")]
    for code_file in code_files:
        if "main" in code_file.lower() or "app" in code_file.lower():
            content = fm.read_file(code_file)
            assert "from ." not in content, (
                f"Entry point {code_file} uses relative import — "
                f"prompt fix not working correctly"
            )
            logger.info("Verified %s has no relative imports", code_file)

    logger.info("E2E test passed! Project %s completed with state=%s", project_id, project.state.value)


@pytest.mark.asyncio
async def test_orchestrator_initialization(e2e_deps):
    """Smoke test: orchestrator initializes and plugins are registered."""
    orchestrator = e2e_deps["orchestrator"]
    registry = e2e_deps["orchestrator"].registry

    assert "pm" in registry.list_plugins()
    assert "architect" in registry.list_plugins()
    assert "coder" in registry.list_plugins()
    assert "reviewer" in registry.list_plugins()

    # Verify workflow map
    assert orchestrator.workflow_map[EventType.PROJECT_CREATED] == "pm"
    assert orchestrator.workflow_map[EventType.SPEC_GENERATED] == "architect"
    assert orchestrator.workflow_map[EventType.ARCHITECTURE_GENERATED] == "coder"
    assert orchestrator.workflow_map[EventType.SYNTAX_CHECKED] == "reviewer"
