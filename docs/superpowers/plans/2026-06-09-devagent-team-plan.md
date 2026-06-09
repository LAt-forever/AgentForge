# DevAgent Team Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-Agent collaborative coding system with a Codex-style React frontend, where PM → Architect → Coder → Reviewer Agents cooperate to turn natural language requirements into runnable code.

**Architecture:** Python FastAPI backend with handwritten state-machine orchestrator (no LangChain), 4 specialized Agents with structured prompts, WebSocket real-time status streaming to a React TypeScript frontend with CodeMirror editor.

**Tech Stack:** Python 3.11+, FastAPI, anthropic/openai SDKs, React 18, TypeScript, Vite, Zustand, CodeMirror 6

---

## File Structure

```
devagent-team/
├── README.md
├── requirements.txt
├── pyproject.toml
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── __init__.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── state_machine.py
│   │   ├── scheduler.py
│   │   └── websocket_manager.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── pm_agent.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   └── reviewer_agent.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── models.py
│   │   └── prompts/
│   │       ├── pm.txt
│   │       ├── architect.txt
│   │       ├── coder.txt
│   │       └── reviewer.txt
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_manager.py
│   │   └── code_runner.py
│   └── core/
│       ├── __init__.py
│       ├── message_bus.py
│       └── state_store.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   ├── store/
│   │   │   └── useStore.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── FileTree.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── AgentPanel.tsx
│   │   │   ├── AgentCard.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ReviewReport.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   └── useAgentStatus.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── styles/
│   │       └── theme.css
│   └── public/
└── output/
    └── .gitkeep
```

---

## Phase 1: Project Skeleton

### Task 1: Root Project Files

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `output/.gitkeep`

- [ ] **Step 1: Create root files**

`README.md`:
```markdown
# DevAgent Team

Multi-Agent collaborative coding system. PM → Architect → Coder → Reviewer Agents cooperate to build software from natural language requirements.

## Quick Start

### Backend
\`\`\`bash
cd backend
pip install -r requirements.txt
python main.py
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

## Architecture

4 specialized Agents orchestrated by a state machine:
- **PM Agent**: Parses requirements into structured specs
- **Architect Agent**: Designs system architecture and module interfaces
- **Coder Agent**: Generates implementation code
- **Reviewer Agent**: Reviews code quality and suggests fixes

## Tech Stack

- Backend: Python, FastAPI, Claude/GPT-4 API
- Frontend: React, TypeScript, Vite, CodeMirror 6
- Communication: WebSocket + REST API
```

