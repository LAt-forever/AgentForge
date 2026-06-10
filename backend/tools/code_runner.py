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

    def validate_syntax(
        self, code: str, language: str | None = None
    ) -> tuple[bool, str | None]:
        """Check code syntax. Returns (is_valid, error_message).

        When use_docker_sandbox=True, delegates to DockerSandbox.
        Otherwise falls back to local py_compile for Python.
        """
        if language is None:
            language = "python"

        if settings.use_docker_sandbox:
            return self._get_docker().validate_syntax(code, language)

        # Local fallback (Python only)
        if language not in ("python", "typescript", "javascript"):
            raise ValueError(f"Unsupported language: {language}")
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
        # Write code to a temp file in the project directory
        suffix = ".py" if language == "python" else ".ts"
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=suffix,
            delete=False,
            dir=".",
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
