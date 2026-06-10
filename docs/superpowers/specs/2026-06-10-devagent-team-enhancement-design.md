# DevAgent Team Enhancement Design

## Overview

This document specifies the four-phase enhancement plan for the DevAgent Team multi-agent collaborative coding system. The goal is to evolve the system from a functional prototype to a production-grade tool with sandboxed execution, version control, multi-language support, and extensible architecture.

**Target Date**: 2026-06-10
**Approach**: Strictly sequential (Phase 1 → Phase 2 → Phase 3 → Phase 4)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React 18 + TS)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ FileTree │  │ CodeEditor│  │ AgentPanel   │  │ TerminalPanel   │ │
│  │ + History│  │ + DiffView│  │ + ReviewTools│  │ + SettingsPanel │ │
│  └──────────┘  └──────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │ REST / WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + Python)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ REST API    │  │ WebSocket   │  │ Event-Driven Orchestrator   │ │
│  │ /api/*      │  │ /ws/{pid}   │  │ (MessageBus + PluginRegistry)│ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ PM Agent │  │ Architect│  │ Coder    │  │ Reviewer + pylint │  │
│  │ (Plugin) │  │ (Plugin) │  │ (Plugin) │  │ (Plugin)          │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ DockerSandbox│  │ GitManager   │  │ StaticAnalyzer         │   │
│  │ (exec)       │  │ (commit/log) │  │ (pylint/mypy/eslint)   │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ FileManager  │  │ StateStore   │  │ Config (UI-editable)   │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │  devagent-sandbox     │
                    │  (Docker container)   │
                    │  Python + Node + git  │
                    └───────────────────────┘
```

---

## Phase 1: Infrastructure

### 1.1 Docker Sandbox Execution

**New File**: `backend/tools/docker_sandbox.py`

```python
class DockerSandbox:
    """Long-running container sandbox executing code via docker exec."""

    def __init__(self, container_name: str = "devagent-sandbox"):
        self.container_name = container_name

    def _ensure_container(self):
        """Check if container exists and is running; create if needed."""

    def execute(
        self,
        project_id: str,
        command: list[str],
        timeout: int = 30,
    ) -> ExecutionResult:
        """Execute command inside container, return stdout/stderr/exit_code."""

    def validate_syntax(
        self,
        code: str,
        language: str,
    ) -> tuple[bool, str | None]:
        """Validate syntax: Python via py_compile, TypeScript via node --check."""

    def write_file(self, project_id: str, path: str, content: str):
        """Write file to container workspace for temporary execution."""
```

**Container Lifecycle**:
- On startup, check if `devagent-sandbox` container exists and is running
- If not, create from image `devagent-sandbox:latest`
- Each project's code directory is bind-mounted from host `output/{project_id}` to container `/workspace/{project_id}`
- Container runs `tail -f /dev/null` to stay alive
- Execution uses `docker exec` with working directory set to `/workspace/{project_id}`

**Docker Image** (`sandbox/Dockerfile`):
```dockerfile
FROM python:3.11-slim-bookworm

# Install Node.js 18
RUN apt-get update && apt-get install -y curl git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Python tools for Phase 3
RUN pip install pylint mypy --no-cache-dir

# Pre-install TypeScript tools for Phase 3
RUN npm install -g typescript eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

WORKDIR /workspace
CMD ["tail", "-f", "/dev/null"]
```

### 1.2 CodeRunner Enhancement

**Modified File**: `backend/tools/code_runner.py`

- Keep existing Python `py_compile` validation as **fallback** when Docker is unavailable
- When `settings.use_docker_sandbox=True`, delegate to `DockerSandbox.validate_syntax()`
- Support language auto-detection by file extension:
  - `.py` → Python
  - `.ts`, `.js` → TypeScript / JavaScript
- Add execution method that runs code in sandbox and captures stdout/stderr

### 1.3 Docker Compose

**New File**: `docker-compose.yml`

```yaml
services:
  sandbox:
    build:
      context: ./sandbox
      dockerfile: Dockerfile
    container_name: devagent-sandbox
    volumes:
      - ./backend/output:/workspace
    command: tail -f /dev/null

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/output:/app/output
    environment:
      - USE_DOCKER_SANDBOX=true
      - SANDBOX_CONTAINER_NAME=devagent-sandbox
    depends_on:
      - sandbox

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
```

### 1.4 Configuration Extension

**Modified File**: `backend/config.py`

New fields:
- `use_docker_sandbox: bool = Field(default=False)` — backward compatibility for local dev without Docker
- `sandbox_container_name: str = "devagent-sandbox"`
- `sandbox_image: str = "devagent-sandbox:latest"`
- `sandbox_workspace: str = "/workspace"`

### 1.5 Workflow Impact

In `main.py` `_run_workflow()`:
1. After Coder Agent generates code, syntax validation goes through DockerSandbox
2. If validation fails, feedback mechanism remains unchanged
3. Execution output (stdout/stderr) is captured and stored for Phase 2 terminal panel

---

## Phase 2: User Experience

### 2.1 Git Integration

**New File**: `backend/tools/git_manager.py`

```python
class GitManager:
    """Git operations per project."""

    def init_repo(self, project_id: str):
        """Run git init in project directory."""

    def commit(self, project_id: str, message: str, files: list[str] | None = None):
        """Stage and commit files. files=None commits all changes."""

    def get_log(self, project_id: str, limit: int = 20) -> list[Commit]:
        """Return commit history: [(hash, message, timestamp, author)]."""

    def get_diff(self, project_id: str, commit_hash: str | None = None) -> str:
        """Return diff. commit_hash=None returns working tree diff against HEAD."""

    def get_status(self, project_id: str) -> dict:
        """Return {modified: [...], untracked: [...], staged: [...]}."""
```

**Workflow Integration** (`main.py`):
- Immediately after project creation: `git init`
- After PM Agent outputs `spec.md`: commit `"spec: add functional specification"`
- After Architect Agent outputs `architecture.md`: commit `"arch: add system architecture"`
- After Coder Agent generates code: commit `"coder: iteration {n}"`
- After Reviewer Agent outputs `review.md`: commit `"review: add review report"`

Commits are triggered explicitly by the workflow orchestrator, not implicitly by FileManager, ensuring meaningful commit messages that reflect the agent action.

### 2.2 Terminal / Log Panel

**New File**: `frontend/src/components/TerminalPanel.tsx`

- Terminal-styled panel with black background and monospace font
- Displays:
  - Agent execution logs (e.g., "Running Coder Agent...")
  - Code execution output (stdout/stderr from DockerSandbox)
  - Syntax validation results
- ANSI color code support via `ansi-to-html` or similar
- Auto-scroll to bottom
- Filter: show all / show errors only / show agent logs only

**WebSocket Message Extension**:
```json
{"type": "terminal_output", "stream": "stdout", "content": "Hello world\n"}
{"type": "terminal_output", "stream": "stderr", "content": "Error: ...\n"}
{"type": "terminal_output", "stream": "agent", "content": "Coder Agent started..."}
```

**Backend Integration**:
- `DockerSandbox.execute()` stdout/stderr piped to WebSocket in real-time
- Agent lifecycle events (started/completed/failed) also pushed to terminal stream

### 2.3 Diff Viewer

**New File**: `frontend/src/components/DiffViewer.tsx`

- Side-by-side diff rendering using parsed diff format
- Syntax highlighting for added/removed lines
- Two modes:
  - **Live Diff**: Current iteration vs previous version (Coder Agent changes)
  - **History Diff**: View diff of any historical commit
- Integrated into AgentPanel, shown when Reviewer reports issues

**New REST APIs**:
```
GET /api/projects/{project_id}/git/log           → [{hash, message, timestamp}]
GET /api/projects/{project_id}/git/diff          → working tree diff (string)
GET /api/projects/{project_id}/git/diff/{hash}   → specific commit diff
```

### 2.4 Project History List

**New File**: `frontend/src/components/ProjectHistory.tsx`

- Located **above** the file tree in the left sidebar
- Displays all projects from StateStore (sorted by last update, newest first)
- Each row shows: requirement preview (first 30 chars), status badge, last updated time
- Click to switch active project: reloads file tree, code editor, and agent status
- New project button clears the form and starts fresh

**StateStore Extension**:
```python
def list_projects(self) -> list[ProjectState]:
    """Scan output/states/ directory, return all projects sorted by mtime desc."""
```

**New REST API**:
```
GET /api/projects  → [{project_id, state, requirement_preview, updated_at}]
```

---

## Phase 3: Capability Enhancement

### 3.1 Static Analysis Integration

**New File**: `backend/tools/static_analyzer.py`

```python
class StaticAnalyzer:
    """Run static analysis tools in sandbox, return structured issues."""

    def analyze_python(self, project_id: str) -> list[Issue]:
        """Run pylint and mypy, return issue list."""

    def analyze_typescript(self, project_id: str) -> list[Issue]:
        """Run eslint and tsc --noEmit, return issue list."""

    def analyze(self, project_id: str, language: str) -> list[Issue]:
        """Auto-select analyzer by language."""
```

**Issue Model**:
```python
class Issue(BaseModel):
    tool: str          # "pylint" | "mypy" | "eslint" | "tsc"
    file: str
    line: int
    column: int
    severity: str      # "error" | "warning" | "info"
    message: str
    code: str | None   # e.g., pylint code "E0602"
```

**Reviewer Agent Integration**:
1. Before LLM-based review, run `StaticAnalyzer.analyze()`
2. Inject tool results into Reviewer prompt:
   ```
   Static analysis found the following issues:
   [formatted issue list]

   Please review the code, considering both the tool report and your own judgment.
   ```
3. LLM reviews code with tool context, output format unchanged
4. Frontend Reviewer panel gets new **"Static Analysis"** tab showing issues grouped by severity

**Execution**: Tools run inside the Docker sandbox (pre-installed in Phase 1 image), via `docker exec`.

### 3.2 Multi-Language Code Generation

**Coder Agent Enhancement**:
- `coder.txt` prompt extended with `{{language}}` variable:
  ```
  Generate {{language}} code for the following specification...
  ```
- Default language read from `settings.default_language` (default: `"python"`)
- Language affects:
  - File extensions generated (`.py` → `.ts`)
  - Import/module syntax in generated code
  - Project scaffolding (package.json for TS, requirements.txt for Python)

**Syntax Validation Matrix**:

| Language | Validation Method | Sandbox Command |
|----------|------------------|-----------------|
| Python | `py_compile` | `python -m py_compile {file}` |
| TypeScript | `tsc --noEmit` | `npx tsc --noEmit` (project-level) |
| JavaScript | `node --check` | `node --check {file}` |

**File Tree Icons**:
- `.py` → 🐍 Python icon
- `.ts` → 📘 TypeScript icon
- `.js` → 📙 JavaScript icon
- Other → 📄 generic file icon

**Language Switching**:
- Configurable per new project (via SettingsPanel)
- Existing projects keep their original language
- No mixed-language projects (for simplicity)

### 3.3 Settings Panel (Configuration UI)

**New File**: `frontend/src/components/SettingsPanel.tsx`

Drawer-style panel (slides from right), organized in sections:

**LLM Configuration**
- Provider selector (Anthropic / OpenAI / DeepSeek / GLM)
- API Key input (password field with show/hide toggle)
- Default model selector (options populated by `GET /api/settings/models`)

**Agent Configuration**
- Temperature slider (0.0 - 1.0, step 0.1)
- Max review iterations spinner (1 - 10)
- Code execution timeout input (seconds)

**Language & Sandbox**
- Target language radio (Python / TypeScript)
- Docker sandbox toggle (on/off)

**New REST APIs**:
```
GET  /api/settings          → current settings (API keys masked as "***")
POST /api/settings          → update settings (write to config.json)
GET  /api/settings/models   → available models grouped by provider
```

**Backend Configuration Persistence**:
- New file: `settings.json` (added to `.gitignore`)
- Load priority (highest wins): defaults < `.env` < `settings.json` < environment variables
- On `POST /api/settings`, write to `settings.json` and hot-reload affected components
- `LLMClient` reinitializes when provider/model/key changes

---

## Phase 4: Architecture Optimization

### 4.1 Event-Driven Workflow Refactor

**Current Problem**: `main.py` `_run_workflow()` is procedural with hardcoded agent calls. Agents are tightly coupled.

**Goal**: Convert to event-driven architecture where agents are independent consumers.

**Event Types** (`backend/core/events.py`):
```python
class EventType(str, Enum):
    PROJECT_CREATED = "project.created"
    SPEC_GENERATED = "spec.generated"
    ARCHITECTURE_GENERATED = "architecture.generated"
    CODE_GENERATED = "code.generated"
    SYNTAX_CHECKED = "syntax.checked"
    REVIEW_COMPLETED = "review.completed"
    ITERATION_STARTED = "iteration.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    ERROR = "workflow.error"

class Event(BaseModel):
    type: EventType
    project_id: str
    payload: dict
    timestamp: datetime
    source: str
```

**Event Flow**:
```
PROJECT_CREATED
    → PM Agent consumer → SPEC_GENERATED
SPEC_GENERATED
    → Architect Agent consumer → ARCHITECTURE_GENERATED
ARCHITECTURE_GENERATED
    → Coder Agent consumer → CODE_GENERATED
CODE_GENERATED
    → SyntaxChecker consumer → SYNTAX_CHECKED
SYNTAX_CHECKED
    → Reviewer Agent consumer → REVIEW_COMPLETED
REVIEW_COMPLETED
    → (passed=True) → WORKFLOW_COMPLETED
    → (passed=False, can_iterate) → ITERATION_STARTED → Coder Agent
    → (passed=False, exhausted) → WORKFLOW_COMPLETED (with warnings)
```

**MessageBus Upgrade** (`backend/core/message_bus.py`):
```python
class MessageBus:
    """Pub/sub with persistent event log."""

    def subscribe(self, event_type: EventType, handler: Callable):
        """Register event consumer."""

    def publish(self, event: Event):
        """Dispatch to all subscribers asynchronously."""

    def get_history(self, project_id: str) -> list[Event]:
        """Retrieve event log for a project (for debugging/replay)."""
```

**Backward Compatibility**: REST API (`/api/projects`) and WebSocket (`/ws/{pid}`) interfaces remain unchanged. Only internal workflow implementation changes.

### 4.2 Agent Plugin System

**Plugin Interface** (`backend/agents/plugin.py`):
```python
class AgentPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def consumes(self) -> list[EventType]: ...

    @property
    @abstractmethod
    def produces(self) -> EventType | None: ...

    @abstractmethod
    async def execute(self, context: AgentContext, event: Event) -> AgentOutput: ...
```

**Plugin Registry** (`backend/agents/registry.py`):
```python
class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, AgentPlugin] = {}

    def register(self, plugin: AgentPlugin):
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> AgentPlugin | None:
        return self._plugins.get(name)

    def discover(self, package: str):
        """Auto-scan package for AgentPlugin subclasses."""
```

**Migration of Existing Agents**:
- `PMAgent`, `ArchitectAgent`, `CoderAgent`, `ReviewerAgent` → implement `AgentPlugin`
- Registration in `backend/agents/__init__.py`:
  ```python
  registry = PluginRegistry()
  registry.register(PMAgent())
  registry.register(ArchitectAgent())
  registry.register(CoderAgent())
  registry.register(ReviewerAgent())
  ```

**Dynamic Discovery** (future extensibility):
- Scan `backend/plugins/` directory at startup
- Import all Python files, register any `AgentPlugin` subclasses
- External plugins can be dropped in without modifying core code

**Workflow Configuration**:
```python
# backend/config.py
workflow: list[str] = ["pm", "architect", "coder", "reviewer"]
```

Users can:
- Replace default agents (custom Coder with different prompt strategy)
- Add new agents (e.g., `SecurityReviewer`, `TestGenerator`)
- Reorder agents (e.g., add design review after Architect)

**Orchestrator Integration**:
```python
class EventDrivenOrchestrator:
    def __init__(self, registry: PluginRegistry, bus: MessageBus):
        # Wire each plugin's produces → next plugin's consumes
        for plugin in registry.all():
            for event_type in plugin.consumes:
                bus.subscribe(event_type, self._wrap_handler(plugin))

    def _wrap_handler(self, plugin: AgentPlugin) -> Callable:
        async def handler(event: Event):
            context = self._build_context(event)
            output = await plugin.execute(context, event)
            if plugin.produces:
                bus.publish(Event(type=plugin.produces, ...))
        return handler
```

---

## Error Handling

### Phase 1
- **Docker not available**: `use_docker_sandbox=False` falls back to local execution
- **Container startup failure**: Log error, emit WebSocket error, workflow continues with fallback
- **Exec timeout**: Kill process, return timeout error to Coder as feedback

### Phase 2
- **Git not initialized**: Silently init before first commit
- **Commit failure** (e.g., no changes): Log warning, continue workflow
- **Terminal WebSocket overflow**: Truncate old messages (keep last 1000 lines)

### Phase 3
- **Static analysis tool not found**: Skip tool, let LLM review alone
- **TypeScript project without tsconfig**: Generate default `tsconfig.json` before analysis
- **Config save failure**: Return 500, keep in-memory settings, retry on next request

### Phase 4
- **Plugin load failure**: Log error, skip plugin, continue with remaining
- **Event handler crash**: Catch exception, publish ERROR event, workflow may halt or retry
- **Circular event flow**: Detected at startup via topology validation

---

## Testing Strategy

### Phase 1
- `test_docker_sandbox.py`: Mock docker client, test container lifecycle, exec behavior
- `test_code_runner.py`: Test language auto-detection, fallback behavior
- Integration test: Start sandbox container, execute Python/TS code, verify output

### Phase 2
- `test_git_manager.py`: Test init, commit, log, diff in temp directory
- Frontend: Test TerminalPanel rendering, WebSocket message handling
- `test_state_store.py`: Test `list_projects()` sorting

### Phase 3
- `test_static_analyzer.py`: Mock tool output parsing, verify Issue model
- `test_coder_agent.py`: Test language-specific prompt generation
- Frontend: Test SettingsPanel form submission, API key masking

### Phase 4
- `test_message_bus.py`: Test pub/sub, multiple subscribers, event persistence
- `test_plugin_registry.py`: Test registration, discovery, workflow resolution
- `test_orchestrator.py`: Test full event flow with mock plugins

---

## Dependencies

### New Backend Dependencies
```
# requirements.txt additions
# (Phase 1 - Docker is external dependency, use subprocess)
# (Phase 2 - git is external dependency)
# (Phase 3 - pylint/mypy installed in sandbox image, not host)
```

### New Frontend Dependencies
```json
// package.json additions
{
  "ansi-to-html": "^0.7.2",     // Phase 2: Terminal color codes
  "diff2html": "^3.4.48"        // Phase 2: Diff rendering
}
```

---

## Rollout Order

| Phase | Features | Estimated Effort |
|-------|----------|-----------------|
| 1 | Docker sandbox, CodeRunner refactor, Docker Compose | Medium |
| 2 | Git integration, Terminal panel, Diff viewer, Project history | Medium |
| 3 | pylint/mypy, TypeScript support, Settings panel | Medium |
| 4 | Event-driven refactor, Plugin system | Large |

**Total**: ~4 phases, each 1-2 weeks of focused development.