`requirements.txt`:
```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
anthropic>=0.25.0
openai>=1.12.0
pydantic>=2.6.0
python-multipart>=0.0.9
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

`pyproject.toml`:
```toml
[project]
name = "devagent-team"
version = "0.1.0"
description = "Multi-Agent collaborative coding system"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["backend"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Commit**

```bash
git init
git add README.md requirements.txt pyproject.toml output/.gitkeep
git commit -m "chore: project skeleton and root config"
```

---

### Task 2: Backend Config

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `tests/backend/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/test_config.py`:
```python
import os
from backend.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.app_name == "DevAgent Team"
    assert settings.output_dir == "output"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    monkeypatch.setenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("MAX_REVIEW_ITERATIONS", "5")

    settings = Settings()
    assert settings.anthropic_api_key == "test-key-anthropic"
    assert settings.openai_api_key == "test-key-openai"
    assert settings.default_model == "claude-3-5-sonnet-20241022"
    assert settings.max_review_iterations == 5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/lanhezheng/vibe-agent
pytest tests/backend/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'backend.config'`

- [ ] **Step 3: Write minimal implementation**

`backend/config.py`:
```python
"""Application configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "DevAgent Team"
    output_dir: str = "output"

    # LLM API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Model configuration
    default_model: str = "claude-3-5-sonnet-20241022"
    fallback_model: str = "gpt-4o"

    # Workflow configuration
    max_review_iterations: int = 3
    max_llm_retries: int = 3
    code_execution_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
```

- [ ] **Step 4: Add pydantic-settings to requirements**

Add `pydantic-settings>=2.1.0` to `requirements.txt`.

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/backend/test_config.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/config.py backend/__init__.py tests/backend/test_config.py requirements.txt
git commit -m "feat: add app configuration with env var support"
```

---

## Phase 2: Core Infrastructure

### Task 3: LLM Client

**Files:**
- Create: `backend/llm/__init__.py`
- Create: `backend/llm/models.py`
- Create: `backend/llm/client.py`
- Create: `tests/backend/llm/test_client.py`

- [ ] **Step 1: Write models**

`backend/llm/models.py`:
```python
"""LLM-related data models."""

from enum import Enum
from dataclasses import dataclass


class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    usage: dict | None = None


@dataclass
class LLMConfig:
    """Configuration for an LLM call."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""
```

- [ ] **Step 2: Write the failing test**

`tests/backend/llm/test_client.py`:
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

from backend.llm.client import LLMClient
from backend.llm.models import LLMConfig


@pytest.fixture
def client():
    return LLMClient(anthropic_key="test-anthropic", openai_key="test-openai")


@pytest.mark.asyncio
async def test_call_anthropic_success(client):
    mock_response = Mock()
    mock_response.content = [Mock(text="Hello from Claude")]
    mock_response.model = "claude-3-5-sonnet-20241022"
    mock_response.usage = Mock(input_tokens=10, output_tokens=5)

    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_response)

        config = LLMConfig(model="claude-3-5-sonnet-20241022", system_prompt="You are a helper")
        result = await client.call("Say hello", config)

        assert result.content == "Hello from Claude"
        assert result.model == "claude-3-5-sonnet-20241022"


@pytest.mark.asyncio
async def test_call_fallback_on_failure(client):
    """Test fallback to OpenAI when Anthropic fails."""
    mock_openai_response = Mock()
    mock_openai_response.choices = [Mock(message=Mock(content="Hello from GPT"))]
    mock_openai_response.model = "gpt-4o"
    mock_openai_response.usage = Mock(prompt_tokens=10, completion_tokens=5)

    with patch("anthropic.AsyncAnthropic") as MockAnthropic:
        instance = MockAnthropic.return_value
        instance.messages.create = AsyncMock(side_effect=Exception("Anthropic error"))

        with patch("openai.AsyncOpenAI") as MockOpenAI:
            openai_instance = MockOpenAI.return_value
            openai_instance.chat.completions.create = AsyncMock(return_value=mock_openai_response)

            config = LLMConfig(model="claude-3-5-sonnet-20241022", system_prompt="Helper")
            result = await client.call("Say hello", config)

            assert result.content == "Hello from GPT"
            assert result.model == "gpt-4o"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/backend/llm/test_client.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write LLM Client implementation**

`backend/llm/client.py`:
```python
"""Unified LLM client with retry and fallback support."""

import asyncio
import logging
from typing import Optional

from backend.llm.models import LLMConfig, LLMResponse, ModelProvider

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified client for calling LLM APIs with retry and fallback."""

    def __init__(self, anthropic_key: str = "", openai_key: str = ""):
        self.anthropic_key = anthropic_key
        self.openai_key = openai_key
        self._anthropic_client = None
        self._openai_client = None

    @property
    def anthropic(self):
        if self._anthropic_client is None and self.anthropic_key:
            import anthropic
            self._anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
        return self._anthropic_client

    @property
    def openai(self):
        if self._openai_client is None and self.openai_key:
            import openai
            self._openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
        return self._openai_client

    async def call(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Call LLM with retry and fallback."""
        provider = self._get_provider(config.model)
        last_error = None

        # Try primary model with retries
        for attempt in range(3):
            try:
                if provider == ModelProvider.ANTHROPIC and self.anthropic:
                    return await self._call_anthropic(prompt, config)
                elif provider == ModelProvider.OPENAI and self.openai:
                    return await self._call_openai(prompt, config)
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Fallback to alternative provider
        fallback_config = LLMConfig(
            model="gpt-4o" if provider == ModelProvider.ANTHROPIC else "claude-3-5-sonnet-20241022",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
        )
        try:
            if provider == ModelProvider.ANTHROPIC and self.openai:
                logger.info("Falling back to OpenAI")
                return await self._call_openai(prompt, fallback_config)
            elif provider == ModelProvider.OPENAI and self.anthropic:
                logger.info("Falling back to Anthropic")
                return await self._call_anthropic(prompt, fallback_config)
        except Exception as e:
            last_error = e

        raise RuntimeError(f"All LLM calls failed. Last error: {last_error}")

    def _get_provider(self, model: str) -> ModelProvider:
        if model.startswith("claude"):
            return ModelProvider.ANTHROPIC
        return ModelProvider.OPENAI

    async def _call_anthropic(self, prompt: str, config: LLMConfig) -> LLMResponse:
        response = await self.anthropic.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        )

    async def _call_openai(self, prompt: str, config: LLMConfig) -> LLMResponse:
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens},
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/backend/llm/test_client.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/llm/ tests/backend/llm/
git commit -m "feat: add unified LLM client with retry and fallback"
```

---

### Task 4: File Manager

**Files:**
- Create: `backend/tools/__init__.py`
- Create: `backend/tools/file_manager.py`
- Create: `tests/backend/tools/test_file_manager.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/tools/test_file_manager.py`:
```python
import os
import tempfile
import pytest

from backend.tools.file_manager import FileManager


@pytest.fixture
def file_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileManager(base_dir=tmpdir)


def test_write_and_read_file(file_manager):
    file_manager.write_file("test.txt", "Hello World")
    content = file_manager.read_file("test.txt")
    assert content == "Hello World"


def test_list_files(file_manager):
    file_manager.write_file("a.py", "print(1)")
    file_manager.write_file("b/c.py", "print(2)")
    files = file_manager.list_files()
    assert "a.py" in files
    assert "b/c.py" in files


def test_file_exists(file_manager):
    assert not file_manager.exists("missing.txt")
    file_manager.write_file("exists.txt", "yes")
    assert file_manager.exists("exists.txt")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/tools/test_file_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/tools/file_manager.py`:
```python
"""File management utilities for Agent output."""

import os
from pathlib import Path


class FileManager:
    """Manages file operations within a project directory."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_file(self, relative_path: str, content: str) -> str:
        """Write content to a file. Returns absolute path."""
        file_path = self.base_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def read_file(self, relative_path: str) -> str:
        """Read content from a file."""
        file_path = self.base_dir / relative_path
        return file_path.read_text(encoding="utf-8")

    def exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        return (self.base_dir / relative_path).exists()

    def list_files(self) -> list[str]:
        """List all files recursively, returning relative paths."""
        files = []
        for path in self.base_dir.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.base_dir)))
        return sorted(files)

    def delete_file(self, relative_path: str) -> None:
        """Delete a file."""
        file_path = self.base_dir / relative_path
        if file_path.exists():
            file_path.unlink()

    def get_absolute_path(self, relative_path: str) -> str:
        """Get absolute path for a relative path."""
        return str(self.base_dir / relative_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/backend/tools/test_file_manager.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tools/ tests/backend/tools/
git commit -m "feat: add file manager for agent output"
```

---

### Task 5: Code Runner

**Files:**
- Create: `backend/tools/code_runner.py`
- Create: `tests/backend/tools/test_code_runner.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/tools/test_code_runner.py`:
```python
import pytest
import tempfile
import os

from backend.tools.code_runner import CodeRunner


@pytest.fixture
def runner():
    return CodeRunner(timeout=5)


def test_validate_syntax_valid(runner):
    is_valid, error = runner.validate_syntax("print('hello')")
    assert is_valid is True
    assert error == ""


def test_validate_syntax_invalid(runner):
    is_valid, error = runner.validate_syntax("print('hello'")
    assert is_valid is False
    assert "unexpected EOF" in error or "invalid syntax" in error


def test_run_code_success(runner):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('success')\n")
        f.flush()
        path = f.name

    try:
        stdout, stderr, returncode = runner.run_file(path)
        assert "success" in stdout
        assert returncode == 0
    finally:
        os.unlink(path)


def test_run_code_timeout(runner):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("import time; time.sleep(10)\n")
        f.flush()
        path = f.name

    try:
        stdout, stderr, returncode = runner.run_file(path)
        assert returncode != 0 or "timeout" in stderr.lower()
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/tools/test_code_runner.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/tools/code_runner.py`:
```python
"""Code execution and validation utilities."""

import subprocess
import tempfile
import os
import py_compile


class CodeRunner:
    """Safely run and validate Python code."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def validate_syntax(self, code: str) -> tuple[bool, str]:
        """Validate Python syntax without executing. Returns (is_valid, error_message)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = f.name

        try:
            py_compile.compile(path, doraise=True)
            return True, ""
        except py_compile.PyCompileError as e:
            return False, str(e)
        finally:
            os.unlink(path)

    def run_file(self, file_path: str) -> tuple[str, str, int]:
        """Run a Python file. Returns (stdout, stderr, returncode)."""
        try:
            result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Execution timed out after {self.timeout} seconds", -1
        except Exception as e:
            return "", str(e), -1

    def run_code(self, code: str) -> tuple[str, str, int]:
        """Run Python code string. Returns (stdout, stderr, returncode)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = f.name

        try:
            return self.run_file(path)
        finally:
            os.unlink(path)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/tools/test_code_runner.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tools/code_runner.py tests/backend/tools/test_code_runner.py
git commit -m "feat: add code runner with syntax validation and timeout"
```

---

### Task 6: Message Bus

**Files:**
- Create: `backend/core/message_bus.py`
- Create: `tests/backend/core/test_message_bus.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/core/test_message_bus.py`:
```python
import pytest
from backend.core.message_bus import MessageBus, Message


@pytest.fixture
def bus():
    return MessageBus()


def test_publish_and_subscribe(bus):
    messages = []

    def handler(msg):
        messages.append(msg)

    bus.subscribe("test_channel", handler)
    bus.publish("test_channel", Message(type="test", sender="a", content="hello"))

    assert len(messages) == 1
    assert messages[0].content == "hello"


def test_multiple_subscribers(bus):
    messages1 = []
    messages2 = []

    bus.subscribe("ch", lambda m: messages1.append(m))
    bus.subscribe("ch", lambda m: messages2.append(m))
    bus.publish("ch", Message(type="t", sender="s", content="x"))

    assert len(messages1) == 1
    assert len(messages2) == 1


def test_no_subscriber_no_crash(bus):
    bus.publish("empty", Message(type="t", sender="s", content="x"))
    # Should not raise
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/core/test_message_bus.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/core/message_bus.py`:
```python
"""Simple in-memory message bus for Agent communication."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Message:
    """A message passed between Agents."""
    type: str
    sender: str
    content: str
    metadata: dict = field(default_factory=dict)


class MessageBus:
    """In-memory pub/sub message bus."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Message], None]]] = {}

    def subscribe(self, channel: str, handler: Callable[[Message], None]) -> None:
        """Subscribe to a channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(handler)

    def publish(self, channel: str, message: Message) -> None:
        """Publish a message to a channel."""
        handlers = self._subscribers.get(channel, [])
        for handler in handlers:
            handler(message)

    def unsubscribe(self, channel: str, handler: Callable[[Message], None]) -> None:
        """Unsubscribe from a channel."""
        if channel in self._subscribers:
            self._subscribers[channel] = [h for h in self._subscribers[channel] if h != handler]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/core/test_message_bus.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/ tests/backend/core/
git commit -m "feat: add in-memory message bus for agent communication"
```

---

### Task 7: State Store

**Files:**
- Create: `backend/core/state_store.py`
- Create: `tests/backend/core/test_state_store.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/core/test_state_store.py`:
```python
import pytest
import tempfile
import json

from backend.core.state_store import StateStore, WorkflowState


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield StateStore(base_dir=tmpdir)


def test_create_and_get_project(store):
    project = store.create_project("test-project")
    assert project.id == "test-project"
    assert project.state == WorkflowState.IDLE

    retrieved = store.get_project("test-project")
    assert retrieved.id == "test-project"


def test_update_state(store):
    project = store.create_project("test-project")
    store.update_state("test-project", WorkflowState.PLANNING)

    project = store.get_project("test-project")
    assert project.state == WorkflowState.PLANNING


def test_update_agent_status(store):
    project = store.create_project("test-project")
    store.update_agent_status("test-project", "coder", {"status": "running", "progress": 50})

    project = store.get_project("test-project")
    assert project.agent_statuses["coder"]["status"] == "running"
    assert project.agent_statuses["coder"]["progress"] == 50


def test_persistence(store):
    store.create_project("persist-test")
    store.update_state("persist-test", WorkflowState.CODING)

    # Create a new store pointing to same dir
    new_store = StateStore(base_dir=store.base_dir)
    project = new_store.get_project("persist-test")
    assert project.state == WorkflowState.CODING
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/core/test_state_store.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/core/state_store.py`:
```python
"""Persistent state store for project workflow state."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class WorkflowState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DESIGNING = "designing"
    CODING = "coding"
    REVIEWING = "reviewing"
    DONE = "done"


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProjectState:
    """Full state of a project."""
    id: str
    state: WorkflowState = WorkflowState.IDLE
    requirement: str = ""
    agent_statuses: dict = field(default_factory=dict)
    iteration_count: int = 0
    max_iterations: int = 3
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    outputs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
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
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        return cls(
            id=data["id"],
            state=WorkflowState(data["state"]),
            requirement=data.get("requirement", ""),
            agent_statuses=data.get("agent_statuses", {}),
            iteration_count=data.get("iteration_count", 0),
            max_iterations=data.get("max_iterations", 3),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            outputs=data.get("outputs", {}),
        )


class StateStore:
    """Persistent JSON-based state store."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, ProjectState] = {}
        self._load_all()

    def _project_path(self, project_id: str) -> Path:
        return self.base_dir / f"{project_id}.json"

    def _load_all(self) -> None:
        """Load all persisted projects."""
        for file_path in self.base_dir.glob("*.json"):
            project_id = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._cache[project_id] = ProjectState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                continue

    def _save(self, project_id: str) -> None:
        """Persist a project to disk."""
        project = self._cache.get(project_id)
        if project:
            project.updated_at = datetime.utcnow().isoformat()
            with open(self._project_path(project_id), "w", encoding="utf-8") as f:
                json.dump(project.to_dict(), f, indent=2)

    def create_project(self, project_id: str, requirement: str = "") -> ProjectState:
        """Create a new project."""
        project = ProjectState(id=project_id, requirement=requirement)
        self._cache[project_id] = project
        self._save(project_id)
        return project

    def get_project(self, project_id: str) -> Optional[ProjectState]:
        """Get a project by ID."""
        return self._cache.get(project_id)

    def update_state(self, project_id: str, state: WorkflowState) -> None:
        """Update project workflow state."""
        if project_id in self._cache:
            self._cache[project_id].state = state
            self._save(project_id)

    def update_agent_status(self, project_id: str, agent_name: str, status: dict) -> None:
        """Update an agent's status."""
        if project_id in self._cache:
            self._cache[project_id].agent_statuses[agent_name] = status
            self._save(project_id)

    def increment_iteration(self, project_id: str) -> None:
        """Increment review iteration count."""
        if project_id in self._cache:
            self._cache[project_id].iteration_count += 1
            self._save(project_id)

    def update_output(self, project_id: str, key: str, value: str) -> None:
        """Store an agent's output."""
        if project_id in self._cache:
            self._cache[project_id].outputs[key] = value
            self._save(project_id)

    def list_projects(self) -> list[str]:
        """List all project IDs."""
        return list(self._cache.keys())
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/core/test_state_store.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/state_store.py tests/backend/core/test_state_store.py
git commit -m "feat: add persistent state store with JSON serialization"
```

---

## Phase 3: Agent Implementation

### Task 8: Agent Prompts

**Files:**
- Create: `backend/llm/prompts/pm.txt`
- Create: `backend/llm/prompts/architect.txt`
- Create: `backend/llm/prompts/coder.txt`
- Create: `backend/llm/prompts/reviewer.txt`

- [ ] **Step 1: Create all prompt files**

`backend/llm/prompts/pm.txt`:
```
You are a Product Manager. Your job is to analyze user requirements and produce a structured functional specification.

Analyze the following user requirement and produce a structured specification in Markdown format.

Your output must include:
1. **Overview** — Brief description of what the software does
2. **User Stories** — Who uses it and what they want to achieve (2-4 stories)
3. **Functional Requirements** — List of specific features/functions
4. **Non-Functional Requirements** — Performance, security, usability constraints
5. **Constraints** — Any limitations (technology, time, scope)
6. **Ambiguities** — Any unclear parts of the requirement that need clarification

If the requirement is ambiguous, mark it explicitly rather than guessing.

Output only the Markdown specification, no extra commentary.
```

`backend/llm/prompts/architect.txt`:
```
You are a Software Architect. Your job is to design the system architecture based on a functional specification.

Given the functional specification below, design a system architecture.

Your output must include:
1. **Module Overview** — List of modules/components and their responsibilities
2. **Module Interfaces** — For each module, define its public interface (functions/classes)
3. **Data Flow** — How data moves between modules (text description)
4. **Technology Recommendations** — Suggested programming language, frameworks, libraries
5. **File Structure** — Proposed directory/file structure for implementation

Keep the design practical and implementable by a single developer. Avoid over-engineering.

Output only the architecture document in Markdown, no extra commentary.
```

`backend/llm/prompts/coder.txt`:
```
You are a Software Developer. Your job is to write clean, working code.

You will be given:
1. A functional specification
2. An architecture design
{{#if review_feedback}}
3. Review feedback that needs to be addressed
{{/if}}

Generate the complete implementation code. Rules:
- Write complete, runnable code files
- Include proper error handling
- Add docstrings and comments where helpful
- Follow standard naming conventions
- Each file should be self-contained and functional

Format your output as follows for each file:

### FILE: path/to/file.py
\`\`\`python
# code here
\`\`\`

List all files needed for the project. Do not omit any files.
{{#if review_feedback}}
Address ALL review feedback items in your code.
{{/if}}
```

`backend/llm/prompts/reviewer.txt`:
```
You are a Code Reviewer. Your job is to review code for quality, correctness, and completeness.

Review the provided code against the functional specification and architecture design.

Check for:
1. **Functional Completeness** — Does it implement all requirements from the spec?
2. **Code Quality** — Readability, naming, comments, structure
3. **Bugs** — Logic errors, edge cases, null handling
4. **Architecture Compliance** — Does it follow the designed architecture?
5. **Security** — Input validation, injection risks, sensitive data handling

Output your review as JSON:

\`\`\`json
{
  "passed": false,
  "issues": [
    {
      "severity": "error|warning|suggestion",
      "file": "filename.py",
      "line": 15,
      "message": "Description of the issue",
      "suggestion": "How to fix it"
    }
  ],
  "summary": "Overall assessment"
}
\`\`\`

Set "passed" to true ONLY if there are no error-level issues and at most 2 warning-level issues.
```

- [ ] **Step 2: Commit**

```bash
git add backend/llm/prompts/
git commit -m "feat: add agent system prompts"
```

---

### Task 9: BaseAgent

**Files:**
- Create: `backend/agents/__init__.py`
- Create: `backend/agents/base_agent.py`
- Create: `tests/backend/agents/test_base_agent.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/agents/test_base_agent.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.base_agent import BaseAgent, AgentContext, AgentOutput
from backend.llm.client import LLMClient
from backend.llm.models import LLMResponse


class DummyAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentOutput:
        return AgentOutput(
            content="test output",
            files={"test.txt": "content"},
            metadata={"key": "value"}
        )


@pytest.mark.asyncio
async def test_base_agent_run():
    mock_llm = Mock(spec=LLMClient)
    agent = DummyAgent("test", mock_llm)

    context = AgentContext(requirement="test req", project_id="proj1")
    result = await agent.run(context)

    assert result.content == "test output"
    assert result.files == {"test.txt": "content"}
    assert result.metadata == {"key": "value"}


def test_base_agent_name():
    mock_llm = Mock(spec=LLMClient)
    agent = DummyAgent("my_agent", mock_llm)
    assert agent.name == "my_agent"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/agents/test_base_agent.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/agents/base_agent.py`:
```python
"""Base class for all Agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from backend.llm.client import LLMClient
from backend.llm.models import LLMConfig


@dataclass
class AgentContext:
    """Context passed to an Agent during execution."""
    requirement: str
    project_id: str
    spec: str = ""           # PM Agent output
    architecture: str = ""   # Architect Agent output
    code: dict = field(default_factory=dict)  # Coder Agent output: {filepath: content}
    review_feedback: str = ""  # Reviewer Agent output (for iteration)
    iteration: int = 0


@dataclass
class AgentOutput:
    """Output produced by an Agent."""
    content: str = ""           # Primary text output
    files: dict = field(default_factory=dict)  # Generated files: {filepath: content}
    metadata: dict = field(default_factory=dict)  # Additional metadata


class BaseAgent(ABC):
    """Abstract base class for all Agents."""

    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self.llm = llm_client

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentOutput:
        """Execute the Agent's task. Must be implemented by subclasses."""
        pass

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from file."""
        import os
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "llm", "prompts", f"{prompt_name}.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def _call_llm(self, system_prompt: str, user_prompt: str, model: str = "", temperature: float = 0.7) -> str:
        """Call LLM with standard configuration."""
        config = LLMConfig(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            max_tokens=4096,
            system_prompt=system_prompt,
        )
        response = await self.llm.call(user_prompt, config)
        return response.content
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/agents/test_base_agent.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/ tests/backend/agents/
git commit -m "feat: add BaseAgent abstract class with context and output models"
```

---

### Task 10: PMAgent

**Files:**
- Create: `backend/agents/pm_agent.py`
- Create: `tests/backend/agents/test_pm_agent.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/agents/test_pm_agent.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.pm_agent import PMAgent
from backend.agents.base_agent import AgentContext
from backend.llm.client import LLMClient
from backend.llm.models import LLMResponse


@pytest.mark.asyncio
async def test_pm_agent_generates_spec():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content="## Overview\nA todo app\n\n## User Stories\n...",
        model="claude-test"
    ))

    agent = PMAgent(mock_llm)
    context = AgentContext(requirement="Build a todo app", project_id="proj1")
    result = await agent.run(context)

    assert "Overview" in result.content
    assert result.metadata.get("agent_type") == "pm"
    # Verify LLM was called
    mock_llm.call.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/agents/test_pm_agent.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/agents/pm_agent.py`:
```python
"""PM Agent: Analyzes requirements and produces functional specifications."""

from backend.agents.base_agent import BaseAgent, AgentContext, AgentOutput


class PMAgent(BaseAgent):
    """Product Manager Agent that translates requirements into specs."""

    def __init__(self, llm_client):
        super().__init__("pm", llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Generate functional specification from requirement."""
        system_prompt = self._load_prompt("pm")
        user_prompt = f"User Requirement:\n{context.requirement}\n\nPlease analyze and produce a structured functional specification."

        spec = await self._call_llm(system_prompt, user_prompt, temperature=0.5)

        return AgentOutput(
            content=spec,
            metadata={"agent_type": "pm", "project_id": context.project_id}
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/agents/test_pm_agent.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agents/pm_agent.py tests/backend/agents/test_pm_agent.py
git commit -m "feat: add PM Agent for requirement analysis"
```

---

### Task 11: ArchitectAgent

**Files:**
- Create: `backend/agents/architect_agent.py`
- Create: `tests/backend/agents/test_architect_agent.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/agents/test_architect_agent.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.base_agent import AgentContext
from backend.llm.client import LLMClient
from backend.llm.models import LLMResponse


@pytest.mark.asyncio
async def test_architect_agent_generates_design():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content="## Module Overview\n- Main module\n\n## Interfaces\n...",
        model="claude-test"
    ))

    agent = ArchitectAgent(mock_llm)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj1",
        spec="## Overview\nA todo app"
    )
    result = await agent.run(context)

    assert "Module Overview" in result.content
    assert result.metadata.get("agent_type") == "architect"
```

- [ ] **Step 2: Write implementation**

`backend/agents/architect_agent.py`:
```python
"""Architect Agent: Designs system architecture from functional specifications."""

from backend.agents.base_agent import BaseAgent, AgentContext, AgentOutput


class ArchitectAgent(BaseAgent):
    """Software Architect Agent that designs system architecture."""

    def __init__(self, llm_client):
        super().__init__("architect", llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Generate architecture design from specification."""
        system_prompt = self._load_prompt("architect")
        user_prompt = f"""Functional Specification:
{context.spec}

Please design the system architecture based on this specification."""

        architecture = await self._call_llm(system_prompt, user_prompt, temperature=0.4)

        return AgentOutput(
            content=architecture,
            metadata={"agent_type": "architect", "project_id": context.project_id}
        )
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/backend/agents/test_architect_agent.py -v
```

Expected: PASS

```bash
git add backend/agents/architect_agent.py tests/backend/agents/test_architect_agent.py
git commit -m "feat: add Architect Agent for system design"
```

---

### Task 12: CoderAgent

**Files:**
- Create: `backend/agents/coder_agent.py`
- Create: `tests/backend/agents/test_coder_agent.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/agents/test_coder_agent.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.coder_agent import CoderAgent
from backend.agents.base_agent import AgentContext
from backend.llm.client import LLMClient
from backend.llm.models import LLMResponse


@pytest.mark.asyncio
async def test_coder_agent_generates_code():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content='### FILE: main.py\n```python\nprint("hello")\n```\n\n### FILE: utils.py\n```python\ndef helper():\n    pass\n```',
        model="claude-test"
    ))

    agent = CoderAgent(mock_llm)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj1",
        spec="## Overview\nA todo app",
        architecture="## Modules\n- main\n- utils"
    )
    result = await agent.run(context)

    assert "main.py" in result.files
    assert "utils.py" in result.files
    assert 'print("hello")' in result.files["main.py"]
    assert result.metadata.get("agent_type") == "coder"


@pytest.mark.asyncio
async def test_coder_agent_with_review_feedback():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content='### FILE: main.py\n```python\nprint("fixed")\n```',
        model="claude-test"
    ))

    agent = CoderAgent(mock_llm)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj1",
        spec="## Overview\nA todo app",
        architecture="## Modules\n- main",
        review_feedback="Fix the print statement",
        iteration=1
    )
    result = await agent.run(context)

    assert "main.py" in result.files
    # LLM should have been called with review feedback context
    call_args = mock_llm.call.call_args
    assert "Fix the print statement" in call_args[0][0] or "review" in call_args[0][0].lower()
```

- [ ] **Step 2: Write implementation**

`backend/agents/coder_agent.py`:
```python
"""Coder Agent: Generates implementation code from architecture design."""

import re

from backend.agents.base_agent import BaseAgent, AgentContext, AgentOutput


class CoderAgent(BaseAgent):
    """Software Developer Agent that writes code."""

    def __init__(self, llm_client):
        super().__init__("coder", llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Generate code from specification and architecture."""
        system_prompt = self._load_prompt("coder")

        user_prompt_parts = [
            f"Functional Specification:\n{context.spec}",
            f"\nArchitecture Design:\n{context.architecture}",
        ]

        if context.review_feedback:
            user_prompt_parts.append(f"\nReview Feedback (please address all issues):\n{context.review_feedback}")

        if context.iteration > 0:
            user_prompt_parts.append(f"\nThis is iteration {context.iteration}. Please carefully fix all issues.")

        user_prompt = "\n".join(user_prompt_parts)

        code_response = await self._call_llm(system_prompt, user_prompt, temperature=0.3)

        files = self._parse_code_files(code_response)

        return AgentOutput(
            content=code_response,
            files=files,
            metadata={
                "agent_type": "coder",
                "project_id": context.project_id,
                "iteration": context.iteration,
                "file_count": len(files),
            }
        )

    def _parse_code_files(self, response: str) -> dict[str, str]:
        """Parse FILE blocks from LLM response into {filepath: content} dict."""
        files = {}

        # Pattern: ### FILE: path/to/file.ext
        # followed by ```language
        # code
        # ```
        pattern = r'###\s*FILE:\s*([^\n]+)\n```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)

        for filepath, content in matches:
            filepath = filepath.strip()
            content = content.strip()
            if filepath and content:
                files[filepath] = content

        # Fallback: if no FILE blocks found, try simpler pattern
        if not files:
            pattern2 = r'```(?:\w+)?\n(.*?)```'
            matches2 = re.findall(pattern2, response, re.DOTALL)
            for i, content in enumerate(matches2):
                content = content.strip()
                if content:
                    files[f"file_{i+1}.py"] = content

        return files
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/backend/agents/test_coder_agent.py -v
```

Expected: PASS

```bash
git add backend/agents/coder_agent.py tests/backend/agents/test_coder_agent.py
git commit -m "feat: add Coder Agent with file parsing"
```

---

### Task 13: ReviewerAgent

**Files:**
- Create: `backend/agents/reviewer_agent.py`
- Create: `tests/backend/agents/test_reviewer_agent.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/agents/test_reviewer_agent.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.base_agent import AgentContext
from backend.llm.client import LLMClient
from backend.llm.models import LLMResponse


@pytest.mark.asyncio
async def test_reviewer_agent_with_issues():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content='```json\n{"passed": false, "issues": [{"severity": "error", "file": "main.py", "line": 1, "message": "Missing import", "suggestion": "Add import"}], "summary": "1 error found"}\n```',
        model="claude-test"
    ))

    agent = ReviewerAgent(mock_llm)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj1",
        spec="## Overview\nA todo app",
        architecture="## Modules\n- main",
        code={"main.py": "print('hello')"}
    )
    result = await agent.run(context)

    assert result.metadata.get("passed") is False
    assert len(result.metadata.get("issues", [])) == 1
    assert result.metadata.get("issues")[0]["severity"] == "error"


