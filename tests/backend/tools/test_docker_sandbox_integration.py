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
