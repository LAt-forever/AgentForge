# 🤖 DevAgent Team

> **Multi-Agent collaborative coding system** — describe what you want, watch PM → Architect → Coder → Reviewer agents build it together.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎬 Demo

![DevAgent Demo](docs/demo.gif)

> Type a requirement like *"Build a Python CLI that greets the user by name"* and watch the team build it in real-time.

---

## ✨ Features

### 🤝 Multi-Agent Collaboration
- **PM Agent** — analyzes requirements, writes functional specifications
- **Architect Agent** — designs system architecture from specs
- **Coder Agent** — generates complete, runnable code files
- **Reviewer Agent** — reviews against spec with static analysis augmentation
- **Review Loop** — auto-iterates up to 5 rounds until quality passes

### 🏗️ Event-Driven Architecture *(New in v2)*
- Agents are **loosely-coupled plugins** consuming/producing events
- **EventBus** routes `PROJECT_CREATED → SPEC_GENERATED → ARCHITECTURE_GENERATED → CODE_GENERATED → REVIEW_COMPLETED`
- Easy to add/replace/reorder agents via `PluginRegistry`

### 🐳 Docker Sandbox *(Secure Execution)*
- Code runs inside a persistent Docker container
- Automatic syntax validation (Python `py_compile`, TypeScript `tsc`)
- Static analysis injection: `pylint`, `mypy` for Python; `tsc` for TypeScript
- Graceful fallback to local execution when Docker unavailable

### 🌐 Multi-LLM Support
| Provider | Models | Status |
|----------|--------|--------|
| Anthropic | Claude 3.5 Sonnet | ✅ |
| OpenAI | GPT-4o | ✅ |
| DeepSeek | DeepSeek-V4-Pro | ✅ |
| Zhipu AI (GLM) | GLM-4-Plus | ✅ |

- **Auto-fallback** — if primary model fails, automatically tries fallback
- **Live model switching** — change models without restart via settings UI

### 🛠️ Development Features
- 📝 **Git Integration** — every agent step auto-committed
- 🖥️ **Terminal Panel** — live stdout/stderr/agent logs streamed via WebSocket
- 📊 **Diff View** — inspect code changes between iterations
- 📜 **Project History** — browse all past projects with metadata
- ⚙️ **Settings UI** — manage API keys, models, timeouts, iteration limits
- 🌍 **Multi-language** — generate Python, TypeScript, or JavaScript

---

## 🏛️ Architecture

### Event-Driven Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         EventBus                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   PROJECT_CREATED  ──▶  PMPlugin  ──▶  SPEC_GENERATED               │
│       │                                                              │
│       ▼                                                              │
│   SPEC_GENERATED   ──▶  ArchitectPlugin  ──▶  ARCHITECTURE_GENERATED│
│       │                                                              │
│       ▼                                                              │
│   ARCHITECTURE_GENERATED  ──▶  CoderPlugin  ──▶  CODE_GENERATED     │
│       │                                                              │
│       ▼                                                              │
│   CODE_GENERATED   ──▶  SyntaxChecker  ──▶  SYNTAX_CHECKED          │
│       │                                                              │
│       ▼                                                              │
│   SYNTAX_CHECKED   ──▶  ReviewerPlugin  ──▶  REVIEW_COMPLETED       │
│       │                                                              │
│       ▼                                                              │
│   REVIEW_COMPLETED ──▶  Decision: WORKFLOW_COMPLETED                │
│                          or ITERATION_STARTED  ──▶  Coder (loop)    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Plugin System

```python
class AgentPlugin(ABC):
    @property @abstractmethod def name(self) -> str          # "coder"
    @property @abstractmethod def consumes(self) -> list[EventType]
    @property @abstractmethod def produces(self) -> EventType | None
    @abstractmethod async def execute(self, context, event) -> AgentOutput
```

Built-in plugins are registered automatically. Drop a new plugin into `backend/plugins/` and it will be auto-discovered.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, WebSocket |
| **Orchestration** | Event-driven, async/await |
| **LLM Client** | Anthropic SDK, OpenAI SDK, custom DeepSeek/GLM adapters |
| **Sandbox** | Docker (persistent container) |
| **Frontend** | React 18, TypeScript, Vite |
| **Editor** | CodeMirror 6 |
| **State** | Zustand |
| **Styling** | CSS Variables (Codex-style dark theme) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- At least one LLM API key (Anthropic / OpenAI / DeepSeek / GLM)
- Docker Desktop (optional, for sandboxed execution)