@pytest.mark.asyncio
async def test_reviewer_agent_passed():
    mock_llm = Mock(spec=LLMClient)
    mock_llm.call = AsyncMock(return_value=LLMResponse(
        content='```json\n{"passed": true, "issues": [], "summary": "All good"}\n```',
        model="claude-test"
    ))

    agent = ReviewerAgent(mock_llm)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj1",
        spec="## Overview\nA todo app",
        code={"main.py": "print('hello')"}
    )
    result = await agent.run(context)

    assert result.metadata.get("passed") is True
```

- [ ] **Step 2: Write implementation**

`backend/agents/reviewer_agent.py`:
```python
"""Reviewer Agent: Reviews code quality, correctness, and completeness."""

import json
import re

from backend.agents.base_agent import BaseAgent, AgentContext, AgentOutput


class ReviewerAgent(BaseAgent):
    """Code Reviewer Agent that checks code quality."""

    def __init__(self, llm_client):
        super().__init__("reviewer", llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Review code against specification and architecture."""
        system_prompt = self._load_prompt("reviewer")

        code_text = "\n\n".join(
            f"### {filepath}\n```\n{content}\n```"
            for filepath, content in context.code.items()
        )

        user_prompt = f"""Functional Specification:
{context.spec}

Architecture Design:
{context.architecture}

Code to Review:
{code_text}

Please review the code and provide your assessment."""

        review_response = await self._call_llm(system_prompt, user_prompt, temperature=0.3)

        review_data = self._parse_review(review_response)

        return AgentOutput(
            content=review_response,
            metadata={
                "agent_type": "reviewer",
                "project_id": context.project_id,
                "passed": review_data.get("passed", False),
                "issues": review_data.get("issues", []),
                "summary": review_data.get("summary", ""),
            }
        )

    def _parse_review(self, response: str) -> dict:
        """Parse JSON review from LLM response."""
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: return a default review if JSON parsing fails
            return {
                "passed": False,
                "issues": [{
                    "severity": "warning",
                    "message": f"Could not parse review JSON. Raw response: {response[:200]}..."
                }],
                "summary": "Review parsing failed"
            }
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/backend/agents/test_reviewer_agent.py -v
```

Expected: PASS

```bash
git add backend/agents/reviewer_agent.py tests/backend/agents/test_reviewer_agent.py
git commit -m "feat: add Reviewer Agent with JSON parsing"
```

---

## Phase 4: Orchestrator

### Task 14: State Machine

**Files:**
- Create: `backend/orchestrator/__init__.py`
- Create: `backend/orchestrator/state_machine.py`
- Create: `tests/backend/orchestrator/test_state_machine.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/orchestrator/test_state_machine.py`:
```python
import pytest

from backend.orchestrator.state_machine import StateMachine, WorkflowState, Transition


@pytest.fixture
def sm():
    return StateMachine()


def test_initial_state(sm):
    assert sm.current == WorkflowState.IDLE


def test_idle_to_planning(sm):
    assert sm.transition_to(WorkflowState.PLANNING) is True
    assert sm.current == WorkflowState.PLANNING


def test_planning_to_designing(sm):
    sm.transition_to(WorkflowState.PLANNING)
    assert sm.transition_to(WorkflowState.DESIGNING) is True


def test_designing_to_coding(sm):
    sm.transition_to(WorkflowState.PLANNING)
    sm.transition_to(WorkflowState.DESIGNING)
    assert sm.transition_to(WorkflowState.CODING) is True


def test_coding_to_reviewing(sm):
    sm.transition_to(WorkflowState.PLANNING)
    sm.transition_to(WorkflowState.DESIGNING)
    sm.transition_to(WorkflowState.CODING)
    assert sm.transition_to(WorkflowState.REVIEWING) is True


def test_reviewing_to_done(sm):
    sm.transition_to(WorkflowState.PLANNING)
    sm.transition_to(WorkflowState.DESIGNING)
    sm.transition_to(WorkflowState.CODING)
    sm.transition_to(WorkflowState.REVIEWING)
    assert sm.transition_to(WorkflowState.DONE) is True


def test_reviewing_back_to_coding(sm):
    sm.transition_to(WorkflowState.PLANNING)
    sm.transition_to(WorkflowState.DESIGNING)
    sm.transition_to(WorkflowState.CODING)
    sm.transition_to(WorkflowState.REVIEWING)
    assert sm.transition_to(WorkflowState.CODING) is True


def test_invalid_transition(sm):
    assert sm.transition_to(WorkflowState.DONE) is False
    assert sm.current == WorkflowState.IDLE


def test_review_loop_limit(sm):
    sm.transition_to(WorkflowState.PLANNING)
    sm.transition_to(WorkflowState.DESIGNING)
    sm.transition_to(WorkflowState.CODING)
    sm.transition_to(WorkflowState.REVIEWING)
    sm.transition_to(WorkflowState.CODING)
    sm.transition_to(WorkflowState.REVIEWING)
    sm.transition_to(WorkflowState.CODING)
    sm.transition_to(WorkflowState.REVIEWING)
    # 3rd review, should not allow going back to CODING
    assert sm.transition_to(WorkflowState.CODING) is False
    assert sm.transition_to(WorkflowState.DONE) is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/orchestrator/test_state_machine.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

`backend/orchestrator/state_machine.py`:
```python
"""Workflow state machine for multi-Agent orchestration."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class WorkflowState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DESIGNING = "designing"
    CODING = "coding"
    REVIEWING = "reviewing"
    DONE = "done"


@dataclass
class Transition:
    """A state transition."""
    from_state: WorkflowState
    to_state: WorkflowState
    condition: Optional[callable] = None


class StateMachine:
    """State machine for managing the DevAgent workflow."""

    # Valid transitions
    TRANSITIONS: list[Transition] = [
        Transition(WorkflowState.IDLE, WorkflowState.PLANNING),
        Transition(WorkflowState.PLANNING, WorkflowState.DESIGNING),
        Transition(WorkflowState.DESIGNING, WorkflowState.CODING),
        Transition(WorkflowState.CODING, WorkflowState.REVIEWING),
        Transition(WorkflowState.REVIEWING, WorkflowState.DONE),
        Transition(WorkflowState.REVIEWING, WorkflowState.CODING),
    ]

    def __init__(self, max_iterations: int = 3):
        self.current = WorkflowState.IDLE
        self.max_iterations = max_iterations
        self._review_count = 0
        self._history: list[WorkflowState] = []

    def transition_to(self, new_state: WorkflowState) -> bool:
        """Attempt to transition to a new state. Returns True if successful."""
        if self._is_valid_transition(new_state):
            self._history.append(self.current)
            self.current = new_state

            if new_state == WorkflowState.REVIEWING:
                self._review_count += 1

            return True
        return False

    def _is_valid_transition(self, new_state: WorkflowState) -> bool:
        """Check if a transition is valid."""
        # Check basic transition validity
        valid = any(
            t.from_state == self.current and t.to_state == new_state
            for t in self.TRANSITIONS
        )

        if not valid:
            return False

        # Special case: limit review iterations
        if self.current == WorkflowState.REVIEWING and new_state == WorkflowState.CODING:
            if self._review_count >= self.max_iterations:
                return False

        return True

    def can_iterate(self) -> bool:
        """Check if more review iterations are allowed."""
        return self._review_count < self.max_iterations

    def get_history(self) -> list[WorkflowState]:
        """Get state transition history."""
        return self._history.copy()

    def reset(self) -> None:
        """Reset to initial state."""
        self.current = WorkflowState.IDLE
        self._review_count = 0
        self._history = []
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/orchestrator/test_state_machine.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/orchestrator/ tests/backend/orchestrator/
git commit -m "feat: add workflow state machine with review loop limiting"
```

---

### Task 15: WebSocket Manager

**Files:**
- Create: `backend/orchestrator/websocket_manager.py`
- Create: `tests/backend/orchestrator/test_websocket_manager.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/orchestrator/test_websocket_manager.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock

from backend.orchestrator.websocket_manager import WebSocketManager


@pytest.fixture
def ws_manager():
    return WebSocketManager()


@pytest.mark.asyncio
async def test_connect_and_disconnect(ws_manager):
    mock_ws = Mock()
    mock_ws.accept = AsyncMock()

    await ws_manager.connect("proj1", mock_ws)
    assert "proj1" in ws_manager._connections

    await ws_manager.disconnect("proj1")
    assert "proj1" not in ws_manager._connections


@pytest.mark.asyncio
async def test_send_message(ws_manager):
    mock_ws = Mock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()

    await ws_manager.connect("proj1", mock_ws)
    await ws_manager.send_message("proj1", {"type": "test", "data": "hello"})

    mock_ws.send_json.assert_called_once_with({"type": "test", "data": "hello"})


@pytest.mark.asyncio
async def test_broadcast(ws_manager):
    mock_ws1 = Mock()
    mock_ws1.accept = AsyncMock()
    mock_ws1.send_json = AsyncMock()

    mock_ws2 = Mock()
    mock_ws2.accept = AsyncMock()
    mock_ws2.send_json = AsyncMock()

    await ws_manager.connect("proj1", mock_ws1)
    await ws_manager.connect("proj2", mock_ws2)

    await ws_manager.broadcast({"type": "announcement"})

    mock_ws1.send_json.assert_called_once()
    mock_ws2.send_json.assert_called_once()
```

- [ ] **Step 2: Write implementation**

`backend/orchestrator/websocket_manager.py`:
```python
"""WebSocket connection manager for real-time Agent status updates."""

from typing import Dict


class WebSocketManager:
    """Manages WebSocket connections by project ID."""

    def __init__(self):
        self._connections: Dict[str, object] = {}

    async def connect(self, project_id: str, websocket) -> None:
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        self._connections[project_id] = websocket

    async def disconnect(self, project_id: str) -> None:
        """Remove a WebSocket connection."""
        if project_id in self._connections:
            del self._connections[project_id]

    async def send_message(self, project_id: str, message: dict) -> None:
        """Send a message to a specific project's WebSocket."""
        ws = self._connections.get(project_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = []
        for project_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(project_id)

        for project_id in disconnected:
            await self.disconnect(project_id)
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/backend/orchestrator/test_websocket_manager.py -v
```

Expected: PASS

```bash
git add backend/orchestrator/websocket_manager.py tests/backend/orchestrator/test_websocket_manager.py
git commit -m "feat: add WebSocket connection manager"
```

---

### Task 16: Scheduler

**Files:**
- Create: `backend/orchestrator/scheduler.py`
- Create: `tests/backend/orchestrator/test_scheduler.py`

- [ ] **Step 1: Write the failing test**

`tests/backend/orchestrator/test_scheduler.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.orchestrator.scheduler import AgentScheduler
from backend.orchestrator.state_machine import WorkflowState


@pytest.fixture
def scheduler():
    mock_llm = Mock()
    mock_ws = Mock()
    mock_store = Mock()
    return AgentScheduler(llm_client=mock_llm, ws_manager=mock_ws, state_store=mock_store)


@pytest.mark.asyncio
async def test_schedule_pm_agent(scheduler):
    with patch("backend.orchestrator.scheduler.PMAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = AsyncMock(return_value=Mock(content="spec output", files={}, metadata={}))

        result = await scheduler.run_agent("pm", Mock(), "proj1")

        assert result.content == "spec output"
        MockAgent.assert_called_once()


@pytest.mark.asyncio
async def test_schedule_invalid_agent(scheduler):
    with pytest.raises(ValueError, match="Unknown agent"):
        await scheduler.run_agent("unknown", Mock(), "proj1")
```

- [ ] **Step 2: Write implementation**

`backend/orchestrator/scheduler.py`:
```python
"""Agent scheduler that instantiates and runs Agents."""

from backend.agents.base_agent import AgentContext
from backend.agents.pm_agent import PMAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.coder_agent import CoderAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.llm.client import LLMClient


class AgentScheduler:
    """Schedules and executes Agents based on workflow state."""

    AGENT_MAP = {
        "pm": PMAgent,
        "architect": ArchitectAgent,
        "coder": CoderAgent,
        "reviewer": ReviewerAgent,
    }

    def __init__(self, llm_client: LLMClient, ws_manager, state_store):
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.state_store = state_store

    async def run_agent(self, agent_name: str, context: AgentContext, project_id: str):
        """Run an Agent and return its output."""
        agent_class = self.AGENT_MAP.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = agent_class(self.llm_client)

        # Update status to running
        await self._notify_status(project_id, agent_name, "running")

        try:
            result = await agent.run(context)
            await self._notify_status(project_id, agent_name, "completed", result)
            return result
        except Exception as e:
            await self._notify_status(project_id, agent_name, "failed", error=str(e))
            raise

    async def _notify_status(self, project_id: str, agent_name: str, status: str, output=None, error=None):
        """Send status update via WebSocket."""
        message = {
            "type": "agent_status",
            "project_id": project_id,
            "agent": agent_name,
            "status": status,
        }

        if output:
            message["output"] = {
                "summary": output.content[:200] if output.content else "",
                "files": list(output.files.keys()) if output.files else [],
                "metadata": output.metadata,
            }

        if error:
            message["error"] = error

        await self.ws_manager.send_message(project_id, message)

        # Also update state store
        if self.state_store:
            self.state_store.update_agent_status(project_id, agent_name, {"status": status})
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/backend/orchestrator/test_scheduler.py -v
```

Expected: PASS

```bash
git add backend/orchestrator/scheduler.py tests/backend/orchestrator/test_scheduler.py
git commit -m "feat: add agent scheduler with websocket status updates"
```

---

## Phase 5: FastAPI Integration

### Task 17: FastAPI Main Application

**Files:**
- Create: `backend/main.py`
- Modify: `requirements.txt` (add `python-dotenv`)

- [ ] **Step 1: Add python-dotenv to requirements**

Add `python-dotenv>=1.0.0` to `requirements.txt`.

- [ ] **Step 2: Write FastAPI app**

`backend/main.py`:
```python
"""FastAPI application entry point."""

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.llm.client import LLMClient
from backend.core.state_store import StateStore
from backend.tools.file_manager import FileManager
from backend.orchestrator.state_machine import StateMachine, WorkflowState
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.orchestrator.scheduler import AgentScheduler
from backend.agents.base_agent import AgentContext


# Global instances
llm_client: LLMClient = None
state_store: StateStore = None
ws_manager: WebSocketManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global llm_client, state_store, ws_manager

    llm_client = LLMClient(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
    )
    state_store = StateStore(base_dir=os.path.join(settings.output_dir, "states"))
    ws_manager = WebSocketManager()

    yield

    # Cleanup
    pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
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


# REST Endpoints

@app.post("/api/projects", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Create a new project and start the workflow."""
    project_id = str(uuid.uuid4())[:8]

    # Create project in state store
    state_store.create_project(project_id, request.requirement)

    # Start workflow asynchronously
    import asyncio
    asyncio.create_task(_run_workflow(project_id, request.requirement))

    return CreateProjectResponse(project_id=project_id, state="planning")


@app.get("/api/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project(project_id: str):
    """Get project status."""
    project = state_store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    return {"files": fm.list_files()}


@app.get("/api/projects/{project_id}/files/{file_path:path}")
async def get_project_file(project_id: str, file_path: str):
    """Get content of a specific file."""
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
    if not fm.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": fm.read_file(file_path)}


# WebSocket Endpoint

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket for real-time updates."""
    await ws_manager.connect(project_id, websocket)
    try:
        while True:
            # Keep connection alive, handle client messages if needed
            data = await websocket.receive_text()
            # Echo or handle commands
    except WebSocketDisconnect:
        await ws_manager.disconnect(project_id)


# Workflow execution

async def _run_workflow(project_id: str, requirement: str):
    """Execute the full DevAgent workflow."""
    scheduler = AgentScheduler(llm_client, ws_manager, state_store)
    sm = StateMachine(max_iterations=settings.max_review_iterations)
    fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))

    # Context that accumulates outputs
    context = AgentContext(requirement=requirement, project_id=project_id)

    try:
        # IDLE -> PLANNING
        sm.transition_to(WorkflowState.PLANNING)
        state_store.update_state(project_id, WorkflowState.PLANNING)
        await _notify_workflow_state(project_id, sm)

        pm_output = await scheduler.run_agent("pm", context, project_id)
        context.spec = pm_output.content
        fm.write_file("spec.md", pm_output.content)
        state_store.update_output(project_id, "spec", pm_output.content)

        # PLANNING -> DESIGNING
        sm.transition_to(WorkflowState.DESIGNING)
        state_store.update_state(project_id, WorkflowState.DESIGNING)
        await _notify_workflow_state(project_id, sm)

        architect_output = await scheduler.run_agent("architect", context, project_id)
        context.architecture = architect_output.content
        fm.write_file("architecture.md", architect_output.content)
        state_store.update_output(project_id, "architecture", architect_output.content)

        # DESIGNING -> CODING (first pass)
        sm.transition_to(WorkflowState.CODING)
        state_store.update_state(project_id, WorkflowState.CODING)
        await _notify_workflow_state(project_id, sm)

        # Review loop
        review_passed = False
        while not review_passed:
            coder_output = await scheduler.run_agent("coder", context, project_id)
            context.code = coder_output.files

            # Write all generated files
            for filepath, content in coder_output.files.items():
                fm.write_file(filepath, content)

            # CODING -> REVIEWING
            sm.transition_to(WorkflowState.REVIEWING)
            state_store.update_state(project_id, WorkflowState.REVIEWING)
            await _notify_workflow_state(project_id, sm)

            reviewer_output = await scheduler.run_agent("reviewer", context, project_id)
            review_passed = reviewer_output.metadata.get("passed", False)

            fm.write_file("review.md", reviewer_output.content)
            state_store.update_output(project_id, "review", reviewer_output.content)

            if not review_passed and sm.can_iterate():
                context.review_feedback = reviewer_output.content
                context.iteration = sm._review_count
                state_store.increment_iteration(project_id)

                # REVIEWING -> CODING (iterate)
                sm.transition_to(WorkflowState.CODING)
                state_store.update_state(project_id, WorkflowState.CODING)
                await _notify_workflow_state(project_id, sm)
            else:
                break

        # Done
        sm.transition_to(WorkflowState.DONE)
        state_store.update_state(project_id, WorkflowState.DONE)
        await _notify_workflow_state(project_id, sm)

    except Exception as e:
        import logging
        logging.error(f"Workflow failed for {project_id}: {e}")
        await ws_manager.send_message(project_id, {
            "type": "error",
            "project_id": project_id,
            "message": str(e),
        })


async def _notify_workflow_state(project_id: str, sm: StateMachine):
    """Send workflow state update."""
    await ws_manager.send_message(project_id, {
        "type": "workflow_state",
        "project_id": project_id,
        "state": sm.current.value,
        "overall_progress": _calculate_progress(sm),
        "iteration_count": sm._review_count,
    })


def _calculate_progress(sm: StateMachine) -> int:
    """Calculate overall workflow progress percentage."""
    progress_map = {
        WorkflowState.IDLE: 0,
        WorkflowState.PLANNING: 10,
        WorkflowState.DESIGNING: 30,
        WorkflowState.CODING: 50,
        WorkflowState.REVIEWING: 80,
        WorkflowState.DONE: 100,
    }
    return progress_map.get(sm.current, 0)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 3: Commit**

```bash
git add backend/main.py requirements.txt
git commit -m "feat: add FastAPI app with REST and WebSocket endpoints"
```

---

## Phase 6: Frontend

### Task 18: Frontend Project Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/main.tsx`

- [ ] **Step 1: Create all frontend config files**

`frontend/package.json`:
```json
{
  "name": "devagent-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^4.5.2",
    "@codemirror/lang-python": "^6.1.6",
    "@codemirror/lang-javascript": "^6.2.2",
    "@codemirror/theme-one-dark": "^6.1.2",
    "@uiw/react-codemirror": "^4.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.5",
    "vite": "^5.2.12"
  }
}
```

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

`frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`frontend/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

`frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DevAgent Team</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

`frontend/src/vite-env.d.ts`:
```typescript
/// <reference types="vite/client" />
```

`frontend/src/main.tsx`:
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/theme.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install
```

Expected: installs without errors

- [ ] **Step 3: Commit**

```bash
cd /Users/lanhezheng/vibe-agent
git add frontend/
git commit -m "feat: setup React frontend with Vite and TypeScript"
```

---

### Task 19: Types and Theme

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/styles/theme.css`

- [ ] **Step 1: Create types**

`frontend/src/types/index.ts`:
```typescript
export interface AgentStatus {
  agent: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  output?: {
    summary?: string;
    files?: string[];
    metadata?: Record<string, unknown>;
  };
  error?: string;
}

export interface WorkflowState {
  project_id: string;
  state: 'idle' | 'planning' | 'designing' | 'coding' | 'reviewing' | 'done';
  overall_progress: number;
  iteration_count: number;
}

export interface ReviewIssue {
  severity: 'error' | 'warning' | 'suggestion';
  file?: string;
  line?: number;
  message: string;
  suggestion?: string;
}

export interface Project {
  project_id: string;
  state: string;
  agent_statuses: Record<string, unknown>;
  iteration_count: number;
  outputs: Record<string, string>;
}

export interface WebSocketMessage {
  type: 'agent_status' | 'workflow_state' | 'error';
  project_id: string;
  [key: string]: unknown;
}
```

- [ ] **Step 2: Create theme CSS**

`frontend/src/styles/theme.css`:
```css
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --bg-hover: #2d333b;
  --border-color: #30363d;
  --border-light: #484f58;

  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --text-muted: #6e7681;

  --accent-blue: #58a6ff;
  --accent-green: #238636;
  --accent-yellow: #d29922;
  --accent-red: #da3633;
  --accent-purple: #8957e5;

  --font-mono: 'SFMono-Regular', 'Consolas', 'Monaco', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  --sidebar-width: 240px;
  --agent-panel-width: 360px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

#root {
  height: 100vh;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-light);
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/ frontend/src/styles/
git commit -m "feat: add TypeScript types and Codex-style theme"
```

---

### Task 20: Zustand Store

**Files:**
- Create: `frontend/src/store/useStore.ts`

- [ ] **Step 1: Write store**

`frontend/src/store/useStore.ts`:
```typescript
import { create } from 'zustand';
import type { AgentStatus, WorkflowState, Project } from '../types';

interface AppState {
  // Project
  currentProject: Project | null;
  projectId: string | null;

  // Agents
  agentStatuses: Record<string, AgentStatus>;

  // Workflow
  workflowState: WorkflowState | null;

  // Files
  files: string[];
  currentFile: string | null;
  fileContent: string;

  // UI
  isConnected: boolean;
  isRunning: boolean;

  // Actions
  setProject: (project: Project | null) => void;
  setProjectId: (id: string | null) => void;
  setAgentStatus: (status: AgentStatus) => void;
  setWorkflowState: (state: WorkflowState) => void;
  setFiles: (files: string[]) => void;
  setCurrentFile: (file: string | null) => void;
  setFileContent: (content: string) => void;
  setConnected: (connected: boolean) => void;
  setRunning: (running: boolean) => void;
  reset: () => void;
}

const initialState = {
  currentProject: null,
  projectId: null,
  agentStatuses: {},
  workflowState: null,
  files: [],
  currentFile: null,
  fileContent: '',
  isConnected: false,
  isRunning: false,
};

export const useStore = create<AppState>((set) => ({
  ...initialState,

  setProject: (project) => set({ currentProject: project }),
  setProjectId: (id) => set({ projectId: id }),

  setAgentStatus: (status) =>
    set((state) => ({
      agentStatuses: {
        ...state.agentStatuses,
        [status.agent]: status,
      },
    })),

  setWorkflowState: (workflowState) => set({ workflowState }),

  setFiles: (files) => set({ files }),
  setCurrentFile: (currentFile) => set({ currentFile }),
  setFileContent: (fileContent) => set({ fileContent }),

  setConnected: (isConnected) => set({ isConnected }),
  setRunning: (isRunning) => set({ isRunning }),

  reset: () => set(initialState),
}));
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/store/
git commit -m "feat: add Zustand store for global state management"
```

---

### Task 21: Layout Component

**Files:**
- Create: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Write Layout component**

`frontend/src/components/Layout.tsx`:
```typescript
import React from 'react';

interface LayoutProps {
  sidebar: React.ReactNode;
  editor: React.ReactNode;
  agentPanel: React.ReactNode;
}

const layoutStyles = {
  container: {
    display: 'flex',
    height: '100vh',
    background: 'var(--bg-primary)',
    overflow: 'hidden',
  } as React.CSSProperties,
  sidebar: {
    width: 'var(--sidebar-width)',
    minWidth: '200px',
    borderRight: '1px solid var(--border-color)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  } as React.CSSProperties,
  editor: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    minWidth: 0,
  } as React.CSSProperties,
  agentPanel: {
    width: 'var(--agent-panel-width)',
    minWidth: '280px',
    borderLeft: '1px solid var(--border-color)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  } as React.CSSProperties,
  header: {
    height: '48px',
    borderBottom: '1px solid var(--border-color)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 16px',
    gap: '12px',
    background: 'var(--bg-secondary)',
  } as React.CSSProperties,
  logo: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--accent-blue)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  } as React.CSSProperties,
  title: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    flex: 1,
  } as React.CSSProperties,
  content: {
    flex: 1,
    overflow: 'auto',
  } as React.CSSProperties,
};

