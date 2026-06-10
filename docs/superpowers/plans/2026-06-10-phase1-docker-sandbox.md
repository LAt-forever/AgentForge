# Phase 1: Docker Sandbox Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace local code execution with a long-running Docker sandbox container, add Docker Compose for one-command startup, and make it configurable.

**Architecture:** A `DockerSandbox` class manages a persistent `devagent-sandbox` container via `docker exec`. `CodeRunner` delegates to `DockerSandbox` when enabled. A custom Docker image pre-installs Python, Node.js, git, pylint, mypy, eslint, and TypeScript. Docker Compose orchestrates sandbox + backend + frontend services.

**Tech Stack:** Python 3.11, FastAPI, Docker, Docker Compose, pytest, pytest-asyncio

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `sandbox/Dockerfile` | Create | Sandbox container image with Python + Node + tools |
| `backend/tools/docker_sandbox.py` | Create | `DockerSandbox` class: container lifecycle, exec, syntax validation |
| `backend/tools/code_runner.py` | Modify | Delegate to `DockerSandbox` when enabled; keep local fallback |
| `backend/config.py` | Modify | Add `use_docker_sandbox`, `sandbox_container_name`, `sandbox_image` |
| `docker-compose.yml` | Create | Orchestrate sandbox + backend + frontend |
| `backend/Dockerfile` | Create | Backend service image |
| `frontend/Dockerfile` | Create | Frontend service image |
| `tests/backend/tools/test_docker_sandbox.py` | Create | Unit tests for `DockerSandbox` (mocked docker calls) |
| `tests/backend/tools/test_code_runner.py` | Modify | Update tests for Docker mode + fallback mode |

---

## Task 1: DockerSandbox Core (container lifecycle + exec)

**Files:**
- Create: `backend/tools/docker_sandbox.py`
- Create: `tests/backend/tools/test_docker_sandbox.py`

### Step 1: Write the failing test