### 1. Clone & Install

```bash
git clone <repo-url>
cd devagent-team

# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Configure API Keys

Create `.env` in the project root:

```bash
# Pick at least one provider
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
GLM_API_KEY=your-glm-key

# Optional: override defaults
DEFAULT_MODEL=glm-4-plus
USE_DOCKER_SANDBOX=true
```

Or use the in-app **Settings UI** to configure keys interactively.

### 3. Start with Docker Compose (Recommended)

```bash
docker compose up --build
```

This starts both backend and frontend, plus the sandbox container.

### 4. Or Start Manually

```bash
# Terminal 1 — Backend
cd backend
python main.py

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

---

## 📁 Project Structure

```
devagent-team/
├── backend/
│   ├── agents/
│   │   ├── built_in/           # Built-in plugins (PM, Architect, Coder, Reviewer)
│   │   ├── plugin_base.py      # AgentPlugin ABC
│   │   ├── base_agent.py       # Legacy base + AgentContext
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   └── reviewer_agent.py
│   ├── core/
│   │   ├── event_bus.py        # EventBus + Event + EventType
│   │   ├── plugin_registry.py  # PluginRegistry
│   │   ├── state_store.py      # Project state persistence
│   │   ├── settings_manager.py # JSON settings with secret masking
│   │   └── message_bus.py      # Legacy (replaced by EventBus)
│   ├── orchestrator/
│   │   ├── event_driven_orchestrator.py  # Event-driven workflow engine
│   │   ├── scheduler.py        # Legacy agent scheduler
│   │   ├── state_machine.py    # Workflow state machine
│   │   └── websocket_manager.py# WebSocket broadcast
│   ├── llm/
│   │   ├── client.py           # Multi-provider LLM client with fallback
│   │   ├── models.py           # LLMConfig, LLMResponse
│   │   └── prompts/            # System prompts for each agent
│   ├── tools/
│   │   ├── docker_sandbox.py   # Docker sandbox for code execution
│   │   ├── file_manager.py     # File I/O within project directory
│   │   ├── git_manager.py      # Git init + commit per project
│   │   ├── code_runner.py      # Syntax validation + local execution
│   │   └── static_analyzer.py  # pylint/mypy/tsc integration
│   └── main.py                 # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── components/         # Chat, Editor, Terminal, ReviewReport, Settings
│   │   ├── hooks/              # useWebSocket
│   │   └── store/              # Zustand state management
│   └── index.html
├── tests/                      # Pytest test suite
│   ├── backend/
│   └── e2e/                    # End-to-end workflow tests
├── docs/
│   ├── demo.gif
│   └── superpowers/            # Design specs & implementation plans
├── output/                     # Generated project files
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## ⚙️ Configuration

Settings are loaded from environment variables (`.env`) and can be overridden at runtime via the Settings UI or REST API.

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `glm-4-plus` | Primary LLM model |
| `FALLBACK_MODEL` | `glm-4-plus` | Fallback when primary fails |
| `MAX_REVIEW_ITERATIONS` | `5` | Max review → code loops |
| `CODE_EXECUTION_TIMEOUT` | `30` | Sandbox execution timeout (s) |
| `DEFAULT_LANGUAGE` | `python` | Code generation language |
| `USE_DOCKER_SANDBOX` | `false` | Enable Docker sandbox |

Settings are persisted to `output/settings.json`. API keys are masked with `***` in the UI.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Skip Docker integration tests (if Docker unavailable)
pytest tests/ -v --ignore=tests/backend/tools/test_docker_sandbox_integration.py

# Run mock end-to-end workflow test
pytest tests/e2e/test_event_driven_workflow_mock.py -v

# Run frontend build check
cd frontend && npm run build
```

---

## 🛣️ Roadmap

- [x] Phase 1 — Docker sandbox + Docker Compose
- [x] Phase 2 — Git integration, terminal panel, diff view, project history
- [x] Phase 3 — Static analysis (pylint/mypy), multi-language, settings UI
- [x] Phase 4 — Event-driven refactor, agent plugin system
- [ ] Phase 5 — Human-in-the-loop approval, custom plugin marketplace

---

## 📝 License

MIT