export default function Layout({ sidebar, editor, agentPanel }: LayoutProps) {
  return (
    <div style={layoutStyles.container}>
      <div style={layoutStyles.sidebar}>
        <div style={layoutStyles.header}>
          <div style={layoutStyles.logo}>
            <span>🤖</span>
            <span>DevAgent</span>
          </div>
        </div>
        <div style={layoutStyles.content}>{sidebar}</div>
      </div>

      <div style={layoutStyles.editor}>
        <div style={layoutStyles.header}>
          <span style={layoutStyles.title}>Code Editor</span>
        </div>
        <div style={layoutStyles.content}>{editor}</div>
      </div>

      <div style={layoutStyles.agentPanel}>
        <div style={layoutStyles.header}>
          <span style={layoutStyles.title}>Agent Workspace</span>
        </div>
        <div style={layoutStyles.content}>{agentPanel}</div>
      </div>
    </div>
  );
}
```

Note: Using 🚀 emoji is only for the logo/brand context which matches Codex style.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat: add three-pane Layout component"
```

---

### Task 22: FileTree Component

**Files:**
- Create: `frontend/src/components/FileTree.tsx`

- [ ] **Step 1: Write FileTree component**

`frontend/src/components/FileTree.tsx`:
```typescript
import React from 'react';
import { useStore } from '../store/useStore';

const treeStyles = {
  container: {
    padding: '8px 0',
    fontSize: '13px',
    fontFamily: 'var(--font-sans)',
  } as React.CSSProperties,
  folder: {
    padding: '4px 12px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: 'var(--text-primary)',
    userSelect: 'none',
  } as React.CSSProperties,
  file: {
    padding: '4px 12px 4px 28px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: 'var(--text-secondary)',
    fontSize: '12px',
  } as React.CSSProperties,
  fileActive: {
    background: 'var(--bg-tertiary)',
    color: 'var(--text-primary)',
  } as React.CSSProperties,
  icon: {
    fontSize: '14px',
    width: '16px',
    textAlign: 'center',
  } as React.CSSProperties,
  empty: {
    padding: '16px',
    color: 'var(--text-muted)',
    fontSize: '12px',
    textAlign: 'center',
  } as React.CSSProperties,
};

function getFileIcon(filename: string): string {
  if (filename.endsWith('.py')) return '🐍';
  if (filename.endsWith('.js') || filename.endsWith('.ts')) return '📜';
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.md')) return '📝';
  if (filename.endsWith('.html')) return '🌐';
  if (filename.endsWith('.css')) return '🎨';
  return '📄';
}

export default function FileTree() {
  const { files, currentFile, setCurrentFile } = useStore();

  if (files.length === 0) {
    return (
      <div style={treeStyles.container}>
        <div style={treeStyles.empty}>No files yet</div>
      </div>
    );
  }

  return (
    <div style={treeStyles.container}>
      {files.map((file) => {
        const isActive = currentFile === file;
        const fileStyle = isActive
          ? { ...treeStyles.file, ...treeStyles.fileActive }
          : treeStyles.file;

        return (
          <div
            key={file}
            style={fileStyle}
            onClick={() => setCurrentFile(file)}
          >
            <span style={treeStyles.icon}>{getFileIcon(file)}</span>
            <span>{file}</span>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/FileTree.tsx
git commit -m "feat: add FileTree component with file icons"
```