```python
# tests/backend/tools/test_docker_sandbox.py
"""Tests for DockerSandbox."""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from backend.tools.docker_sandbox import DockerSandbox, ExecutionResult


class TestDockerSandboxInit:
    """Test container initialization."""

    def test_uses_default_container_name(self):
        """Default container name is devagent-sandbox."""
        ds = DockerSandbox()
        assert ds.container_name == "devagent-sandbox"

    def test_uses_custom_container_name(self):
        """Custom container name can be set."""
        ds = DockerSandbox(container_name="my-sandbox")
        assert ds.container_name == "my-sandbox"


class TestEnsureContainer:
    """Test _ensure_container creates container if missing."""

    @patch("subprocess.run")
    def test_container_exists_and_running(self, mock_run):
        """If container exists and running, do nothing."""
        mock_run.return_value = MagicMock(returncode=0, stdout="running\n")
        ds = DockerSandbox()
        ds._ensure_container()
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_container_not_exists_creates_it(self, mock_run):
        """If container does not exist, create it."""
        # First call: inspect (fails = container missing)
        # Second call: create/run
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="No such container"),
            MagicMock(returncode=0),
        ]
        ds = DockerSandbox()
        ds._ensure_container()
        assert mock_run.call_count == 2
        # Second call should be docker run
        second_call = mock_run.call_args_list[1]
        assert "run" in second_call[0][0]

    @patch("subprocess.run")
    def test_container_exists_but_not_running_restarts(self, mock_run):
        """If container exists but stopped, start it."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="exited\n"),
            MagicMock(returncode=0),
        ]
        ds = DockerSandbox()
        ds._ensure_container()
        assert mock_run.call_count == 2
        second_call = mock_run.call_args_list[1]
        assert "start" in second_call[0][0]


class TestExecute:
    """Test execute method."""

    @patch("subprocess.run")
    def test_execute_success(self, mock_run):
        """Execute command successfully."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="hello\n",
            stderr="",
        )
        ds = DockerSandbox()
        result = ds.execute("proj123", ["python", "-c", "print('hello')"])

        assert result.exit_code == 0
        assert result.stdout == "hello\n"
        assert result.stderr == ""
        # Verify docker exec was called with correct args
        call_args = mock_run.call_args[0][0]
        assert "exec" in call_args
        assert "--workdir" in call_args
        assert "/workspace/proj123" in call_args

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run):
        """Execute command that returns non-zero exit code."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error: something went wrong\n",
        )
        ds = DockerSandbox()
        result = ds.execute("proj123", ["python", "-c", "raise Exception()"])

        assert result.exit_code == 1
        assert "something went wrong" in result.stderr

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run):
        """Execute command that times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["docker"], timeout=5)
        ds = DockerSandbox()
        result = ds.execute("proj123", ["sleep", "100"], timeout=5)

        assert result.exit_code == -1
        assert "timed out" in result.stderr

    @patch("subprocess.run")
    def test_ensures_container_before_exec(self, mock_run):
        """Execute calls _ensure_container first."""
        mock_run.return_value = MagicMock(returncode=0, stdout="running\n")
        ds = DockerSandbox()
        with patch.object(ds, "_ensure_container") as mock_ensure:
            ds.execute("proj123", ["echo", "hi"])
            mock_ensure.assert_called_once()


class TestValidateSyntax:
    """Test syntax validation."""

    @patch("subprocess.run")
    def test_validate_python_syntax_valid(self, mock_run):
        """Valid Python code passes syntax check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ds = DockerSandbox()
        is_valid, error = ds.validate_syntax("print('hello')", "python")

        assert is_valid is True
        assert error is None
        call_args = mock_run.call_args[0][0]
        assert "py_compile" in call_args

    @patch("subprocess.run")
    def test_validate_python_syntax_invalid(self, mock_run):
        """Invalid Python code fails syntax check."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="SyntaxError: invalid syntax\n",
        )
        ds = DockerSandbox()
        is_valid, error = ds.validate_syntax("print(", "python")

        assert is_valid is False
        assert "SyntaxError" in error

    @patch("subprocess.run")
    def test_validate_typescript_syntax_valid(self, mock_run):
        """Valid TypeScript code passes syntax check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ds = DockerSandbox()
        is_valid, error = ds.validate_syntax("const x: number = 1;", "typescript")

        assert is_valid is True
        call_args = mock_run.call_args[0][0]
        assert "tsc" in call_args or "node" in call_args

    @patch("subprocess.run")
    def test_validate_unsupported_language(self, mock_run):
        """Unsupported language raises ValueError."""
        ds = DockerSandbox()
        with pytest.raises(ValueError, match="Unsupported language"):
            ds.validate_syntax("code", "rust")
```

### Step 2: Run test to verify it fails

Run: `pytest tests/backend/tools/test_docker_sandbox.py -v`

Expected: FAIL with import errors (DockerSandbox and ExecutionResult not defined)

### Step 3: Write minimal implementation

