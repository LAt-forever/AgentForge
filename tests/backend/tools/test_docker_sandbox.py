"""Tests for DockerSandbox."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from backend.tools.docker_sandbox import DockerSandbox, ExecutionResult


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_creation(self):
        """Can create ExecutionResult."""
        result = ExecutionResult(stdout="out", stderr="err", exit_code=0)
        assert result.stdout == "out"
        assert result.stderr == "err"
        assert result.exit_code == 0


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

    def test_uses_default_image(self):
        """Default image is devagent-sandbox:latest."""
        ds = DockerSandbox()
        assert ds.image == "devagent-sandbox:latest"

    def test_uses_default_workspace(self):
        """Default workspace is /workspace."""
        ds = DockerSandbox()
        assert ds.workspace == "/workspace"


class TestEnsureContainer:
    """Test _ensure_container creates container if missing."""

    @patch("subprocess.run")
    def test_container_exists_and_running(self, mock_run):
        """If container exists and running, do nothing."""
        mock_run.return_value = MagicMock(returncode=0, stdout="running\n")
        ds = DockerSandbox()
        ds._ensure_container()
        # Should only call inspect once
        assert mock_run.call_count == 1
        call_args = mock_run.call_args[0][0]
        assert "inspect" in call_args

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

        assert isinstance(result, ExecutionResult)
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
        # First call: _ensure_container's inspect
        # Second call: docker exec that times out
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="running\n"),
            subprocess.TimeoutExpired(cmd=["docker"], timeout=5),
        ]
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

    @patch("subprocess.run")
    def test_validate_javascript_syntax_valid(self, mock_run):
        """Valid JavaScript code passes syntax check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ds = DockerSandbox()
        is_valid, error = ds.validate_syntax("const x = 1;", "javascript")

        assert is_valid is True

    @patch.object(DockerSandbox, "_ensure_container")
    def test_validate_unsupported_language(self, mock_ensure):
        """Unsupported language raises ValueError."""
        ds = DockerSandbox()
        with pytest.raises(ValueError, match="Unsupported language"):
            ds.validate_syntax("code", "rust")