---

### Task 23: CodeEditor Component

**Files:**
- Create: `frontend/src/components/CodeEditor.tsx`

- [ ] **Step 1: Write CodeEditor component**

`frontend/src/components/CodeEditor.tsx`:
```typescript
import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { oneDark } from '@codemirror/theme-one-dark';
import { useStore } from '../store/useStore';

const editorStyles = {
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  } as React.CSSProperties,
  tabBar: {
    height: '36px',
    background: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border-color)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 12px',
    gap: '4px',
  } as React.CSSProperties,
  tab: {
    padding: '6px 12px',
    fontSize: '12px',
    color: 'var(--text-secondary)',
    background: 'var(--bg-tertiary)',
    borderRadius: '4px 4px 0 0',
    border: '1px solid var(--border-color)',
    borderBottom: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  } as React.CSSProperties,
  empty: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--text-muted)',
    fontSize: '14px',
  } as React.CSSProperties,
};

function getLanguageExtension(filename: string) {
  if (filename.endsWith('.py')) return python();
  if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx')) return javascript();
  return [];
}

export default function CodeEditor() {
  const { currentFile, fileContent } = useStore();

  if (!currentFile) {
    return (
      <div style={editorStyles.container}>
        <div style={editorStyles.empty}>
          Select a file to view its contents
        </div>
      </div>
    );
  }

  return (
    <div style={editorStyles.container}>
      <div style={editorStyles.tabBar}>
        <div style={editorStyles.tab}>
          <span>📄</span>
          <span>{currentFile}</span>
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <CodeMirror
          value={fileContent}
          height="100%"
          theme={oneDark}
          extensions={getLanguageExtension(currentFile)}
          editable={false}
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            highlightActiveLine: true,
            foldGutter: false,
          }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/CodeEditor.tsx
git commit -m "feat: add CodeMirror-based CodeEditor component"
```

