import os
from backend.config import Settings


def test_settings_default_values():
    settings = Settings(_env_file=None)
    assert settings.app_name == "DevAgent Team"
    assert settings.output_dir == "output"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    monkeypatch.setenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("MAX_REVIEW_ITERATIONS", "5")

    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key == "test-key-anthropic"
    assert settings.openai_api_key == "test-key-openai"
    assert settings.default_model == "claude-3-5-sonnet-20241022"
    assert settings.max_review_iterations == 5


def test_docker_sandbox_defaults():
    """Docker sandbox settings have sensible defaults."""
    settings = Settings(_env_file=None)
    assert settings.use_docker_sandbox is False
    assert settings.sandbox_container_name == "devagent-sandbox"
    assert settings.sandbox_image == "devagent-sandbox:latest"
    assert settings.sandbox_workspace == "/workspace"


def test_docker_sandbox_from_env(monkeypatch):
    """Docker sandbox settings can be overridden via environment."""
    monkeypatch.setenv("USE_DOCKER_SANDBOX", "true")
    monkeypatch.setenv("SANDBOX_CONTAINER_NAME", "my-sandbox")
    monkeypatch.setenv("SANDBOX_IMAGE", "custom-image:tag")

    settings = Settings(_env_file=None)
    assert settings.use_docker_sandbox is True
    assert settings.sandbox_container_name == "my-sandbox"
    assert settings.sandbox_image == "custom-image:tag"


def test_default_language_default():
    """default_language defaults to python."""
    assert Settings(_env_file=None).default_language == "python"


def test_default_language_from_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_LANGUAGE", "typescript")
    assert Settings(_env_file=None).default_language == "typescript"