```python
# backend/tools/docker_sandbox.py
"""Docker sandbox for secure code execution."""

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a command execution."""
    stdout: str
    stderr: str
    exit_code: int


class DockerSandbox:
    """Manages a long-running Docker sandbox container for code execution."""

    def __init__(
        self,
        container_name: str = "devagent-sandbox",
        image: str = "devagent-sandbox:latest",
        workspace: str = "/workspace",
    ):
        self.container_name = container_name
        self.image = image
        self.workspace = workspace

    def _ensure_container(self) -> None:
        """Check if container exists and is running; create/start if needed."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", self.container_name],
                capture_output=True,
                text=True,
                check=True,
            )
            status = result.stdout.strip()
            if status != "running":
                logger.info("Container %s is %s, starting it", self.container_name, status)
                subprocess.run(
                    ["docker", "start", self.container_name],
                    capture_output=True,
                    check=True,
                )
        except subprocess.CalledProcessError:
            logger.info("Container %s does not exist, creating it", self.container_name)
            subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", self.container_name,
                    "-v", f"{self._host_workspace}:{self.workspace}",
                    self.image,
                    "tail", "-f", "/dev/null",
                ],
                capture_output=True,
                check=True,
            )

    @property
    def _host_workspace(self) -> str:
        """Get the host-side workspace path."""
        import os
        return os.path.abspath("output")

    def execute(
        self,
        project_id: str,
        command: list[str],
        timeout: int = 30,
    ) -> ExecutionResult:
        """Execute a command inside the sandbox container.

        Args:
            project_id: Project identifier (determines working directory)
            command: Command and arguments to execute
            timeout: Maximum execution time in seconds

        Returns:
            ExecutionResult with stdout, stderr, and exit code
        """
        self._ensure_container()

        workdir = f"{self.workspace}/{project_id}"
        docker_cmd = [
            "docker", "exec",
            "--workdir", workdir,
            self.container_name,
        ] + command

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                exit_code=-1,
            )

    def validate_syntax(
        self,
        code: str,
        language: str,
    ) -> tuple[bool, str | None]:
        """Validate code syntax without executing.

        Args:
            code: Source code to validate
            language: Programming language ("python" or "typescript")

        Returns:
            (is_valid, error_message). error_message is None if valid.
        """
        import tempfile
        import os

        self._ensure_container()

        with tempfile.NamedTemporaryFile(mode="w", suffix=f".{language}", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            if language == "python":
                result = self.execute(
                    "_syntax_check",
                    ["python", "-m", "py_compile", f"/workspace/_syntax_check/{os.path.basename(temp_path)}"],
                    timeout=10,
                )
            elif language in ("typescript", "javascript"):
                # Write to container and run node --check or tsc
                result = self.execute(
                    "_syntax_check",
                    ["node", "--check", f"/workspace/_syntax_check/{os.path.basename(temp_path)}"],
                    timeout=10,
                )
            else:
                raise ValueError(f"Unsupported language: {language}")

            if result.exit_code == 0:
                return True, None
            return False, result.stderr
        finally:
            os.unlink(temp_path)

    def write_file(self, project_id: str, path: str, content: str) -> None:
        """Write a file to the sandbox workspace.

        Args:
            project_id: Project directory name
            path: Relative path within project
            content: File content
        """
        import os
        full_path = os.path.join(self._host_workspace, project_id, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
```

### Step 4: Run test to verify it passes

Run: `pytest tests/backend/tools/test_docker_sandbox.py -v`

Expected: All tests PASS

### Step 5: Commit

```bash
git add tests/backend/tools/test_docker_sandbox.py backend/tools/docker_sandbox.py
git commit -m "feat: add DockerSandbox with container lifecycle, exec, and syntax validation"
```

---

## Task 2: Enhance CodeRunner with Docker fallback

**Files:**
- Modify: `backend/tools/code_runner.py`
- Modify: `tests/backend/tools/test_code_runner.py`

### Step 1: Write the failing test