---

### Task 24: AgentCard and AgentPanel

**Files:**
- Create: `frontend/src/components/AgentCard.tsx`
- Create: `frontend/src/components/AgentPanel.tsx`
- Create: `frontend/src/components/ProgressBar.tsx`

- [ ] **Step 1: Write AgentCard**

`frontend/src/components/AgentCard.tsx`:
```typescript
import React from 'react';
import type { AgentStatus } from '../types';

interface AgentCardProps {
  status: AgentStatus;
}

const cardStyles = {
  container: {
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
    marginBottom: '8px',
  } as React.CSSProperties,
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '8px',
  } as React.CSSProperties,
  name: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  } as React.CSSProperties,
  status: {
    fontSize: '11px',
    padding: '2px 8px',
    borderRadius: '10px',
    fontWeight: 500,
  } as React.CSSProperties,
  statusRunning: {
    background: 'rgba(88, 166, 255, 0.15)',
    color: 'var(--accent-blue)',
  } as React.CSSProperties,
  statusCompleted: {
    background: 'rgba(35, 134, 54, 0.15)',
    color: 'var(--accent-green)',
  } as React.CSSProperties,
  statusFailed: {
    background: 'rgba(218, 54, 51, 0.15)',
    color: 'var(--accent-red)',
  } as React.CSSProperties,
  statusIdle: {
    background: 'rgba(110, 118, 129, 0.15)',
    color: 'var(--text-muted)',
  } as React.CSSProperties,
  summary: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    lineHeight: 1.5,
  } as React.CSSProperties,
  files: {
    marginTop: '8px',
    fontSize: '11px',
    color: 'var(--text-muted)',
  } as React.CSSProperties,
};

function getStatusStyle(status: string) {
  switch (status) {
    case 'running': return { ...cardStyles.status, ...cardStyles.statusRunning };
    case 'completed': return { ...cardStyles.status, ...cardStyles.statusCompleted };
    case 'failed': return { ...cardStyles.status, ...cardStyles.statusFailed };
    default: return { ...cardStyles.status, ...cardStyles.statusIdle };
  }
}

const agentNames: Record<string, string> = {
  pm: 'PM Agent',
  architect: 'Architect Agent',
  coder: 'Coder Agent',
  reviewer: 'Reviewer Agent',
};

export default function AgentCard({ status }: AgentCardProps) {
  return (
    <div style={cardStyles.container}>
      <div style={cardStyles.header}>
        <span style={cardStyles.name}>{agentNames[status.agent] || status.agent}</span>
        <span style={getStatusStyle(status.status)}>
          {status.status === 'idle' ? 'Waiting' : status.status}
        </span>
      </div>
      {status.output?.summary && (
        <div style={cardStyles.summary}>{status.output.summary}</div>
      )}
      {status.output?.files && status.output.files.length > 0 && (
        <div style={cardStyles.files}>
          Files: {status.output.files.join(', ')}
        </div>
      )}
      {status.error && (
        <div style={{ ...cardStyles.summary, color: 'var(--accent-red)' }}>
          Error: {status.error}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write ProgressBar**

`frontend/src/components/ProgressBar.tsx`:
```typescript
import React from 'react';

