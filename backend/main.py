"""FastAPI application entry point."""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.llm.client import LLMClient
from backend.core.state_store import StateStore, WorkflowState
from backend.core.settings_manager import SettingsManager
from backend.tools.file_manager import FileManager
from backend.tools.code_runner import CodeRunner
from backend.tools.git_manager import GitManager
from backend.orchestrator.state_machine import StateMachine
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.orchestrator.scheduler import AgentScheduler
from backend.agents.base_agent import AgentContext

logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
llm_client: LLMClient | None = None
state_store: StateStore | None = None
ws_manager: WebSocketManager | None = None
settings_manager: SettingsManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and clean up global resources."""
    global llm_client, state_store, ws_manager, settings_manager

    llm_client = LLMClient(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
        deepseek_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
        glm_key=settings.glm_api_key,
        glm_base_url=settings.glm_base_url,
    )
    state_store = StateStore(base_dir=os.path.join(settings.output_dir, "states"))
    ws_manager = WebSocketManager()

    editable_defaults = {
        "default_model": settings.default_model,
        "fallback_model": settings.fallback_model,
        "max_review_iterations": settings.max_review_iterations,
        "code_execution_timeout": settings.code_execution_timeout,
        "default_language": settings.default_language,
        "use_docker_sandbox": settings.use_docker_sandbox,
        "anthropic_api_key": settings.anthropic_api_key,
        "openai_api_key": settings.openai_api_key,
        "deepseek_api_key": settings.deepseek_api_key,
        "glm_api_key": settings.glm_api_key,
    }
    settings_manager = SettingsManager(
        os.path.join(settings.output_dir, "settings.json"),
        defaults=editable_defaults,
    )
    _apply_settings(settings_manager.get_all())

    logger.info("DevAgent Team API started")
    yield
    logger.info("DevAgent Team API shutting down")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    requirement: str


class CreateProjectResponse(BaseModel):
    project_id: str
    state: str


class ProjectStatusResponse(BaseModel):
    project_id: str
    state: str
    agent_statuses: dict
    iteration_count: int
    outputs: dict


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/projects", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Create a new project and start the workflow."""
    project_id = str(uuid.uuid4())[:8]
    state_store.create_project(project_id, request.requirement)
    asyncio.create_task(_run_workflow(project_id, request.requirement))
    return CreateProjectResponse(project_id=project_id, state="planning")


