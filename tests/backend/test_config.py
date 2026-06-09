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
