"""Tests for the CodeRunner tool."""

import os
import tempfile
import pytest

from backend.tools.code_runner import CodeRunner


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
