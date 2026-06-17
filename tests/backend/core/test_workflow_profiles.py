"""Tests for workflow profile resolution."""

from backend.core.workflow_profiles import (
    DEFAULT_PROFILE,
    STATIC_WEB_PROFILE,
    get_workflow_profile,
    resolve_workflow_profile,
)


def test_get_default_profile():
    """Default profile uses existing agent labels and no preview."""
    profile = get_workflow_profile(DEFAULT_PROFILE)

    assert profile.name == DEFAULT_PROFILE
    assert profile.display_name == "Default"
    assert profile.agent_labels == {
        "pm": "PM Agent",
        "architect": "Architect Agent",
        "coder": "Coder Agent",
        "reviewer": "Reviewer Agent",
    }
    assert profile.prompt_context == ""
    assert profile.validators == []
    assert profile.preview_enabled is False


def test_get_static_web_profile():
    """Static web profile describes browser-ready frontend artifacts."""
    profile = get_workflow_profile(STATIC_WEB_PROFILE)

    assert profile.name == STATIC_WEB_PROFILE
    assert profile.display_name == "Web App"
    assert profile.agent_labels == {
        "pm": "Product Brief",
        "architect": "Web Structure",
        "coder": "Frontend Build",
        "reviewer": "Web Review",
    }
    assert "index.html" in profile.prompt_context
    assert "style.css" in profile.prompt_context
    assert "script.js" in profile.prompt_context
    assert "avoid external/CDN runtime dependencies" in profile.prompt_context
    assert "interactive web page" in profile.prompt_context
    assert profile.validators == ["web_artifact"]
    assert profile.preview_enabled is True


def test_unknown_profile_falls_back_to_default():
    """Unknown profile names resolve to the default profile."""
    profile = get_workflow_profile("missing")

    assert profile.name == DEFAULT_PROFILE


def test_resolve_static_web_from_english_terms():
    """English web-related requirements resolve to the static web profile."""
    profile = resolve_workflow_profile("Build a browser timer with HTML and CSS")

    assert profile.name == STATIC_WEB_PROFILE


def test_resolve_static_web_from_chinese_terms():
    """Chinese web-related requirements resolve to the static web profile."""
    profile = resolve_workflow_profile("制作一个前端计算器页面")

    assert profile.name == STATIC_WEB_PROFILE


def test_resolve_cli_requirement_defaults():
    """CLI-style requirements without web terms use the default profile."""
    profile = resolve_workflow_profile("Build a Python command line file renamer")

    assert profile.name == DEFAULT_PROFILE


def test_resolve_explicit_profile_overrides_requirement():
    """Explicit profile names override requirement inference."""
    profile = resolve_workflow_profile("Build a Python CLI tool", explicit=STATIC_WEB_PROFILE)

    assert profile.name == STATIC_WEB_PROFILE
