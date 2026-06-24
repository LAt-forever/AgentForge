# Web App Artifact Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-class Web App workflow profile that guides static HTML/CSS/JS generation, validates generated artifacts, and exposes a reliable preview action in the UI.

**Architecture:** Add a small workflow profile layer that reuses the existing EventBus and PM -> Architect -> Coder -> Reviewer pipeline. Static web projects use profile-aware prompt context, a WebArtifactValidator after code generation, persisted artifact status, and FastAPI preview routes. The frontend reads the persisted profile/artifact status and shows mode-specific labels, validation problems, and Preview App actions.

**Tech Stack:** Python 3.11, FastAPI, pytest, React 18, TypeScript, Vite, Zustand.

---

## File Structure

Backend files:

- Create `backend/core/workflow_profiles.py`: workflow profile dataclass, profile registry, deterministic profile resolver.
- Modify `backend/agents/base_agent.py`: add `workflow_profile`, `workflow_profile_display`, `workflow_prompt_context`, and `artifact_status` to `AgentContext`.
- Modify `backend/core/state_store.py`: persist `workflow_profile` and `artifact_status`; add update helpers.
- Create `backend/tools/web_artifact_validator.py`: validate static web entry point, local references, safe paths, and basic JavaScript syntax.
- Modify `backend/orchestrator/event_driven_orchestrator.py`: resolve profile at workflow start, inject profile into context, run web validator after Coder output, persist artifact status, broadcast mode/status messages.
- Modify `backend/agents/pm_agent.py`, `backend/agents/architect_agent.py`, `backend/agents/coder_agent.py`, `backend/agents/reviewer_agent.py`: include profile prompt context when present.
- Modify `backend/main.py`: include profile/artifact status in API responses and add preview endpoints.

Backend tests:

- Create `tests/backend/core/test_workflow_profiles.py`.
- Modify `tests/backend/core/test_state_store.py`.
- Create `tests/backend/tools/test_web_artifact_validator.py`.
- Create `tests/backend/test_preview_api.py`.
- Modify `tests/e2e/test_event_driven_workflow_mock.py`.

Frontend files:

- Modify `frontend/src/types/index.ts`: add `WorkflowProfileName`, `ArtifactStatus`, and project/workflow fields.
- Modify `frontend/src/store/useStore.ts`: store and expose current project profile/artifact status through existing `currentProject`.
- Modify `frontend/src/App.tsx`: hydrate project fields and merge artifact validator issues into Problems.
- Modify `frontend/src/components/CompletedView.tsx`: show Web App mode, Preview ready copy, and Preview App button.
- Modify `frontend/src/components/AgentStatusList.tsx`: use profile-aware agent labels.
- Modify `frontend/src/components/OrchestratorView.tsx`: show preview action near editor when `index.html` is selected or artifact is ready.
- Modify `frontend/src/components/LogsPanel.tsx`: no structural change required if Problems receives validator issues, but verify layout handles fileless issues.

Verification:

- Backend focused pytest commands.
- Mock E2E workflow with static web FakeLLM.
- Frontend TypeScript build.

---

### Task 1: Add Workflow Profile Model and State Persistence

**Files:**
- Create: `backend/core/workflow_profiles.py`
- Modify: `backend/agents/base_agent.py`
- Modify: `backend/core/state_store.py`
- Test: `tests/backend/core/test_workflow_profiles.py`
- Test: `tests/backend/core/test_state_store.py`

- [ ] **Step 1: Write workflow profile tests**

Create `tests/backend/core/test_workflow_profiles.py`:

```python
"""Tests for workflow profile resolution."""

from backend.core.workflow_profiles import (
    DEFAULT_PROFILE,
    STATIC_WEB_PROFILE,
    get_workflow_profile,
    resolve_workflow_profile,
)


def test_get_default_profile():
    profile = get_workflow_profile(DEFAULT_PROFILE)
    assert profile.name == "default"
    assert profile.display_name == "Default"
    assert profile.preview_enabled is False


def test_get_static_web_profile():
    profile = get_workflow_profile(STATIC_WEB_PROFILE)
    assert profile.name == "static_web"
    assert profile.display_name == "Web App"
    assert profile.preview_enabled is True
    assert profile.agent_labels["coder"] == "Frontend Build"


def test_unknown_profile_falls_back_to_default():
    assert get_workflow_profile("missing").name == "default"


def test_resolve_static_web_from_english_requirement():
    profile = resolve_workflow_profile("Build a pomodoro timer web page")
    assert profile.name == "static_web"


def test_resolve_static_web_from_chinese_requirement():
    profile = resolve_workflow_profile("做一个颜色调色板网页")
    assert profile.name == "static_web"


def test_resolve_default_for_cli_requirement():
    profile = resolve_workflow_profile("Build a Python CLI greeter")
    assert profile.name == "default"


def test_explicit_profile_override_wins():
    profile = resolve_workflow_profile("Build a Python CLI greeter", explicit="static_web")
    assert profile.name == "static_web"
```

- [ ] **Step 2: Run workflow profile tests and verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_workflow_profiles.py -q
```

Expected: fail during collection with `ModuleNotFoundError: No module named 'backend.core.workflow_profiles'`.

- [ ] **Step 3: Implement workflow profile model**

Create `backend/core/workflow_profiles.py`:

```python
"""Workflow profiles for product-facing generation modes."""

from dataclasses import dataclass, field


DEFAULT_PROFILE = "default"
STATIC_WEB_PROFILE = "static_web"


@dataclass(frozen=True)
class WorkflowProfile:
    """Defines mode-specific labels, prompt context, and validation behavior."""

    name: str
    display_name: str
    agent_labels: dict[str, str]
    prompt_context: str = ""
    validators: list[str] = field(default_factory=list)
    preview_enabled: bool = False


