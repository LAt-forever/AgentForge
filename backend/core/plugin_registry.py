"""Plugin registry for agent plugins.

Supports registration, lookup, auto-discovery from directories, and
workflow configuration (ordered list of plugin names).
"""

import importlib
import inspect
import logging
import os
from pathlib import Path

from backend.agents.plugin_base import AgentPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for agent plugins.

    Plugins are registered by name and can be looked up by name or
    by the event types they consume.  The registry also supports
    dynamic discovery from Python modules in a directory.
    """

    def __init__(self):
        self._plugins: dict[str, AgentPlugin] = {}

    def register(self, plugin: AgentPlugin) -> None:
        """Register a plugin instance.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        self._plugins[plugin.name] = plugin
        logger.info("Registered plugin: %s", plugin.name)

    def get(self, name: str) -> AgentPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def get_plugins_for_event(self, event_type: str) -> list[AgentPlugin]:
        """Get all plugins that consume a given event type."""
        return [
            p for p in self._plugins.values()
            if event_type in [et.value for et in p.consumes]
        ]

    def build_workflow(self, names: list[str]) -> list[AgentPlugin]:
        """Resolve a list of plugin names into plugin instances.

        Args:
            names: Ordered list of plugin names defining the workflow.

        Returns:
            List of plugin instances in the given order.

        Raises:
            ValueError: If any plugin name is not registered.
        """
        missing = [n for n in names if n not in self._plugins]
        if missing:
            raise ValueError(f"Unknown plugins in workflow: {missing}")
        return [self._plugins[n] for n in names]

    def discover(self, directory: str | Path) -> list[str]:
        """Auto-discover plugins from Python modules in a directory.

        Scans all .py files in the directory, imports them, and
        registers any classes that subclass AgentPlugin (excluding
        AgentPlugin and BaseAgentPlugin themselves).

        Returns:
            List of discovered plugin names.
        """
        discovered: list[str] = []
        directory = Path(directory)
        if not directory.exists():
            logger.warning("Plugin directory does not exist: %s", directory)
            return discovered

        # Add to path if needed
        str_path = str(directory.resolve())
        if str_path not in os.sys.path:
            os.sys.path.insert(0, str_path)

        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = py_file.stem
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, AgentPlugin)
                        and obj is not AgentPlugin
                        and obj.__name__ != "BaseAgentPlugin"
                        and not getattr(obj, "_plugin_abstract", False)
                    ):
                        # Instantiate and register (requires constructor with no args)
                        try:
                            instance = obj()
                            self.register(instance)
                            discovered.append(instance.name)
                        except TypeError:
                            logger.debug(
                                "Skipping %s (constructor requires arguments)",
                                obj.__name__,
                            )
            except Exception as exc:
                logger.warning("Failed to import plugin module %s: %s", module_name, exc)

        return discovered
