"""Tests for PluginRegistry."""

import pytest

from backend.agents.plugin_base import AgentPlugin
from backend.core.event_bus import EventType
from backend.core.plugin_registry import PluginRegistry


class FakePlugin(AgentPlugin):
    """Fake plugin for testing."""

    def __init__(self, name="fake"):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def consumes(self):
        return [EventType.PROJECT_CREATED]

    @property
    def produces(self):
        return EventType.SPEC_GENERATED

    async def execute(self, context, event):
        return type("Output", (), {"content": "", "files": {}, "metadata": {}})()


class AnotherFakePlugin(AgentPlugin):
    """Another fake plugin."""

    @property
    def name(self):
        return "another"

    @property
    def consumes(self):
        return [EventType.SPEC_GENERATED]

    @property
    def produces(self):
        return None

    async def execute(self, context, event):
        return type("Output", (), {"content": "", "files": {}, "metadata": {}})()


@pytest.fixture
def registry():
    return PluginRegistry()


class TestPluginRegistryRegister:
    """Test plugin registration."""

    def test_register_plugin(self, registry):
        """Can register a plugin."""
        plugin = FakePlugin()
        registry.register(plugin)
        assert "fake" in registry.list_plugins()

    def test_register_duplicate_raises(self, registry):
        """Registering duplicate name raises ValueError."""
        registry.register(FakePlugin())
        with pytest.raises(ValueError, match="already registered"):
            registry.register(FakePlugin())

    def test_get_plugin(self, registry):
        """Can retrieve plugin by name."""
        plugin = FakePlugin()
        registry.register(plugin)
        assert registry.get("fake") is plugin

    def test_get_missing_returns_none(self, registry):
        """Getting unregistered plugin returns None."""
        assert registry.get("missing") is None

    def test_list_plugins(self, registry):
        """Lists all registered plugin names."""
        registry.register(FakePlugin("a"))
        registry.register(FakePlugin("b"))
        assert sorted(registry.list_plugins()) == ["a", "b"]


class TestPluginRegistryEventLookup:
    """Test lookup by event type."""

    def test_get_plugins_for_event(self, registry):
        """Find plugins that consume a specific event type."""
        registry.register(FakePlugin())  # consumes PROJECT_CREATED
        registry.register(AnotherFakePlugin())  # consumes SPEC_GENERATED

        creators = registry.get_plugins_for_event("project_created")
        assert len(creators) == 1
        assert creators[0].name == "fake"


class TestPluginRegistryBuildWorkflow:
    """Test workflow resolution."""

    def test_build_workflow(self, registry):
        """Resolve ordered list of plugin names to instances."""
        p1 = FakePlugin("pm")
        p2 = FakePlugin("architect")
        registry.register(p1)
        registry.register(p2)

        workflow = registry.build_workflow(["pm", "architect"])
        assert len(workflow) == 2
        assert workflow[0] is p1
        assert workflow[1] is p2

    def test_build_workflow_missing_raises(self, registry):
        """Unknown plugin names raise ValueError."""
        registry.register(FakePlugin())
        with pytest.raises(ValueError, match="Unknown plugins"):
            registry.build_workflow(["fake", "missing"])