DEFAULT_WORKFLOW_PROFILE = WorkflowProfile(
    name=DEFAULT_PROFILE,
    display_name="Default",
    agent_labels={
        "pm": "PM",
        "architect": "Architect",
        "coder": "Coder",
        "reviewer": "Reviewer",
    },
    prompt_context="",
    validators=[],
    preview_enabled=False,
)


STATIC_WEB_WORKFLOW_PROFILE = WorkflowProfile(
    name=STATIC_WEB_PROFILE,
    display_name="Web App",
    agent_labels={
        "pm": "Product Brief",
        "architect": "Web Structure",
        "coder": "Frontend Build",
        "reviewer": "Web Review",
    },
    prompt_context=(
        "Workflow profile: Static Web App. Treat the user request as a browser-based "
        "static frontend tool. Prefer browser-ready files named index.html, style.css, "
        "and script.js. A single self-contained index.html is acceptable when simpler. "
        "Avoid external runtime dependencies and CDN dependencies. Review the result as "
        "an interactive web page, not as a Python CLI."
    ),
    validators=["web_artifact"],
    preview_enabled=True,
)


_PROFILES = {
    DEFAULT_PROFILE: DEFAULT_WORKFLOW_PROFILE,
    STATIC_WEB_PROFILE: STATIC_WEB_WORKFLOW_PROFILE,
}

_STATIC_WEB_TERMS = (
    "web",
    "page",
    "html",
    "css",
    "javascript",
    "frontend",
    "browser",
    "timer",
    "calculator",
    "palette",
    "dashboard",
    "form",
    "网页",
    "页面",
    "前端",
    "浏览器",
    "计时器",
    "计算器",
    "调色板",
    "表单",
)


def get_workflow_profile(name: str | None) -> WorkflowProfile:
    """Return a profile by name, falling back to the default profile."""
    return _PROFILES.get(name or DEFAULT_PROFILE, DEFAULT_WORKFLOW_PROFILE)


def resolve_workflow_profile(
    requirement: str,
    explicit: str | None = None,
) -> WorkflowProfile:
    """Resolve a workflow profile from explicit input or requirement text."""
    if explicit:
        return get_workflow_profile(explicit)

    lower_requirement = requirement.lower()
    if any(term in lower_requirement for term in _STATIC_WEB_TERMS):
        return STATIC_WEB_WORKFLOW_PROFILE
    return DEFAULT_WORKFLOW_PROFILE
```

- [ ] **Step 4: Run workflow profile tests and verify they pass**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_workflow_profiles.py -q
```

Expected: `7 passed`.

- [ ] **Step 5: Write state store tests for profile and artifact status**

Append to `tests/backend/core/test_state_store.py`:

```python
class TestWorkflowProfilePersistence:
    """Test workflow profile and artifact status persistence."""

    def test_create_project_defaults_to_profile_and_empty_artifact_status(self, state_store):
        project = state_store.create_project("web_1", "build a web timer")

        assert project.workflow_profile == "default"
        assert project.artifact_status["type"] == "none"
        assert project.artifact_status["status"] == "unknown"
        assert project.artifact_status["preview_url"] == ""
        assert project.artifact_status["issues"] == []

    def test_update_workflow_profile(self, state_store):
        state_store.create_project("web_1")
        state_store.update_workflow_profile("web_1", "static_web")

        project = state_store.get_project("web_1")
        assert project.workflow_profile == "static_web"

    def test_update_artifact_status(self, state_store):
        state_store.create_project("web_1")
        status = {
            "type": "static_web",
            "status": "ready",
            "preview_url": "/api/projects/web_1/preview/",
            "issues": [],
        }

        state_store.update_artifact_status("web_1", status)

        project = state_store.get_project("web_1")
        assert project.artifact_status == status

    def test_profile_and_artifact_status_persist_across_instances(self, temp_dir):
        store1 = StateStore(base_dir=temp_dir)
        store1.create_project("web_1", "build a web app")
        store1.update_workflow_profile("web_1", "static_web")
        store1.update_artifact_status(
            "web_1",
            {
                "type": "static_web",
                "status": "ready",
                "preview_url": "/api/projects/web_1/preview/",
                "issues": [],
            },
        )

        store2 = StateStore(base_dir=temp_dir)
        project = store2.get_project("web_1")

        assert project.workflow_profile == "static_web"
        assert project.artifact_status["status"] == "ready"
```

- [ ] **Step 6: Run state store tests and verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_state_store.py -q
```

Expected: fail with `AttributeError: 'ProjectState' object has no attribute 'workflow_profile'`.

- [ ] **Step 7: Add workflow fields to AgentContext and ProjectState**

Modify `backend/agents/base_agent.py` by adding fields to `AgentContext`:

```python
    workflow_profile: str = "default"
    workflow_profile_display: str = "Default"
    workflow_prompt_context: str = ""
    artifact_status: dict = field(default_factory=lambda: {
        "type": "none",
        "status": "unknown",
        "preview_url": "",
        "issues": [],
    })
```

Modify `backend/core/state_store.py` by adding the same persisted fields to `ProjectState`:

```python
    workflow_profile: str = "default"
    artifact_status: dict = field(default_factory=lambda: {
        "type": "none",
        "status": "unknown",
        "preview_url": "",
        "issues": [],
    })
```

In `ProjectState.to_dict()`, include:

```python
            "workflow_profile": self.workflow_profile,
            "artifact_status": self.artifact_status,
```

In `ProjectState.from_dict()`, include:

```python
            workflow_profile=data.get("workflow_profile", "default"),
            artifact_status=data.get(
                "artifact_status",
                {
                    "type": "none",
                    "status": "unknown",
                    "preview_url": "",
                    "issues": [],
                },
            ),