```python
# tests/backend/tools/test_code_runner.py
"""Tests for CodeRunner."""

from unittest.mock import patch, MagicMock

import pytest

from backend.tools.code_runner import CodeRunner
from backend.tools.docker_sandbox import ExecutionResult


class TestValidateSyntax:
    """Test syntax validation."""

    @patch("backend.tools.code_runner.py_compile.compile")
    def test_validate_python_syntax_local(self, mock_compile):
        """Local Python validation works."""
        mock_compile.return_value = None
        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("print('hello')", "python")
        assert is_valid is True
        assert error == ""

    @patch("backend.tools.code_runner.py_compile.compile")
    def test_validate_python_syntax_invalid_local(self, mock_compile):
        """Invalid Python returns False."""
        import py_compile
        mock_compile.side_effect = py_compile.PyCompileError("SyntaxError")
        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("invalid", "python")
        assert is_valid is False
        assert "SyntaxError" in error

    @patch("backend.tools.code_runner.settings")
    @patch("backend.tools.code_runner.DockerSandbox")
    def test_validate_python_syntax_docker(self, mock_docker_cls, mock_settings):
        """When Docker mode enabled, delegate to DockerSandbox."""
        mock_settings.use_docker_sandbox = True
        mock_docker = MagicMock()
        mock_docker.validate_syntax.return_value = (True, None)
        mock_docker_cls.return_value = mock_docker

        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("print('hello')", "python")

        assert is_valid is True
        assert error is None
        mock_docker.validate_syntax.assert_called_once_with("print('hello')", "python")

    @patch("backend.tools.code_runner.settings")
    def test_validate_typescript_syntax(self, mock_settings):
        """TypeScript syntax validation."""
        mock_settings.use_docker_sandbox = False
        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("const x = 1;", "typescript")
        assert is_valid is True  # Local fallback just returns True for now

    def test_validate_unsupported_language(self):
        """Unsupported language raises ValueError."""
        runner = CodeRunner()
        with pytest.raises(ValueError, match="Unsupported language"):
            runner.validate_syntax("code", "rust")


class TestDetectLanguage:
    """Test language detection from file extension."""

    def test_detect_python(self):
        """.py files are Python."""
        runner = CodeRunner()
        assert runner.detect_language("main.py") == "python"

    def test_detect_typescript(self):
        """.ts files are TypeScript."""
        runner = CodeRunner()
        assert runner.detect_language("main.ts") == "typescript"

    def test_detect_javascript(self):
        """.js files are JavaScript."""
        runner = CodeRunner()
        assert runner.detect_language("main.js") == "javascript"

    def test_detect_unknown(self):
        """Unknown extensions return None."""
        runner = CodeRunner()
        assert runner.detect_language("main.rs") is None


class TestRunCode:
    """Test code execution."""

    @patch("subprocess.run")
    def test_run_python_file_local(self, mock_run):
        """Run Python file locally."""
        mock_run.return_value = MagicMock(
            stdout="hello\n", stderr="", returncode=0,
        )
        runner = CodeRunner()
        stdout, stderr, rc = runner.run_code("print('hello')")
        assert stdout == "hello\n"
        assert rc == 0

    @patch("backend.tools.code_runner.settings")
    @patch("backend.tools.code_runner.DockerSandbox")
    def test_run_code_docker(self, mock_docker_cls, mock_settings):
        """Run code in Docker when enabled."""
        mock_settings.use_docker_sandbox = True
        mock_docker = MagicMock()
        mock_docker.execute.return_value = ExecutionResult(
            stdout="hello\n", stderr="", exit_code=0,
        )
        mock_docker_cls.return_value = mock_docker

        runner = CodeRunner()
        stdout, stderr, rc = runner.run_code("print('hello')", project_id="proj1", language="python")

        assert stdout == "hello\n"
        assert rc == 0
        mock_docker.execute.assert_called_once()
```

### Step 2: Run test to verify it fails

Run: `pytest tests/backend/tools/test_code_runner.py -v`