interface ProgressBarProps {
  progress: number;
  label?: string;
}

const progressStyles = {
  container: {
    padding: '12px',
    borderTop: '1px solid var(--border-color)',
  } as React.CSSProperties,
  label: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    marginBottom: '8px',
    display: 'flex',
    justifyContent: 'space-between',
  } as React.CSSProperties,
  barBg: {
    height: '6px',
    background: 'var(--bg-tertiary)',
    borderRadius: '3px',
    overflow: 'hidden',
  } as React.CSSProperties,
  barFill: {
    height: '100%',
    background: 'var(--accent-blue)',
    borderRadius: '3px',
    transition: 'width 0.5s ease',
  } as React.CSSProperties,
};

export default function ProgressBar({ progress, label }: ProgressBarProps) {
  return (
    <div style={progressStyles.container}>
      <div style={progressStyles.label}>
        <span>{label || 'Overall Progress'}</span>
        <span>{progress}%</span>
      </div>
      <div style={progressStyles.barBg}>
        <div style={{ ...progressStyles.barFill, width: `${progress}%` }} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write AgentPanel**

`frontend/src/components/AgentPanel.tsx`:
```typescript
import React from 'react';
import { useStore } from '../store/useStore';
import AgentCard from './AgentCard';
import ProgressBar from './ProgressBar';

const panelStyles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  } as React.CSSProperties,
  scrollArea: {
    flex: 1,
    overflow: 'auto',
    padding: '12px',
  } as React.CSSProperties,
  sectionTitle: {
    fontSize: '11px',
    textTransform: 'uppercase' as const,
    color: 'var(--text-muted)',
    marginBottom: '8px',
    letterSpacing: '0.5px',
  } as React.CSSProperties,
  empty: {
    padding: '24px',
    color: 'var(--text-muted)',
    fontSize: '13px',
    textAlign: 'center',
  } as React.CSSProperties,
};

const AGENT_ORDER = ['pm', 'architect', 'coder', 'reviewer'];

export default function AgentPanel() {
  const { agentStatuses, workflowState } = useStore();

  const progress = workflowState?.overall_progress || 0;
  const iterationCount = workflowState?.iteration_count || 0;

  return (
    <div style={panelStyles.container}>
      <div style={panelStyles.scrollArea}>
        <div style={panelStyles.sectionTitle}>Agents</div>

        {AGENT_ORDER.length === 0 ? (
          <div style={panelStyles.empty}>
            Start a project to see Agents in action
          </div>
        ) : (
          AGENT_ORDER.map((agentName) => {
            const status = agentStatuses[agentName] || {
              agent: agentName,
              status: 'idle',
              progress: 0,
            };
            return <AgentCard key={agentName} status={status} />;
          })
        )}

        {iterationCount > 0 && (
          <div style={{
            ...panelStyles.sectionTitle,
            marginTop: '12px',
            color: 'var(--accent-yellow)',
          }}>
            Review Iterations: {iterationCount}
          </div>
        )}
      </div>

      <ProgressBar progress={progress} />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AgentCard.tsx frontend/src/components/AgentPanel.tsx frontend/src/components/ProgressBar.tsx
git commit -m "feat: add AgentPanel, AgentCard, and ProgressBar components"
```

---

### Task 25: ChatInput Component

**Files:**
- Create: `frontend/src/components/ChatInput.tsx`

- [ ] **Step 1: Write ChatInput**

`frontend/src/components/ChatInput.tsx`:
```typescript
import React, { useState } from 'react';
import { useStore } from '../store/useStore';

const inputStyles = {
  container: {
    padding: '12px',
    borderTop: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
  } as React.CSSProperties,
  textarea: {
    width: '100%',
    minHeight: '60px',
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid var(--border-color)',
    background: 'var(--bg-tertiary)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    fontFamily: 'var(--font-sans)',
    resize: 'vertical' as const,
    outline: 'none',
  } as React.CSSProperties,
  buttonRow: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginTop: '8px',
    gap: '8px',
  } as React.CSSProperties,
  button: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    background: 'var(--accent-green)',
    color: '#fff',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    opacity: 1,
    transition: 'opacity 0.2s',
  } as React.CSSProperties,
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  } as React.CSSProperties,
  status: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  } as React.CSSProperties,
  connected: {
    color: 'var(--accent-green)',
  } as React.CSSProperties,
  disconnected: {
    color: 'var(--accent-red)',
  } as React.CSSProperties,
};

interface ChatInputProps {
  onSubmit: (requirement: string) => void;
}

export default function ChatInput({ onSubmit }: ChatInputProps) {
  const [requirement, setRequirement] = useState('');
  const { isConnected, isRunning } = useStore();

  const handleSubmit = () => {
    if (requirement.trim() && !isRunning) {
      onSubmit(requirement.trim());
      setRequirement('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };

  const buttonStyle = isRunning
    ? { ...inputStyles.button, ...inputStyles.buttonDisabled }
    : inputStyles.button;

  return (
    <div style={inputStyles.container}>
      <div style={inputStyles.status}>
        <span style={isConnected ? inputStyles.connected : inputStyles.disconnected}>
          {isConnected ? '🟢' : '🔴'}
        </span>
        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        {isRunning && <span> | Running...</span>}
      </div>
      <textarea
        style={inputStyles.textarea}
        placeholder="Describe your project requirement... (Cmd+Enter to submit)"
        value={requirement}
        onChange={(e) => setRequirement(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isRunning}
      />
      <div style={inputStyles.buttonRow}>
        <button
          style={buttonStyle}
          onClick={handleSubmit}
          disabled={isRunning || !requirement.trim()}
        >
          {isRunning ? 'Running...' : 'Start Project'}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatInput.tsx
git commit -m "feat: add ChatInput component for requirement submission"
```

---

### Task 26: WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Write useWebSocket hook**

`frontend/src/hooks/useWebSocket.ts`:
```typescript
import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';
import type { WebSocketMessage } from '../types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const {
    projectId,
    setConnected,
    setRunning,
    setAgentStatus,
    setWorkflowState,
  } = useStore();

  const connect = useCallback(() => {
    if (!projectId) return;

    const wsUrl = `ws://localhost:8000/ws/${projectId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleMessage(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect with backoff
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [projectId]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'agent_status':
        setAgentStatus({
          agent: message.agent as string,
          status: message.status as 'idle' | 'running' | 'completed' | 'failed',
          progress: 0,
          output: message.output as Record<string, unknown>,
          error: message.error as string | undefined,
        });
        if (message.status === 'running') {
          setRunning(true);
        }
        break;

      case 'workflow_state':
        setWorkflowState({
          project_id: message.project_id as string,
          state: message.state as 'idle' | 'planning' | 'designing' | 'coding' | 'reviewing' | 'done',
          overall_progress: message.overall_progress as number,
          iteration_count: message.iteration_count as number,
        });
        if (message.state === 'done') {
          setRunning(false);
        }
        break;

      case 'error':
        console.error('Workflow error:', message.message);
        setRunning(false);
        break;
    }
  }, []);

  useEffect(() => {
    if (projectId) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [projectId, connect]);

  return { connect };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts
git commit -m "feat: add WebSocket hook with auto-reconnect"
```

---

### Task 27: App Component

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write App component**

`frontend/src/App.tsx`:
```typescript
import React, { useCallback, useEffect } from 'react';
import Layout from './components/Layout';
import FileTree from './components/FileTree';
import CodeEditor from './components/CodeEditor';
import AgentPanel from './components/AgentPanel';
import ChatInput from './components/ChatInput';
import { useStore } from './store/useStore';
import { useWebSocket } from './hooks/useWebSocket';

const appStyles = {
  chatContainer: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  } as React.CSSProperties,
  scrollArea: {
    flex: 1,
    overflow: 'auto',
  } as React.CSSProperties,
};