```

Add methods to `StateStore`:

```python
    def update_workflow_profile(self, project_id: str, profile: str) -> None:
        """Update the workflow profile for a project."""
        project = self._cache[project_id]
        project.workflow_profile = profile
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)

    def update_artifact_status(self, project_id: str, status: dict) -> None:
        """Update static artifact status for a project."""
        project = self._cache[project_id]
        project.artifact_status = status
        project.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(project_id)
```

In `list_projects_detailed()`, include:

```python
                    "workflow_profile": project.workflow_profile,
                    "artifact_status": project.artifact_status,
```

- [ ] **Step 8: Run backend profile/state tests**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_workflow_profiles.py tests/backend/core/test_state_store.py -q
```

Expected: all tests pass.

- [ ] **Step 9: Commit Task 1**

Run:

```bash
git add backend/core/workflow_profiles.py backend/agents/base_agent.py backend/core/state_store.py tests/backend/core/test_workflow_profiles.py tests/backend/core/test_state_store.py
git commit -m "feat: add workflow profile state"
```

Expected: commit succeeds.

---

### Task 2: Add WebArtifactValidator

**Files:**
- Create: `backend/tools/web_artifact_validator.py`
- Test: `tests/backend/tools/test_web_artifact_validator.py`

- [ ] **Step 1: Write validator tests**

Create `tests/backend/tools/test_web_artifact_validator.py`:

```python
"""Tests for static web artifact validation."""

from backend.tools.file_manager import FileManager
from backend.tools.web_artifact_validator import WebArtifactValidator


def _write_app(tmp_path, files):
    fm = FileManager(str(tmp_path))
    for path, content in files.items():
        fm.write_file(path, content)
    return fm


def test_three_file_static_app_passes(tmp_path):
    fm = _write_app(
        tmp_path,
        {
            "index.html": '<link rel="stylesheet" href="style.css"><script src="script.js"></script>',
            "style.css": "body { color: black; }",
            "script.js": "const app = document.body;",
        },
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "ready"
    assert result["preview_url"] == ""
    assert result["issues"] == []


def test_single_file_index_html_passes(tmp_path):
    fm = _write_app(
        tmp_path,
        {
            "index.html": "<html><style>body{}</style><script>const x = 1;</script></html>",
        },
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "ready"
    assert result["issues"] == []


def test_missing_index_html_fails(tmp_path):
    fm = _write_app(tmp_path, {"script.js": "const x = 1;"})

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "missing_entry"
    assert result["issues"][0]["code"] == "missing_entry"
    assert result["issues"][0]["repairable"] is True


def test_missing_referenced_script_fails(tmp_path):
    fm = _write_app(
        tmp_path,
        {"index.html": '<script src="script.js"></script>'},
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "invalid_refs"
    assert result["issues"][0]["code"] == "missing_ref"
    assert result["issues"][0]["file"] == "index.html"


def test_external_references_are_ignored(tmp_path):
    fm = _write_app(
        tmp_path,
        {"index.html": '<script src="https://example.com/app.js"></script>'},
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "ready"


def test_path_traversal_reference_fails(tmp_path):
    fm = _write_app(
        tmp_path,
        {"index.html": '<script src="../secret.js"></script>'},
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "unsafe_path"
    assert result["issues"][0]["code"] == "unsafe_ref"


def test_absolute_filesystem_reference_fails(tmp_path):
    fm = _write_app(
        tmp_path,
        {"index.html": '<link rel="stylesheet" href="/etc/passwd">'},
    )

    result = WebArtifactValidator(fm).validate()

    assert result["status"] == "unsafe_path"
    assert result["issues"][0]["code"] == "unsafe_ref"
```

