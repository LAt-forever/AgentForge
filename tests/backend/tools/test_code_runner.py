"""Tests for the CodeRunner tool."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from backend.tools.code_runner import CodeRunner
from backend.tools.docker_sandbox import ExecutionResult


@pytest.fixture(autouse=True)
def local_syntax_mode(monkeypatch):
    """Keep local-mode tests isolated from the developer's .env."""
    from backend.tools import code_runner

    monkeypatch.setattr(code_runner.settings, "use_docker_sandbox", False)


@pytest.fixture
def runner():
    return CodeRunner(timeout=5)


class TestValidateSyntax:
    """Test syntax validation."""

    def test_validate_syntax_valid(self, runner):
        """Valid Python code passes syntax check."""
        code = "x = 1 + 2\nprint(x)"
        is_valid, error = runner.validate_syntax(code)
        assert is_valid is True
        assert error == ""

    def test_validate_syntax_invalid(self, runner):
        """Invalid Python code fails syntax check."""
        code = "x = 1 + \nprint(x)"  # Syntax error
        is_valid, error = runner.validate_syntax(code)
        assert is_valid is False
        assert error != ""

    def test_validate_syntax_with_language(self, runner):
        """Can pass language explicitly."""
        code = "x = 1 + 2\nprint(x)"
        is_valid, error = runner.validate_syntax(code, language="python")
        assert is_valid is True

    @patch("backend.tools.code_runner.settings")
    @patch("backend.tools.docker_sandbox.DockerSandbox")
    def test_validate_syntax_docker_mode(self, mock_docker_cls, mock_settings):
        """When Docker mode enabled, delegate to DockerSandbox."""
        mock_settings.use_docker_sandbox = True
        mock_docker = MagicMock()
        mock_docker.validate_syntax.return_value = (True, None)
        mock_docker_cls.return_value = mock_docker

        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("print('hello')", language="python")

        assert is_valid is True
        assert error is None
        mock_docker.validate_syntax.assert_called_once_with("print('hello')", "python")

    @patch("backend.tools.code_runner.settings")
    def test_validate_typescript_local_fallback(self, mock_settings):
        """TypeScript in local mode returns True (no validation available)."""
        mock_settings.use_docker_sandbox = False
        runner = CodeRunner()
        is_valid, error = runner.validate_syntax("const x = 1;", language="typescript")
        assert is_valid is True
        assert error is None

    def test_validate_unsupported_language(self, runner):
        """Unsupported language raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            runner.validate_syntax("code", language="rust")


class TestDetectLanguage:
    """Test language detection from file extension."""

    def test_detect_python(self, runner):
        """.py files are Python."""
        assert runner.detect_language("main.py") == "python"

    def test_detect_typescript(self, runner):
        """.ts files are TypeScript."""
        assert runner.detect_language("main.ts") == "typescript"

    def test_detect_javascript(self, runner):
        """.js files are JavaScript."""
        assert runner.detect_language("main.js") == "javascript"

    def test_detect_unknown(self, runner):
        """Unknown extensions return None."""
        assert runner.detect_language("main.rs") is None

    def test_detect_nested_path(self, runner):
        """Works with nested paths."""
        assert runner.detect_language("src/utils/helpers.py") == "python"


class TestRunCode:
    """Test running Python code."""

    def test_run_code_success(self, runner):
        """Run code that prints output."""
        code = 'print("Hello, World!")'
        stdout, stderr, returncode = runner.run_code(code)
        assert "Hello, World!" in stdout
        assert returncode == 0

    def test_run_code_timeout(self, runner):
        """Code that sleeps longer than timeout gets killed."""
        code = "import time\ntime.sleep(10)"
        stdout, stderr, returncode = runner.run_code(code)
        # Should timeout and be killed
        assert returncode != 0 or "timeout" in stderr.lower() or "timed out" in str(stderr).lower()

    def test_run_file(self, runner):
        """Run a Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('print("from file")')
            temp_path = f.name

        try:
            stdout, stderr, returncode = runner.run_file(temp_path)
            assert "from file" in stdout
            assert returncode == 0
        finally:
            os.unlink(temp_path)

    @patch("backend.tools.code_runner.settings")
    @patch("backend.tools.docker_sandbox.DockerSandbox")
    def test_run_code_docker_mode(self, mock_docker_cls, mock_settings):
        """Run code in Docker when enabled."""
        mock_settings.use_docker_sandbox = True
        mock_docker = MagicMock()
        mock_docker.execute.return_value = ExecutionResult(
            stdout="hello\n", stderr="", exit_code=0,
        )
        mock_docker_cls.return_value = mock_docker

        runner = CodeRunner()
        stdout, stderr, rc = runner.run_code(
            "print('hello')", project_id="proj1", language="python"
        )

        assert stdout == "hello\n"
        assert rc == 0
        mock_docker.execute.assert_called_once()

    @patch("backend.tools.code_runner.settings")
    def test_run_code_local_fallback_when_no_project_id(self, mock_settings):
        """Without project_id, always use local execution."""
        mock_settings.use_docker_sandbox = True
        runner = CodeRunner()
        stdout, stderr, rc = runner.run_code("print('hello')")
        assert "hello" in stdout
        assert rc == 0
