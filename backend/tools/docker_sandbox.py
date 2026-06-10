"""Docker sandbox for secure code execution."""

import logging
import os
import subprocess
import tempfile
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
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", self.container_name],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # Container does not exist — create it
            logger.info(
                "Container %s does not exist, creating it", self.container_name
            )
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    self.container_name,
                    "-v",
                    f"{self._host_workspace}:{self.workspace}",
                    self.image,
                    "tail",
                    "-f",
                    "/dev/null",
                ],
                capture_output=True,
                check=True,
            )
            return

        status = result.stdout.strip()
        if status != "running":
            logger.info(
                "Container %s is %s, starting it", self.container_name, status
            )
            subprocess.run(
                ["docker", "start", self.container_name],
                capture_output=True,
                check=True,
            )

    @property
    def _host_workspace(self) -> str:
        """Get the host-side workspace path."""
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
            "docker",
            "exec",
            "--workdir",
            workdir,
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
            language: Programming language ("python", "typescript", or "javascript")

        Returns:
            (is_valid, error_message). error_message is None if valid.
        """
        self._ensure_container()

        # Create temp file with appropriate extension
        ext_map = {
            "python": ".py",
            "typescript": ".ts",
            "javascript": ".js",
        }
        ext = ext_map.get(language)
        if ext is None:
            raise ValueError(f"Unsupported language: {language}")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Copy file to container via docker cp
            temp_filename = os.path.basename(temp_path)
            check_dir = f"{self.workspace}/_syntax_check"
            container_path = f"{check_dir}/{temp_filename}"

            # Ensure check directory exists in container
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.container_name,
                    "mkdir",
                    "-p",
                    check_dir,
                ],
                capture_output=True,
                check=True,
            )

            # Copy file to container
            subprocess.run(
                ["docker", "cp", temp_path, f"{self.container_name}:{container_path}"],
                capture_output=True,
                check=True,
            )

            if language == "python":
                result = self.execute(
                    "_syntax_check",
                    ["python", "-m", "py_compile", temp_filename],
                    timeout=10,
                )
            elif language in ("typescript", "javascript"):
                result = self.execute(
                    "_syntax_check",
                    ["node", "--check", temp_filename],
                    timeout=10,
                )

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
        full_path = os.path.join(self._host_workspace, project_id, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