- [ ] **Step 2: Run validator tests and verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/backend/tools/test_web_artifact_validator.py -q
```

Expected: fail during collection with `ModuleNotFoundError: No module named 'backend.tools.web_artifact_validator'`.

- [ ] **Step 3: Implement validator**

Create `backend/tools/web_artifact_validator.py`:

```python
"""Validation for generated static web artifacts."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from backend.tools.file_manager import FileManager


_SCRIPT_SRC = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_STYLESHEET_HREF = re.compile(
    r"<link[^>]+rel=[\"']stylesheet[\"'][^>]+href=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)


def _issue(code: str, message: str, *, file: str = "", severity: str = "error") -> dict:
    return {
        "severity": severity,
        "code": code,
        "file": file,
        "message": message,
        "repairable": True,
    }


class WebArtifactValidator:
    """Validates static browser artifacts in a project directory."""

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def validate(self) -> dict:
        """Return artifact status for a generated static web app."""
        if not self.file_manager.exists("index.html"):
            return self._result(
                "missing_entry",
                [_issue(
                    "missing_entry",
                    "Static web app requires an index.html entry point.",
                    file="index.html",
                )],
            )

        html = self.file_manager.read_file("index.html")
        issues = []
        for ref in self._local_refs(html):
            if self._is_unsafe_ref(ref):
                issues.append(_issue(
                    "unsafe_ref",
                    f"Reference '{ref}' is not allowed in static preview.",
                    file="index.html",
                ))
                continue
            if not self.file_manager.exists(ref):
                issues.append(_issue(
                    "missing_ref",
                    f"index.html references missing file '{ref}'.",
                    file="index.html",
                ))

        if issues:
            status = "unsafe_path" if any(i["code"] == "unsafe_ref" for i in issues) else "invalid_refs"
            return self._result(status, issues)

        return self._result("ready", [])

    def _local_refs(self, html: str) -> list[str]:
        refs = []
        refs.extend(_SCRIPT_SRC.findall(html))
        refs.extend(_STYLESHEET_HREF.findall(html))
        return [ref for ref in refs if self._is_local_ref(ref)]

    def _is_local_ref(self, ref: str) -> bool:
        parsed = urlparse(ref)
        if parsed.scheme or parsed.netloc:
            return False
        if ref.startswith("#") or ref.startswith("data:") or ref.startswith("mailto:"):
            return False
        return True

    def _is_unsafe_ref(self, ref: str) -> bool:
        normalized = ref.replace("\\", "/")
        return normalized.startswith("/") or ".." in normalized.split("/")

    def _result(self, status: str, issues: list[dict]) -> dict:
        return {
            "type": "static_web",
            "status": status,
            "preview_url": "",
            "issues": issues,
        }
```

- [ ] **Step 4: Run validator tests**

Run:

```bash
.venv/bin/python -m pytest tests/backend/tools/test_web_artifact_validator.py -q
```

Expected: all validator tests pass.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add backend/tools/web_artifact_validator.py tests/backend/tools/test_web_artifact_validator.py
git commit -m "feat: validate static web artifacts"
```

Expected: commit succeeds.

---

### Task 3: Integrate Profile and Validator into Orchestrator

**Files:**
- Modify: `backend/orchestrator/event_driven_orchestrator.py`
- Modify: `backend/agents/pm_agent.py`
- Modify: `backend/agents/architect_agent.py`
- Modify: `backend/agents/coder_agent.py`
- Modify: `backend/agents/reviewer_agent.py`
- Test: `tests/e2e/test_event_driven_workflow_mock.py`

- [ ] **Step 1: Add static web mock E2E test**

Append to `tests/e2e/test_event_driven_workflow_mock.py`:

```python
class StaticWebFakeLLMClient(LLMClient):
    """Fake LLM that returns a valid static web artifact."""

    def __init__(self):
        pass

    async def call(self, prompt, config):
        from backend.llm.models import LLMResponse

        sys = config.system_prompt.lower()
        prompt_text = prompt.lower()
        if "product manager" in sys:
            assert "static web app" in prompt_text
            return LLMResponse(content="# Web Spec\n\nBuild an interactive timer page.", model="mock")
        if "system architect" in sys or ("architect" in sys and "developer" not in sys):
            assert "index.html" in prompt_text
            return LLMResponse(content="# Web Architecture\n\nFiles: index.html, style.css, script.js", model="mock")
        if "software developer" in sys or "developer" in sys:
            assert "index.html" in prompt_text
            return LLMResponse(content="""### FILE: index.html
```html
<!doctype html>
<html>
  <head>
    <link rel="stylesheet" href="style.css">
  </head>
  <body>
    <button id="start">Start</button>
    <script src="script.js"></script>
  </body>
</html>
```

### FILE: style.css
```css
body { font-family: sans-serif; }
```

