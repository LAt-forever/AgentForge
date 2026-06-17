"""Workflow profile definitions and requirement-based resolution."""

from dataclasses import dataclass

DEFAULT_PROFILE = "default"
STATIC_WEB_PROFILE = "static_web"


@dataclass(frozen=True)
class WorkflowProfile:
    """Configuration that adapts agent labels, prompts, and artifact handling."""

    name: str
    display_name: str
    agent_labels: dict[str, str]
    prompt_context: str = ""
    validators: tuple[str, ...] = ()
    preview_enabled: bool = False


_DEFAULT_AGENT_LABELS = {
    "pm": "PM",
    "architect": "Architect",
    "coder": "Coder",
    "reviewer": "Reviewer",
}

_STATIC_WEB_AGENT_LABELS = {
    "pm": "Product Brief",
    "architect": "Web Structure",
    "coder": "Frontend Build",
    "reviewer": "Web Review",
}

_STATIC_WEB_PROMPT_CONTEXT = (
    "Create browser-ready static files index.html, style.css, and script.js. "
    "Please avoid external/CDN runtime deps. Review the result as an "
    "interactive web page."
)

_PROFILES = {
    DEFAULT_PROFILE: WorkflowProfile(
        name=DEFAULT_PROFILE,
        display_name="Default",
        agent_labels=_DEFAULT_AGENT_LABELS,
    ),
    STATIC_WEB_PROFILE: WorkflowProfile(
        name=STATIC_WEB_PROFILE,
        display_name="Web App",
        agent_labels=_STATIC_WEB_AGENT_LABELS,
        prompt_context=_STATIC_WEB_PROMPT_CONTEXT,
        validators=("web_artifact",),
        preview_enabled=True,
    ),
}

_STATIC_WEB_TERMS = (
    "static web",
    "static website",
    "landing page",
    "web",
    "page",
    "html",
    "css",
    "js",
    "javascript",
    "frontend",
    "browser",
    "website",
    "timer",
    "calculator",
    "palette",
    "dashboard",
    "form",
    "网页",
    "静态网页",
    "静态网站",
    "网页",
    "页面",
    "前端",
    "浏览器",
    "网站",
    "落地页",
    "计时器",
    "计算器",
    "调色板",
    "仪表盘",
    "表单",
)


def get_workflow_profile(name: str | None) -> WorkflowProfile:
    """Return a workflow profile, falling back to default for unknown names."""
    return _PROFILES.get(name or DEFAULT_PROFILE, _PROFILES[DEFAULT_PROFILE])


def resolve_workflow_profile(
    requirement: str, explicit: str | None = None
) -> WorkflowProfile:
    """Resolve a profile from an explicit choice or requirement text."""
    if explicit:
        return get_workflow_profile(explicit)

    normalized = requirement.lower()
    if any(term in normalized for term in _STATIC_WEB_TERMS):
        return get_workflow_profile(STATIC_WEB_PROFILE)
    return get_workflow_profile(DEFAULT_PROFILE)