@app.get("/api/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project(project_id: str):
    """Get the current status of a project."""
    project = state_store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectStatusResponse(
        project_id=project.id,
        state=project.state.value,
        agent_statuses=project.agent_statuses,
        iteration_count=project.iteration_count,
        outputs=project.outputs,
    )


@app.get("/api/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """List all files in a project."""
    project = state_store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    return {"files": fm.list_files()}


@app.get("/api/projects/{project_id}/files/{file_path:path}")
async def get_project_file(project_id: str, file_path: str):
    """Get the content of a specific file in a project."""
    project = state_store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    if not fm.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File {file_path} not found")
    return {"content": fm.read_file(file_path)}


@app.get("/api/projects")
async def list_projects():
    """List all projects with metadata for the history view."""
    return {"projects": state_store.list_projects_detailed()}


@app.get("/api/projects/{project_id}/git/log")
async def get_git_log(project_id: str):
    """Return commit history for a project."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    commits = gm.get_log(project_id)
    return {
        "commits": [
            {"hash": c.hash, "message": c.message, "timestamp": c.timestamp}
            for c in commits
        ]
    }


@app.get("/api/projects/{project_id}/git/diff")
async def get_git_diff_working(project_id: str):
    """Return the working-tree diff against HEAD."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    return {"diff": gm.get_diff(project_id)}


@app.get("/api/projects/{project_id}/git/diff/{commit_hash}")
async def get_git_diff_commit(project_id: str, commit_hash: str):
    """Return the diff for a specific commit."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    return {"diff": gm.get_diff(project_id, commit_hash)}


# ---------------------------------------------------------------------------
# Settings Endpoints
# ---------------------------------------------------------------------------

def _apply_settings(values: dict) -> None:
    """Push editable settings into the live config and rebuild the LLM client."""
    global llm_client
    settings.default_model = values["default_model"]
    settings.fallback_model = values["fallback_model"]
    settings.max_review_iterations = values["max_review_iterations"]
    settings.code_execution_timeout = values["code_execution_timeout"]
    settings.default_language = values["default_language"]
    settings.use_docker_sandbox = values["use_docker_sandbox"]
    settings.anthropic_api_key = values["anthropic_api_key"]
    settings.openai_api_key = values["openai_api_key"]
    settings.deepseek_api_key = values["deepseek_api_key"]
    settings.glm_api_key = values["glm_api_key"]
    llm_client = LLMClient(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
        deepseek_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
        glm_key=settings.glm_api_key,
        glm_base_url=settings.glm_base_url,
    )


class UpdateSettingsRequest(BaseModel):
    settings: dict


@app.get("/api/settings")
async def get_settings():
    """Return editable settings with secrets masked."""
    return {"settings": settings_manager.get_masked()}


@app.get("/api/settings/models")
async def get_models():
    """Return available models grouped by provider."""
    return {
        "models": {
            "anthropic": ["claude-3-5-sonnet-20241022"],
            "openai": ["gpt-4o"],
            "deepseek": ["deepseek-v4-pro"],
            "glm": ["glm-4-plus"],
        }
    }


@app.post("/api/settings")
async def update_settings(request: UpdateSettingsRequest):
    """Apply and persist settings changes; rebuild the LLM client."""
    values = settings_manager.update(request.settings)
    _apply_settings(values)
    return {"settings": settings_manager.get_masked()}


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project updates."""
    await ws_manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        await ws_manager.disconnect(project_id)


# ---------------------------------------------------------------------------
# Workflow Execution
# ---------------------------------------------------------------------------

async def _run_workflow(project_id: str, requirement: str):
    """Execute the full agent workflow for a project."""
    scheduler = AgentScheduler(llm_client, ws_manager, state_store)
    sm = StateMachine(max_iterations=settings.max_review_iterations)
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    gm = GitManager(base_dir=settings.output_dir)
    gm.init_repo(project_id)
    await _send_terminal(project_id, "agent", f"Initialized project {project_id}\n")
    context = AgentContext(requirement=requirement, project_id=project_id)
    context.language = settings.default_language

    try:
        # IDLE -> PLANNING
        sm.transition_to(WorkflowState.PLANNING)
        state_store.update_state(project_id, WorkflowState.PLANNING)
        await _notify_workflow_state(project_id, sm)

        pm_output = await scheduler.run_agent("pm", context, project_id)
        context.spec = pm_output.content
        fm.write_file("spec.md", pm_output.content)
        state_store.update_output(project_id, "spec", pm_output.content)
        gm.commit(project_id, "spec: add functional specification")
        await _send_terminal(project_id, "agent", "PM Agent completed: spec.md committed\n")

        # PLANNING -> DESIGNING
        sm.transition_to(WorkflowState.DESIGNING)
        state_store.update_state(project_id, WorkflowState.DESIGNING)
        await _notify_workflow_state(project_id, sm)

        architect_output = await scheduler.run_agent("architect", context, project_id)
        context.architecture = architect_output.content
        fm.write_file("architecture.md", architect_output.content)
        state_store.update_output(project_id, "architecture", architect_output.content)
        gm.commit(project_id, "arch: add system architecture")
        await _send_terminal(project_id, "agent", "Architect Agent completed: architecture.md committed\n")

        # DESIGNING -> CODING (first pass)
        sm.transition_to(WorkflowState.CODING)
        state_store.update_state(project_id, WorkflowState.CODING)
        await _notify_workflow_state(project_id, sm)

        # Review loop
        review_passed = False
        code_runner = CodeRunner(timeout=settings.code_execution_timeout)
        while not review_passed:
            coder_output = await scheduler.run_agent("coder", context, project_id)
            context.code = coder_output.files

            for filepath, content in coder_output.files.items():
                fm.write_file(filepath, content)

            gm.commit(project_id, f"coder: iteration {sm._review_count}")
            await _send_terminal(
                project_id, "agent",
                f"Coder Agent wrote {len(coder_output.files)} file(s)\n",
            )

            # --- Syntax validation before review ---
            syntax_errors = []
            for filepath, content in coder_output.files.items():
                language = code_runner.detect_language(filepath)
                if language:
                    is_valid, error = code_runner.validate_syntax(content, language)
                    if not is_valid:
                        syntax_errors.append(f"{filepath}: {error}")

            if syntax_errors:
                logger.warning("Syntax errors found in iteration %d: %s", sm._review_count, syntax_errors)
                for err in syntax_errors:
                    await _send_terminal(project_id, "stderr", err + "\n")
                if sm.can_iterate():
                    context.review_feedback = (
                        "The generated code has syntax errors. Please fix them before review.\n\n"
                        + "\n".join(syntax_errors)
                    )
                    context.iteration = sm._review_count
                    state_store.increment_iteration(project_id)
                    # Stay in CODING state, skip reviewer for this round
                    await ws_manager.send_message(project_id, {
                        "type": "agent_status",
                        "project_id": project_id,
                        "agent": "coder",
                        "status": "running",
                        "output": {"summary": f"Fixing {len(syntax_errors)} syntax error(s)..."},
                    })
                    continue
                else:
                    # Out of iterations; proceed to reviewer for final assessment
                    pass

            sm.transition_to(WorkflowState.REVIEWING)
            state_store.update_state(project_id, WorkflowState.REVIEWING)
            await _notify_workflow_state(project_id, sm)

            reviewer_output = await scheduler.run_agent("reviewer", context, project_id)
            review_passed = reviewer_output.metadata.get("passed", False)

            fm.write_file("review.md", reviewer_output.content)
            state_store.update_output(project_id, "review", reviewer_output.content)
            gm.commit(project_id, "review: add review report")
            await _send_terminal(project_id, "agent", "Reviewer Agent completed\n")

            if not review_passed and sm.can_iterate():
                context.review_feedback = reviewer_output.content
                context.iteration = sm._review_count
                state_store.increment_iteration(project_id)
                sm.transition_to(WorkflowState.CODING)
                state_store.update_state(project_id, WorkflowState.CODING)
                await _notify_workflow_state(project_id, sm)
            else:
                break

        sm.transition_to(WorkflowState.DONE)
        state_store.update_state(project_id, WorkflowState.DONE)
        await _notify_workflow_state(project_id, sm)

    except Exception as e:
        logger.error("Workflow failed for %s: %s", project_id, e)
        await ws_manager.send_message(project_id, {
            "type": "error",
            "project_id": project_id,
            "message": str(e),
        })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _send_terminal(project_id: str, stream: str, content: str):
    """Send a terminal output line to the frontend."""
    await ws_manager.send_message(project_id, {
        "type": "terminal_output",
        "project_id": project_id,
        "stream": stream,  # "stdout" | "stderr" | "agent"
        "content": content,
    })


async def _notify_workflow_state(project_id: str, sm: StateMachine):
    """Send workflow state update via WebSocket."""
    progress_map = {
        WorkflowState.IDLE: 0,
        WorkflowState.PLANNING: 10,
        WorkflowState.DESIGNING: 30,
        WorkflowState.CODING: 50,
        WorkflowState.REVIEWING: 80,
        WorkflowState.DONE: 100,
    }
    await ws_manager.send_message(project_id, {
        "type": "workflow_state",
        "project_id": project_id,
        "state": sm.current.value,
        "overall_progress": progress_map.get(sm.current, 0),
        "iteration_count": sm._review_count,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["output/*", "**/output/*"],
    )