export default function App() {
  const {
    projectId,
    setProjectId,
    setProject,
    setFiles,
    setFileContent,
    currentFile,
    reset,
  } = useStore();

  useWebSocket();

  // Fetch file content when currentFile changes
  useEffect(() => {
    if (projectId && currentFile) {
      fetch(`/api/projects/${projectId}/files/${currentFile}`)
        .then((res) => res.json())
        .then((data) => setFileContent(data.content))
        .catch((err) => console.error('Failed to fetch file:', err));
    }
  }, [projectId, currentFile]);

  // Fetch file list periodically when running
  useEffect(() => {
    if (!projectId) return;

    const interval = setInterval(() => {
      fetch(`/api/projects/${projectId}/files`)
        .then((res) => res.json())
        .then((data) => setFiles(data.files))
        .catch(() => {});
    }, 2000);

    return () => clearInterval(interval);
  }, [projectId]);

  const handleSubmit = useCallback(async (requirement: string) => {
    reset();

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirement }),
      });

      const data = await response.json();
      setProjectId(data.project_id);
      setProject({
        project_id: data.project_id,
        state: data.state,
        agent_statuses: {},
        iteration_count: 0,
        outputs: {},
      });
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  }, []);

  const sidebar = (
    <div style={appStyles.chatContainer}>
      <div style={appStyles.scrollArea}>
        <FileTree />
      </div>
      <ChatInput onSubmit={handleSubmit} />
    </div>
  );

  return (
    <Layout
      sidebar={sidebar}
      editor={<CodeEditor />}
      agentPanel={<AgentPanel />}
    />
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add App component wiring everything together"
```

---

## Phase 7: Integration & Polish

### Task 28: Add ReviewReport Component

**Files:**
- Create: `frontend/src/components/ReviewReport.tsx`

- [ ] **Step 1: Write ReviewReport**

`frontend/src/components/ReviewReport.tsx`:
```typescript
import React from 'react';
import { useStore } from '../store/useStore';
import type { ReviewIssue } from '../types';

const reportStyles = {
  container: {
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--border-color)',
    background: 'var(--bg-secondary)',
    marginBottom: '8px',
  } as React.CSSProperties,
  title: {
    fontSize: '13px',
    fontWeight: 600,
    marginBottom: '8px',
    color: 'var(--text-primary)',
  } as React.CSSProperties,
  issue: {
    padding: '8px',
    borderRadius: '4px',
    marginBottom: '6px',
    fontSize: '12px',
  } as React.CSSProperties,
  error: {
    background: 'rgba(218, 54, 51, 0.1)',
    borderLeft: '3px solid var(--accent-red)',
  } as React.CSSProperties,
  warning: {
    background: 'rgba(210, 153, 34, 0.1)',
    borderLeft: '3px solid var(--accent-yellow)',
  } as React.CSSProperties,
  suggestion: {
    background: 'rgba(88, 166, 255, 0.1)',
    borderLeft: '3px solid var(--accent-blue)',
  } as React.CSSProperties,
  severity: {
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    fontSize: '10px',
    marginBottom: '4px',
  } as React.CSSProperties,
  message: {
    color: 'var(--text-primary)',
    marginBottom: '4px',
  } as React.CSSProperties,
  suggestion: {
    color: 'var(--text-secondary)',
    fontStyle: 'italic',
  } as React.CSSProperties,
};

export default function ReviewReport() {
  const { currentProject } = useStore();

  if (!currentProject?.outputs?.review) {
    return null;
  }

  let issues: ReviewIssue[] = [];
  try {
    const review = JSON.parse(currentProject.outputs.review);
    issues = review.issues || [];
  } catch {
    return null;
  }

  if (issues.length === 0) {
    return (
      <div style={reportStyles.container}>
        <div style={reportStyles.title}>Review Report</div>
        <div style={{ color: 'var(--accent-green)', fontSize: '13px' }}>
          All checks passed!
        </div>
      </div>
    );
  }

  return (
    <div style={reportStyles.container}>
      <div style={reportStyles.title}>Review Report ({issues.length} issues)</div>
      {issues.map((issue, idx) => {
        const severityStyle = issue.severity === 'error'
          ? reportStyles.error
          : issue.severity === 'warning'
          ? reportStyles.warning
          : reportStyles.suggestion;

        return (
          <div key={idx} style={{ ...reportStyles.issue, ...severityStyle }}>
            <div style={reportStyles.severity}>{issue.severity}</div>
            {issue.file && (
              <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>
                {issue.file}{issue.line ? `:${issue.line}` : ''}
              </div>
            )}
            <div style={reportStyles.message}>{issue.message}</div>
            {issue.suggestion && (
              <div style={reportStyles.suggestion}>Suggestion: {issue.suggestion}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ReviewReport.tsx
git commit -m "feat: add ReviewReport component for displaying code review results"
```

---

### Task 29: Final README Update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with architecture diagram and setup instructions**

Replace the entire `README.md` with:

```markdown
# DevAgent Team

Multi-Agent collaborative coding system that transforms natural language requirements into working software through 4 specialized AI Agents.

## Demo

![DevAgent Demo](docs/demo.gif)

## Architecture

```
User Requirement
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PM Agent   │───▶│   Architect │───▶│    Coder    │───▶│  Reviewer   │
│  (Analyze)  │    │   (Design)  │    │  (Implement)│    │  (Review)   │
└─────────────┘    └─────────────┘    └──────┬──────┘    └──────┬──────┘
                                             │                   │
                                             │     Not Passed    │
                                             │◄──────────────────┘
                                             │    (max 3 loops)
                                             │
                                             ▼
                                        ┌─────────┐
                                        │  DONE   │
                                        └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API Key (or OpenAI API Key)

### Backend

\`\`\`bash
cd backend
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
python main.py
\`\`\`

### Frontend

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

Open http://localhost:5173

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, WebSocket |
| LLM | Claude 3.5 Sonnet / GPT-4o |
| Frontend | React 18, TypeScript, Vite |
| Editor | CodeMirror 6 |
| State | Zustand |
| Styling | CSS Variables (Codex-style dark theme) |

## Project Structure

```
devagent-team/
├── backend/           # Python FastAPI backend
│   ├── agents/        # 4 specialized Agents
│   ├── orchestrator/  # State machine + scheduler
│   ├── llm/           # LLM client + prompts
│   ├── core/          # Message bus + state store
│   └── tools/         # File manager + code runner
├── frontend/          # React TypeScript frontend
│   ├── components/    # UI components
│   ├── store/         # Zustand state
│   └── hooks/         # WebSocket hook
└── output/            # Agent-generated files
```

## Interview Topics

This project demonstrates:

- **Multi-Agent Orchestration**: Handwritten state machine for coordinating 4 AI Agents
- **LLM Application Design**: Structured prompts, output parsing, model fallback
- **Real-time Communication**: WebSocket for live Agent status streaming
- **Code Generation Pipeline**: From spec → architecture → code → review
- **Error Handling**: Retry with backoff, circuit breaker pattern, graceful degradation
- **Full-stack Development**: FastAPI + React with TypeScript

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with architecture and setup instructions"
```

---

## Plan Self-Review

### Spec Coverage Check

| Spec Section | Task(s) | Status |
|---|---|---|
| Project skeleton (README, requirements) | Task 1 | ✅ |
| App configuration | Task 2 | ✅ |
| LLM Client with retry/fallback | Task 3 | ✅ |
| File Manager | Task 4 | ✅ |
| Code Runner with validation | Task 5 | ✅ |
| Message Bus | Task 6 | ✅ |
| State Store (persistent JSON) | Task 7 | ✅ |
| Agent Prompts | Task 8 | ✅ |
| BaseAgent (abstract class) | Task 9 | ✅ |
| PMAgent | Task 10 | ✅ |
| ArchitectAgent | Task 11 | ✅ |
| CoderAgent with file parsing | Task 12 | ✅ |
| ReviewerAgent with JSON parsing | Task 13 | ✅ |
| State Machine | Task 14 | ✅ |
| WebSocket Manager | Task 15 | ✅ |
| Agent Scheduler | Task 16 | ✅ |
| FastAPI Main App | Task 17 | ✅ |
| React project setup | Task 18 | ✅ |
| Types + Theme | Task 19 | ✅ |
| Zustand Store | Task 20 | ✅ |
| Layout (3-pane) | Task 21 | ✅ |
| FileTree | Task 22 | ✅ |
| CodeEditor (CodeMirror) | Task 23 | ✅ |
| AgentCard + AgentPanel + ProgressBar | Task 24 | ✅ |
| ChatInput | Task 25 | ✅ |
| WebSocket Hook | Task 26 | ✅ |
| App component | Task 27 | ✅ |
| ReviewReport | Task 28 | ✅ |
| README | Task 29 | ✅ |

**No gaps found.**

### Placeholder Scan

- No TBD/TODO placeholders
- No vague instructions like "add appropriate error handling"
- Each test has complete code
- Each implementation has complete code
- Each commit command is explicit

### Type Consistency Check

- `AgentContext` fields consistent across all Agent uses
- `AgentOutput` structure consistent
- `WorkflowState` enum consistent between backend and frontend
- WebSocket message types consistent

All types are consistent. ✅