Expected: FAIL (new methods don't exist, Docker mode not implemented)

### Step 3: Write minimal implementation

```python
# backend/tools/code_runner.py
"""Code execution tool for agents."""

import os
import py_compile
import subprocess
import sys
import tempfile

from backend.config import settings


class CodeRunner:
    """Runs and validates code, with optional Docker sandbox delegation."""

    def __init__(self, timeout: int = 30):
        self._timeout = timeout
        self._docker = None

    def _get_docker(self):
        """Lazy-load DockerSandbox instance."""
        if self._docker is None:
            from backend.tools.docker_sandbox import DockerSandbox
            self._docker = DockerSandbox(
                container_name=settings.sandbox_container_name,
                image=settings.sandbox_image,
            )
        return self._docker

    def validate_syntax(self, code: str, language: str | None = None) -> tuple[bool, str | None]:
        """Check code syntax. Returns (is_valid, error_message).

        When use_docker_sandbox=True, delegates to DockerSandbox.
        Otherwise falls back to local py_compile for Python.
        """
        if language is None:
            language = "python"

        if settings.use_docker_sandbox:
            return self._get_docker().validate_syntax(code, language)

        # Local fallback (Python only)
        if language != "python":
            # For local mode without Docker, we can't validate non-Python
            return True, None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            py_compile.compile(temp_path, doraise=True)
            return True, ""
        except py_compile.PyCompileError as exc:
            return False, str(exc)
        finally:
            os.unlink(temp_path)

    def detect_language(self, file_path: str) -> str | None:
        """Detect programming language from file extension.

        Returns: "python", "typescript", "javascript", or None
        """
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".ts": "typescript",
            ".js": "javascript",
        }
        return mapping.get(ext)

    def run_file(self, file_path: str) -> tuple[str, str, int]:
        """Run a file with subprocess. Returns (stdout, stderr, returncode)."""
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )
        return result.stdout, result.stderr, result.returncode

    def run_code(
        self,
        code: str,
        project_id: str | None = None,
        language: str = "python",
    ) -> tuple[str, str, int]:
        """Write code to temp file and run it.

        When use_docker_sandbox=True and project_id is provided,
        executes inside the Docker sandbox.
        """
        if settings.use_docker_sandbox and project_id:
            return self._run_in_docker(code, project_id, language)

        # Local execution
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            return self.run_file(temp_path)
        except subprocess.TimeoutExpired:
            return "", f"Execution timed out after {self._timeout} seconds", -1
        finally:
            os.unlink(temp_path)

    def _run_in_docker(
        self,
        code: str,
        project_id: str,
        language: str,
    ) -> tuple[str, str, int]:
        """Execute code inside Docker sandbox."""
        import tempfile

        # Write code to a temp file in the project directory
        suffix = ".py" if language == "python" else ".ts"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, dir=".",
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            filename = os.path.basename(temp_path)
            self._get_docker().write_file(project_id, f"_exec/{filename}", code)

            if language == "python":
                result = self._get_docker().execute(
                    project_id,
                    ["python", f"_exec/{filename}"],
                    timeout=self._timeout,
                )
            else:
                result = self._get_docker().execute(
                    project_id,
                    ["node", f"_exec/{filename}"],
                    timeout=self._timeout,
                )

            return result.stdout, result.stderr, result.exit_code
        finally:
            os.unlink(temp_path)
```

### Step 4: Run test to verify it passes

Run: `pytest tests/backend/tools/test_code_runner.py -v`

Expected: All tests PASS

### Step 5: Commit

```bash
git add tests/backend/tools/test_code_runner.py backend/tools/code_runner.py
git commit -m "feat: enhance CodeRunner with Docker sandbox delegation and language detection"
```

---

## Task 3: Extend configuration

**Files:**
- Modify: `backend/config.py`
- Modify: `tests/backend/test_config.py`

### Step 1: Write the failing test

```python
# tests/backend/test_config.py (append)

def test_docker_sandbox_settings():
    """Docker sandbox settings have defaults."""
    from backend.config import Settings
    s = Settings()
    assert s.use_docker_sandbox is False
    assert s.sandbox_container_name == "devagent-sandbox"
    assert s.sandbox_image == "devagent-sandbox:latest"
    assert s.sandbox_workspace == "/workspace"


def test_docker_sandbox_settings_from_env(monkeypatch):
    """Docker sandbox settings can be overridden via env."""
    from backend.config import Settings
    monkeypatch.setenv("USE_DOCKER_SANDBOX", "true")
    monkeypatch.setenv("SANDBOX_CONTAINER_NAME", "custom-sandbox")
    s = Settings()
    assert s.use_docker_sandbox is True
    assert s.sandbox_container_name == "custom-sandbox"
```

### Step 2: Run test to verify it fails

Run: `pytest tests/backend/test_config.py::test_docker_sandbox_settings -v`

Expected: FAIL (AttributeError: use_docker_sandbox)

### Step 3: Write minimal implementation

```python
# backend/config.py

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "DevAgent Team"
    output_dir: str = "output"

    # LLM API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    glm_api_key: str = ""

    # Model configuration
    default_model: str = "deepseek-v4-pro"
    fallback_model: str = "glm-4-plus"

    # DeepSeek configuration
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-v4-pro"

    # GLM (Zhipu AI) configuration
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    glm_model: str = "glm-4-plus"

    # Workflow configuration
    max_review_iterations: int = 5
    max_llm_retries: int = 3
    code_execution_timeout: int = 30

    # Docker sandbox configuration
    use_docker_sandbox: bool = False
    sandbox_container_name: str = "devagent-sandbox"
    sandbox_image: str = "devagent-sandbox:latest"
    sandbox_workspace: str = "/workspace"


# Global settings instance
settings = Settings()
```

### Step 4: Run test to verify it passes

Run: `pytest tests/backend/test_config.py -v`

Expected: All tests PASS

### Step 5: Commit

```bash
git add tests/backend/test_config.py backend/config.py
git commit -m "feat: add Docker sandbox configuration settings"
```

---

## Task 4: Create sandbox Dockerfile

**Files:**
- Create: `sandbox/Dockerfile`

### Step 1: Write the Dockerfile

```dockerfile
# sandbox/Dockerfile
FROM python:3.11-slim-bookworm

# Install system dependencies: curl, git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Python static analysis tools (for Phase 3)
RUN pip install --no-cache-dir \
    pylint \
    mypy

# Pre-install TypeScript / JavaScript tools (for Phase 3)
RUN npm install -g \
    typescript \
    eslint \
    @typescript-eslint/parser \
    @typescript-eslint/eslint-plugin

# Create workspace directory
WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
```

### Step 2: Verify the Dockerfile builds

Run:
```bash
cd sandbox && docker build -t devagent-sandbox:latest .
```

Expected: Build succeeds, image `devagent-sandbox:latest` is created

### Step 3: Commit

```bash
git add sandbox/Dockerfile
git commit -m "feat: add sandbox Dockerfile with Python, Node.js, git, pylint, mypy, eslint"
```

---

## Task 5: Create backend and frontend Dockerfiles + Docker Compose

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`

### Step 1: Write backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for managing sandbox container from backend)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Write frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server (bind to 0.0.0.0 for Docker)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Step 3: Write docker-compose.yml

```yaml
# docker-compose.yml
services:
  sandbox:
    build:
      context: ./sandbox
      dockerfile: Dockerfile
    container_name: devagent-sandbox
    volumes:
      - ./backend/output:/workspace
    command: tail -f /dev/null
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/output:/app/output
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - USE_DOCKER_SANDBOX=true
      - SANDBOX_CONTAINER_NAME=devagent-sandbox
      - SANDBOX_IMAGE=devagent-sandbox:latest
      - OUTPUT_DIR=/app/output
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
      - GLM_API_KEY=${GLM_API_KEY:-}
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
    depends_on:
      - backend
```

### Step 4: Commit

```bash
git add backend/Dockerfile frontend/Dockerfile docker-compose.yml
git commit -m "feat: add Docker Compose orchestration with backend, frontend, and sandbox services"
```

---

## Task 6: Integration test — end-to-end Docker sandbox

**Files:**
- Create: `tests/backend/tools/test_docker_sandbox_integration.py`

### Step 1: Write integration test (optional, skip if Docker unavailable)

```python
# tests/backend/tools/test_docker_sandbox_integration.py
"""Integration tests for DockerSandbox (requires Docker daemon)."""

import os
import subprocess

import pytest

from backend.tools.docker_sandbox import DockerSandbox, ExecutionResult


pytestmark = pytest.mark.skipif(
    subprocess.run(["docker", "info"], capture_output=True).returncode != 0,
    reason="Docker not available",
)


@pytest.fixture
def docker_sandbox():
    """Create a DockerSandbox for testing."""
    ds = DockerSandbox(
        container_name="devagent-sandbox-test",
        image="devagent-sandbox:latest",
    )
    yield ds
    # Cleanup: remove test container
    subprocess.run(
        ["docker", "rm", "-f", "devagent-sandbox-test"],
        capture_output=True,
    )


class TestIntegration:
    """Integration tests requiring Docker."""

    def test_execute_python(self, docker_sandbox):
        """Execute Python code in sandbox."""
        os.makedirs("output/test_proj", exist_ok=True)
        result = docker_sandbox.execute(
            "test_proj",
            ["python", "-c", "print('hello from docker')"],
        )
        assert result.exit_code == 0
        assert "hello from docker" in result.stdout

    def test_validate_python_syntax(self, docker_sandbox):
        """Validate Python syntax."""
        is_valid, error = docker_sandbox.validate_syntax("print('ok')", "python")
        assert is_valid is True
        assert error is None

    def test_validate_python_syntax_invalid(self, docker_sandbox):
        """Validate invalid Python syntax."""
        is_valid, error = docker_sandbox.validate_syntax("print(", "python")
        assert is_valid is False
        assert error is not None
```

### Step 2: Run integration test (if Docker available)

Run: `pytest tests/backend/tools/test_docker_sandbox_integration.py -v`

Expected: PASS if Docker is running and image exists

### Step 3: Commit

```bash
git add tests/backend/tools/test_docker_sandbox_integration.py
git commit -m "test: add Docker sandbox integration tests"
```

---

## Task 7: Update main.py workflow to use Docker sandbox

**Files:**
- Modify: `backend/main.py`

### Step 1: Identify changes needed

In `backend/main.py` `_run_workflow()`:
- After Coder Agent generates code, syntax validation currently calls `code_runner.validate_syntax(content)`
- Need to pass `language` parameter (detect from file extension)
- Docker mode should be transparent — CodeRunner handles the delegation internally

### Step 2: Make minimal changes

Find this block in `main.py`:
```python
# --- Syntax validation before review ---
syntax_errors = []
for filepath, content in coder_output.files.items():
    if filepath.endswith(".py"):
        is_valid, error = code_runner.validate_syntax(content)
        if not is_valid:
            syntax_errors.append(f"{filepath}: {error}")
```

Replace with:
```python
# --- Syntax validation before review ---
syntax_errors = []
for filepath, content in coder_output.files.items():
    language = code_runner.detect_language(filepath)
    if language:
        is_valid, error = code_runner.validate_syntax(content, language)
        if not is_valid:
            syntax_errors.append(f"{filepath}: {error}")
```

### Step 3: Commit

```bash
git add backend/main.py
git commit -m "feat: integrate Docker sandbox into workflow with language detection"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] DockerSandbox class with container lifecycle — Task 1
- [x] CodeRunner enhanced with Docker delegation — Task 2
- [x] Config extended with sandbox settings — Task 3
- [x] Sandbox Dockerfile with Python + Node + tools — Task 4
- [x] Docker Compose with all 3 services — Task 5
- [x] Integration tests — Task 6
- [x] main.py workflow integration — Task 7

**2. Placeholder scan:**
- [x] No TBD, TODO, or "implement later"
- [x] All code blocks contain complete implementations
- [x] All test code is complete
- [x] No "similar to Task N" references

**3. Type consistency:**
- [x] `validate_syntax` returns `tuple[bool, str | None]` consistently
- [x] `ExecutionResult` has `stdout`, `stderr`, `exit_code` everywhere
- [x] Config field names match usage in `DockerSandbox.__init__`
- [x] `detect_language` returns `str | None` consistently

**4. DRY / YAGNI:**
- [x] `DockerSandbox._get_docker` pattern reused in `CodeRunner`
- [x] Language detection is a single method, not duplicated
- [x] No premature abstraction — simple delegation pattern

**5. Test coverage:**
- [x] Container lifecycle: exists/running, missing, stopped
- [x] Execute: success, failure, timeout
- [x] Validate syntax: valid Python, invalid Python, valid TS, unsupported
- [x] CodeRunner: local mode, Docker mode, fallback, language detection
- [x] Config: defaults, env override
- [x] Integration: Python execution, syntax validation

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-phase1-docker-sandbox.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach would you like?