### FILE: script.js
```javascript
document.getElementById("start").addEventListener("click", () => {
  document.body.dataset.started = "true";
});
```
""", model="mock")
        if "code reviewer" in sys or "reviewer" in sys:
            assert "static web app" in prompt_text
            return LLMResponse(content='{"passed": true, "issues": [], "summary": "Web app looks good"}', model="mock")
        return LLMResponse(content="OK", model="mock")


@pytest.mark.asyncio
async def test_static_web_workflow_profile_completes(tmp_path_factory):
    """Static web workflow resolves profile, validates artifact, and exposes preview metadata."""
    output_dir = str(tmp_path_factory.mktemp("static_web_output"))
    app_settings.output_dir = output_dir
    app_settings.use_docker_sandbox = False

    llm_client = StaticWebFakeLLMClient()
    state_store = StateStore(base_dir=os.path.join(output_dir, "states"))
    ws_manager = WebSocketManager()
    event_bus = EventBus()
    plugin_registry = PluginRegistry()
    register_built_in_plugins(plugin_registry, llm_client)
    orchestrator = EventDrivenOrchestrator(event_bus, plugin_registry, ws_manager, state_store)

    project_id = "mock-web-001"
    completion_event = asyncio.Event()

    async def on_complete(event):
        if event.project_id == project_id:
            completion_event.set()

    event_bus.subscribe(EventType.WORKFLOW_COMPLETED, on_complete)
    await orchestrator.start_workflow(project_id, "做一个番茄钟网页工具")

    await asyncio.wait([asyncio.create_task(completion_event.wait())], timeout=30)

    project = state_store.get_project(project_id)
    assert project.state == WorkflowState.DONE
    assert project.workflow_profile == "static_web"
    assert project.artifact_status["status"] == "ready"
    assert project.artifact_status["preview_url"] == f"/api/projects/{project_id}/preview/"

    fm = FileManager(base_dir=os.path.join(output_dir, project_id))
    assert fm.exists("index.html")
    assert fm.exists("style.css")
    assert fm.exists("script.js")

    shutil.rmtree(output_dir, ignore_errors=True)
```

- [ ] **Step 2: Run static web E2E test and verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/e2e/test_event_driven_workflow_mock.py::test_static_web_workflow_profile_completes -q
```

Expected: fail because workflow profile stays `default` or `artifact_status.status` remains `unknown`.

- [ ] **Step 3: Inject profile into orchestrator workflow start and restore**

Modify imports in `backend/orchestrator/event_driven_orchestrator.py`:

```python
from backend.core.workflow_profiles import resolve_workflow_profile, get_workflow_profile
from backend.tools.web_artifact_validator import WebArtifactValidator
```

In `start_workflow()`, after creating `AgentContext`, add:

```python
        profile = resolve_workflow_profile(requirement)
        context.workflow_profile = profile.name
        context.workflow_profile_display = profile.display_name
        context.workflow_prompt_context = profile.prompt_context
        self.state_store.update_workflow_profile(project_id, profile.name)
```

After sending initialized terminal line, add:

```python
        await self._send_terminal(
            project_id,
            "agent",
            f"Detected workflow profile: {profile.display_name}\n",
        )
```

In `_restore_context()`, after setting language, add:

```python
        profile = get_workflow_profile(getattr(project, "workflow_profile", "default") if project else "default")
        context.workflow_profile = profile.name
        context.workflow_profile_display = profile.display_name
        context.workflow_prompt_context = profile.prompt_context
        context.artifact_status = project.artifact_status if project else context.artifact_status
```

- [ ] **Step 4: Run static web E2E and verify prompt assertions fail**

Run:

```bash
.venv/bin/python -m pytest tests/e2e/test_event_driven_workflow_mock.py::test_static_web_workflow_profile_completes -q
```

Expected: fail at FakeLLM assertion because agent prompts do not yet include static web context.

- [ ] **Step 5: Add workflow prompt context to agents**

In each agent `run()` method, add `context.workflow_prompt_context` when present.

For `backend/agents/pm_agent.py`, before requirement:

```python
        user_prompt_parts = []
        if context.workflow_prompt_context:
            user_prompt_parts.append(context.workflow_prompt_context)
        user_prompt_parts.append(f"User Requirement:\n{context.requirement}")
        user_prompt = "\n\n".join(user_prompt_parts)
```

For `backend/agents/architect_agent.py`, include profile context before spec:

```python
        user_prompt_parts = []
        if context.workflow_prompt_context:
            user_prompt_parts.append(context.workflow_prompt_context)
        user_prompt_parts.append(f"Functional Specification:\n{context.spec}")
        user_prompt = "\n\n".join(user_prompt_parts)
```

For `backend/agents/coder_agent.py`, add after the target language line:

```python
        if context.workflow_prompt_context:
            user_prompt_parts.append(context.workflow_prompt_context)
```

For `backend/agents/reviewer_agent.py`, add profile context to `user_prompt` before the functional specification:

```python
        profile_section = (
            f"{context.workflow_prompt_context}\n\n"
            if context.workflow_prompt_context else ""
        )
        user_prompt = (
            f"{profile_section}"
            f"Functional Specification:\n{context.spec}\n\n"
            f"Architecture:\n{context.architecture}\n\n"
            f"Code Files:\n{code_text}"
            f"{analysis_section}\n\n"
            f"Important: Code files ARE provided above. Do NOT say 'no code files provided'. "
            f"Review the actual code for completeness, correctness, and quality."
        )
```

- [ ] **Step 6: Add web artifact validation in `_syntax_check`**

In `EventDrivenOrchestrator._syntax_check()`, after regular syntax error handling and before returning `SYNTAX_CHECKED`, add:

```python
        if context.workflow_profile == "static_web":
            await self._send_terminal(project_id, "agent", "Validating static web artifact\n")
            fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
            artifact_status = WebArtifactValidator(fm).validate()
            if artifact_status["status"] == "ready":
                artifact_status["preview_url"] = f"/api/projects/{project_id}/preview/"
                await self._send_terminal(
                    project_id,
                    "agent",
                    f"Preview ready: {artifact_status['preview_url']}\n",
                )
            else:
                await self._send_terminal(
                    project_id,
                    "stderr",
                    f"Preview unavailable: {artifact_status['status']}\n",
                )
            context.artifact_status = artifact_status
            self.state_store.update_artifact_status(project_id, artifact_status)

            repairable_issues = [
                issue for issue in artifact_status.get("issues", [])
                if issue.get("repairable", False)
            ]
            if repairable_issues and sm.can_iterate():
                feedback_lines = [
                    f"{issue.get('file', '')}: {issue.get('message', '')}".strip(": ")
                    for issue in repairable_issues
                ]
                context.review_feedback = (
                    "The generated static web artifact is not preview-ready. "
                    "Fix these issues:\n\n" + "\n".join(feedback_lines)
                )
                context.iteration = sm._review_count
                self.state_store.increment_iteration(project_id)
                return Event(
                    type=EventType.ITERATION_STARTED,
                    project_id=project_id,
                    payload={"reason": "web_artifact_validation", "issues": repairable_issues},
                )
```

- [ ] **Step 7: Include profile and artifact status in workflow state websocket messages**

In `_notify_workflow_state()`, fetch the project and include fields:

```python
        project = self.state_store.get_project(project_id)
```

Add keys to the message:

```python
            "workflow_profile": project.workflow_profile if project else "default",
            "artifact_status": project.artifact_status if project else {
                "type": "none",
                "status": "unknown",
                "preview_url": "",
                "issues": [],
            },
```

- [ ] **Step 8: Run static web and existing mock E2E tests**

Run:

```bash
.venv/bin/python -m pytest tests/e2e/test_event_driven_workflow_mock.py -q
```

Expected: all mock E2E tests pass.

- [ ] **Step 9: Commit Task 3**

Run:

```bash
git add backend/orchestrator/event_driven_orchestrator.py backend/agents/pm_agent.py backend/agents/architect_agent.py backend/agents/coder_agent.py backend/agents/reviewer_agent.py tests/e2e/test_event_driven_workflow_mock.py
git commit -m "feat: run static web workflow profile"
```

Expected: commit succeeds.

---

### Task 4: Add Preview API

**Files:**
- Modify: `backend/main.py`
- Test: `tests/backend/test_preview_api.py`

- [ ] **Step 1: Write preview API tests**

Create `tests/backend/test_preview_api.py`:

```python
"""Tests for generated project preview routes."""

import os

from fastapi.testclient import TestClient

from backend.config import settings
from backend.core.state_store import StateStore
from backend.main import app
from backend.tools.file_manager import FileManager


def _make_client(tmp_path, monkeypatch):
    import backend.main as main

    output_dir = str(tmp_path)
    settings.output_dir = output_dir
    main.state_store = StateStore(base_dir=os.path.join(output_dir, "states"))
    return TestClient(app), main.state_store, output_dir


def _create_web_project(state_store, output_dir, project_id="web1"):
    state_store.create_project(project_id, "build a web app")
    state_store.update_workflow_profile(project_id, "static_web")
    state_store.update_artifact_status(
        project_id,
        {
            "type": "static_web",
            "status": "ready",
            "preview_url": f"/api/projects/{project_id}/preview/",
            "issues": [],
        },
    )
    fm = FileManager(base_dir=os.path.join(output_dir, project_id))
    fm.write_file("index.html", '<link rel="stylesheet" href="style.css">')
    fm.write_file("style.css", "body { color: black; }")
    return fm


def test_preview_index_returns_html(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "style.css" in response.text


def test_preview_static_asset_returns_css(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/style.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert response.text == "body { color: black; }"


def test_preview_missing_asset_returns_404(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/missing.js")

    assert response.status_code == 404
    assert response.json()["detail"] == "Preview file missing.js not found"


def test_preview_blocks_path_traversal(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/../states/web1.json")

    assert response.status_code in (403, 404)


def test_preview_blocks_dotfiles(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    fm = _create_web_project(state_store, output_dir)
    fm.write_file(".secret", "hidden")

    response = client.get("/api/projects/web1/preview/.secret")

    assert response.status_code == 403


def test_preview_not_ready_returns_409(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    state_store.create_project("cli1", "build a cli")

    response = client.get("/api/projects/cli1/preview/")

    assert response.status_code == 409
    assert response.json()["detail"] == "Project cli1 is not preview-ready"
```

- [ ] **Step 2: Run preview API tests and verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/backend/test_preview_api.py -q
```

Expected: fail with `404 Not Found` for preview routes.

- [ ] **Step 3: Add API response fields**

In `backend/main.py`, modify `CreateProjectRequest`:

```python
class CreateProjectRequest(BaseModel):
    requirement: str
    workflow_profile: str | None = None
```

Modify `ProjectStatusResponse`:

```python
class ProjectStatusResponse(BaseModel):
    project_id: str
    state: str
    agent_statuses: dict
    iteration_count: int
    outputs: dict
    workflow_profile: str
    artifact_status: dict
```

In `get_project()`, include:

```python
        workflow_profile=project.workflow_profile,
        artifact_status=project.artifact_status,
```

In `list_projects_detailed()`, Task 1 already adds fields.

- [ ] **Step 4: Add preview helpers and routes**

In `backend/main.py`, add imports:

```python
from pathlib import Path
from fastapi.responses import FileResponse
```

Add helper functions before REST endpoints:

```python
_PREVIEW_MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".txt": "text/plain",
}


def _preview_file_response(project_id: str, file_path: str) -> FileResponse:
    project = state_store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    if project.artifact_status.get("status") != "ready":
        raise HTTPException(status_code=409, detail=f"Project {project_id} is not preview-ready")

    normalized = file_path or "index.html"
    path_parts = Path(normalized).parts
    if any(part.startswith(".") for part in path_parts) or ".." in path_parts:
        raise HTTPException(status_code=403, detail=f"Preview file {normalized} is not allowed")

    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    try:
        abs_path = fm.get_absolute_path(normalized)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Preview file {normalized} is not allowed") from None

    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail=f"Preview file {normalized} not found")

    suffix = Path(abs_path).suffix.lower()
    media_type = _PREVIEW_MIME_TYPES.get(suffix)
    if media_type is None:
        raise HTTPException(status_code=403, detail=f"Preview file {normalized} type is not allowed")
    return FileResponse(abs_path, media_type=media_type)
```

Add routes after file endpoints:

```python
@app.get("/api/projects/{project_id}/preview/")
async def preview_project_index(project_id: str):
    """Serve the preview entry point for a generated static web app."""
    return _preview_file_response(project_id, "index.html")


@app.get("/api/projects/{project_id}/preview/{file_path:path}")
async def preview_project_file(project_id: str, file_path: str):
    """Serve a safe static asset for a generated static web app."""
    return _preview_file_response(project_id, file_path)
```

- [ ] **Step 5: Run preview API tests**

Run:

```bash
.venv/bin/python -m pytest tests/backend/test_preview_api.py -q
```

Expected: all preview API tests pass.

- [ ] **Step 6: Run focused backend regression tests**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_state_store.py tests/backend/tools/test_web_artifact_validator.py tests/backend/test_preview_api.py tests/e2e/test_event_driven_workflow_mock.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 7: Commit Task 4**

Run:

```bash
git add backend/main.py tests/backend/test_preview_api.py
git commit -m "feat: serve generated web app previews"
```

Expected: commit succeeds.

---

### Task 5: Add Frontend Types, Hydration, and Problems Integration

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/store/useStore.ts`

- [ ] **Step 1: Add frontend type definitions**

Modify `frontend/src/types/index.ts`:

```typescript
export type WorkflowProfileName = 'default' | 'static_web';

export interface ArtifactIssue {
  severity: string;
  code?: string;
  file?: string;
  line?: number;
  message: string;
  repairable?: boolean;
}

export interface ArtifactStatus {
  type: string;
  status:
    | 'unknown'
    | 'not_web_artifact'
    | 'validating'
    | 'ready'
    | 'missing_entry'
    | 'invalid_refs'
    | 'syntax_error'
    | 'unsafe_path'
    | 'error';
  preview_url: string;
  issues: ArtifactIssue[];
}
```

Update `WorkflowState`:

```typescript
  workflow_profile?: WorkflowProfileName;
  artifact_status?: ArtifactStatus;
```

Update `Project`:

```typescript
  workflow_profile: WorkflowProfileName;
  artifact_status: ArtifactStatus;
```

Update `ProjectSummary`:

```typescript
  workflow_profile?: WorkflowProfileName;
  artifact_status?: ArtifactStatus;
```

- [ ] **Step 2: Add default artifact status helper**

In `frontend/src/App.tsx`, add near imports:

```typescript
import type { ArtifactStatus, WorkflowProfileName } from './types';

const DEFAULT_ARTIFACT_STATUS: ArtifactStatus = {
  type: 'none',
  status: 'unknown',
  preview_url: '',
  issues: [],
};

function normalizeArtifactStatus(raw: unknown): ArtifactStatus {
  const value = raw as Partial<ArtifactStatus> | undefined;
  return {
    type: value?.type ?? 'none',
    status: value?.status ?? 'unknown',
    preview_url: value?.preview_url ?? '',
    issues: Array.isArray(value?.issues) ? value.issues : [],
  };
}

function normalizeWorkflowProfile(raw: unknown): WorkflowProfileName {
  return raw === 'static_web' ? 'static_web' : 'default';
}
```

- [ ] **Step 3: Hydrate new fields when creating and loading projects**

In `handleSubmit()`, update `setProject`:

```typescript
        setProject({
          project_id: data.project_id,
          state: data.state,
          agent_statuses: {},
          iteration_count: 0,
          outputs: {},
          workflow_profile: 'default',
          artifact_status: DEFAULT_ARTIFACT_STATUS,
        });
```

In both project fetch hydration blocks, update `setProject`:

```typescript
          const artifactStatus = normalizeArtifactStatus(data.artifact_status);
          setProject({
            project_id: data.project_id,
            state: data.state,
            agent_statuses: data.agent_statuses || {},
            iteration_count: data.iteration_count || 0,
            outputs: data.outputs || {},
            workflow_profile: normalizeWorkflowProfile(data.workflow_profile),
            artifact_status: artifactStatus,
          });
```

- [ ] **Step 4: Merge reviewer and artifact issues into Problems**

Replace the existing reviewer-only parsing effect in `frontend/src/App.tsx` with:

```typescript
  useEffect(() => {
    const nextProblems = [];
    const raw = currentProject?.outputs?.reviewer;
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as {
          issues?: Array<{ severity: string; file?: string; line?: number; message: string }>;
        };
        if (Array.isArray(parsed.issues)) {
          nextProblems.push(
            ...parsed.issues.map((it) => ({
              severity: it.severity ?? 'warning',
              file: it.file ?? '',
              line: it.line,
              message: it.message,
            }))
          );
        }
      } catch {
        // Reviewer output not valid JSON - ignore.
      }
    }

    const artifactIssues = currentProject?.artifact_status?.issues ?? [];
    nextProblems.push(
      ...artifactIssues.map((it) => ({
        severity: it.severity ?? 'error',
        file: it.file ?? '',
        line: it.line,
        message: it.message,
      }))
    );

    setProblems(nextProblems);
  }, [currentProject?.outputs?.reviewer, currentProject?.artifact_status, setProblems]);
```

- [ ] **Step 5: Handle websocket workflow fields**

In `frontend/src/hooks/useWebSocket.ts`, extend `setWorkflowState` payload:

```typescript
            workflow_profile: message.workflow_profile as 'default' | 'static_web' | undefined,
            artifact_status: message.artifact_status as ArtifactStatus | undefined,
```

Add import:

```typescript
import type { ArtifactStatus, WebSocketMessage } from '../types';
```

- [ ] **Step 6: Run TypeScript and fix any type errors**

Run:

```bash
cd frontend
./node_modules/.bin/tsc --noEmit
```

Expected: type errors appear if a `Project` object is missing new fields. Fix each missing object by adding `workflow_profile: 'default'` and `artifact_status: DEFAULT_ARTIFACT_STATUS` or normalized backend values. Re-run until the command exits 0.

- [ ] **Step 7: Commit Task 5**

Run:

```bash
git add frontend/src/types/index.ts frontend/src/App.tsx frontend/src/hooks/useWebSocket.ts frontend/src/store/useStore.ts
git commit -m "feat: hydrate web artifact status in UI"
```

Expected: commit succeeds.

---

### Task 6: Add Web App Mode UI and Preview Actions

**Files:**
- Modify: `frontend/src/components/CompletedView.tsx`
- Modify: `frontend/src/components/AgentStatusList.tsx`
- Modify: `frontend/src/components/OrchestratorView.tsx`

- [ ] **Step 1: Add helper labels in `CompletedView`**

In `frontend/src/components/CompletedView.tsx`, read profile and artifact status:

```typescript
  const currentProject = useStore((s) => s.currentProject);
  const isWebApp = currentProject?.workflow_profile === 'static_web';
  const artifactStatus = currentProject?.artifact_status;
  const previewReady = artifactStatus?.status === 'ready' && Boolean(artifactStatus.preview_url);
```

Add preview function:

```typescript
  const previewApp = () => {
    if (artifactStatus?.preview_url) {
      window.open(artifactStatus.preview_url, '_blank');
    }
  };
```

Replace success copy:

```typescript
            {isWebApp && previewReady ? '✓ Preview ready' : '✓ Workflow complete'}
```

Replace secondary copy:

```typescript
            {isWebApp && previewReady
              ? `Static web app validated. Generated ${fileCount} file${fileCount === 1 ? '' : 's'}.`
              : `Generated ${fileCount} file${fileCount === 1 ? '' : 's'}. Review finished.`}
```

Add a mode stat:

```typescript
            <Stat label="Mode" value={isWebApp ? 'Web App' : 'Default'} />
```

Add Preview App button above Open in Editor:

```tsx
          {isWebApp && (
            <ActionButton primary={previewReady} onClick={previewApp} disabled={!previewReady}>
              ◉ Preview App
            </ActionButton>
          )}
```

Update `ActionButton` props to include `disabled?: boolean` and styles:

```typescript
const ActionButton: React.FC<{
  children: React.ReactNode;
  onClick: () => void;
  primary?: boolean;
  disabled?: boolean;
}> = ({ children, onClick, primary, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      width: '100%',
      padding: '10px',
      borderRadius: '6px',
      border: primary ? 'none' : '1px solid var(--border-color)',
      background: disabled ? 'var(--bg-tertiary)' : primary ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
      color: disabled ? 'var(--text-muted)' : primary ? '#fff' : 'var(--text-primary)',
      fontSize: '13px',
      fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer',
    }}
  >
    {children}
  </button>
);
```

- [ ] **Step 2: Make agent labels profile-aware**

In `frontend/src/components/AgentStatusList.tsx`, add:

```typescript
const WEB_AGENT_LABELS: Record<string, string> = {
  pm: 'Product Brief',
  architect: 'Web Structure',
  coder: 'Frontend Build',
  reviewer: 'Web Review',
};
```

In `AgentStatusList`, read:

```typescript
  const currentProject = useStore((s) => s.currentProject);
  const isWebApp = currentProject?.workflow_profile === 'static_web';
```

When rendering `AgentRow`, pass adjusted meta:

```typescript
        {AGENTS.map((meta) => (
          <AgentRow
            key={meta.key}
            meta={isWebApp ? { ...meta, label: WEB_AGENT_LABELS[meta.key] ?? meta.label } : meta}
            status={agentStatuses[meta.key]}
          />
        ))}
```

Change header text:

```typescript
        {isWebApp ? 'Web App Agents' : 'Agents'}
```

- [ ] **Step 3: Add preview button to editor toolbar**

In `frontend/src/components/OrchestratorView.tsx`, read current project:

```typescript
  const currentProject = useStore((s) => s.currentProject);
  const previewUrl = currentProject?.artifact_status?.preview_url;
  const canPreview = currentProject?.artifact_status?.status === 'ready' && Boolean(previewUrl);
```

Add function:

```typescript
  const openPreview = () => {
    if (previewUrl) window.open(previewUrl, '_blank');
  };
```

In the toolbar where `View Diff` is rendered, add a Preview button before View Diff:

```tsx
            {(currentFile === 'index.html' || canPreview) && (
              <button
                onClick={openPreview}
                disabled={!canPreview}
                style={{
                  fontSize: '11px',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: canPreview ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                  color: canPreview ? '#fff' : 'var(--text-muted)',
                  cursor: canPreview ? 'pointer' : 'not-allowed',
                }}
              >
                Preview
              </button>
            )}
```

- [ ] **Step 4: Run TypeScript build**

Run:

```bash
cd frontend
./node_modules/.bin/tsc --noEmit
```

Expected: exits 0.

- [ ] **Step 5: Commit Task 6**

Run:

```bash
git add frontend/src/components/CompletedView.tsx frontend/src/components/AgentStatusList.tsx frontend/src/components/OrchestratorView.tsx
git commit -m "feat: show web app preview actions"
```

Expected: commit succeeds.

---

### Task 7: Final Verification and Documentation Touch-Up

**Files:**
- Modify: `README.md` if it lacks any mention of Web App Mode and preview.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
.venv/bin/python -m pytest tests/backend/core/test_workflow_profiles.py tests/backend/core/test_state_store.py tests/backend/tools/test_web_artifact_validator.py tests/backend/test_preview_api.py tests/e2e/test_event_driven_workflow_mock.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run broader backend tests if time allows**

Run:

```bash
.venv/bin/python -m pytest tests/backend -q
```

Expected: all backend tests pass. If a Docker integration test fails because Docker is unavailable, record the exact failing test and continue with the focused backend set as the required gate.

- [ ] **Step 3: Run frontend TypeScript check**

Run:

```bash
cd frontend
./node_modules/.bin/tsc --noEmit
```

Expected: exits 0.

- [ ] **Step 4: Smoke running services manually**

If services are already running, use them. If not, start backend:

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start frontend in another terminal:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Check backend API:

```bash
curl -s http://127.0.0.1:5173/api/projects
```

Expected: JSON with a `projects` array.

- [ ] **Step 5: Add README note**

If `README.md` does not yet mention Web App Mode, add a short section under Features:

```markdown
### 🌐 Web App Preview Mode
- Automatically detects small static frontend tool requests.
- Guides agents to produce preview-ready `index.html`, `style.css`, and `script.js` artifacts.
- Validates local static references and exposes a `Preview App` action when the artifact is ready.
```

- [ ] **Step 6: Commit final docs if README changed**

Run only if README changed:

```bash
git add README.md
git commit -m "docs: document web app preview mode"
```

Expected: commit succeeds.

- [ ] **Step 7: Final status check**

Run:

```bash
git status --short
```

Expected: only intentional untracked local runtime directories remain, such as `.vscode/` and `output/`, unless the user has added other unrelated files.

---

## Self-Review Checklist

- Spec coverage:
  - Workflow profile: Task 1 and Task 3.
  - Profile-aware prompts: Task 3.
  - WebArtifactValidator: Task 2 and Task 3.
  - Preview API: Task 4.
  - UI mode signal and preview actions: Task 5 and Task 6.
  - Validator issues in Problems: Task 5.
  - Tests and demo gates: Task 1 through Task 7.
- Scope boundaries:
  - No separate WebOrchestrator.
  - No required Playwright.
  - No React/Vite app generation.
  - New-tab preview is the primary v1 behavior.
- Type consistency:
  - Backend uses `workflow_profile` and `artifact_status`.
  - Frontend uses `workflow_profile` and `artifact_status`.
  - Artifact status shape uses `type`, `status`, `preview_url`, and `issues`.
