"""Event-driven workflow orchestrator.

Replaces the hard-coded _run_workflow() in main.py with an event-driven
architecture where agents are independent consumers and state transitions
are triggered by events.

The orchestrator:
  1. Maintains the AgentContext for each project
  2. Routes events to the appropriate plugin via the PluginRegistry
  3. Handles file I/O, git commits, WebSocket notifications, and state transitions
  4. Manages the review iteration loop

Backwards compatibility:
  - REST API (/api/projects) and WebSocket (/ws/{id}) interfaces are unchanged
  - Only internal implementation changes
"""

import logging
import os

from backend.agents.base_agent import AgentContext, AgentOutput
from backend.agents.plugin_base import AgentPlugin
from backend.config import settings
from backend.core.event_bus import Event, EventBus, EventType
from backend.core.plugin_registry import PluginRegistry
from backend.core.state_store import StateStore, WorkflowState
from backend.orchestrator.state_machine import StateMachine
from backend.orchestrator.websocket_manager import WebSocketManager
from backend.tools.code_runner import CodeRunner
from backend.tools.file_manager import FileManager
from backend.tools.git_manager import GitManager

logger = logging.getLogger(__name__)


class EventDrivenOrchestrator:
    """Orchestrates the agent workflow via events.

    Usage:
        orchestrator = EventDrivenOrchestrator(...)
        await orchestrator.start_workflow(project_id, requirement)

    The orchestrator registers itself as the sole event handler on the
    EventBus and dispatches events to plugins based on the workflow map.
    """

    # Event type -> next action mapping
    # Special actions start with "_" and are handled internally
    DEFAULT_WORKFLOW: dict[EventType, str] = {
        EventType.PROJECT_CREATED: "pm",
        EventType.SPEC_GENERATED: "architect",
        EventType.ARCHITECTURE_GENERATED: "coder",
        EventType.CODE_GENERATED: "_syntax_check",
        EventType.SYNTAX_CHECKED: "reviewer",
        EventType.REVIEW_COMPLETED: "_review_decision",
        EventType.ITERATION_STARTED: "coder",
    }

    def __init__(
        self,
        event_bus: EventBus,
        plugin_registry: PluginRegistry,
        ws_manager: WebSocketManager,
        state_store: StateStore,
        workflow_map: dict[EventType, str] | None = None,
    ):
        self.event_bus = event_bus
        self.registry = plugin_registry
        self.ws_manager = ws_manager
        self.state_store = state_store
        self.workflow_map = workflow_map or dict(self.DEFAULT_WORKFLOW)

        # Per-project state
        self._contexts: dict[str, AgentContext] = {}
        self._state_machines: dict[str, StateMachine] = {}
        self._code_runners: dict[str, CodeRunner] = {}

        # Register self as handler for all workflow event types
        for event_type in self.workflow_map.keys():
            self.event_bus.subscribe(event_type, self._on_event)

        # Also handle ERROR events
        self.event_bus.subscribe(EventType.ERROR, self._on_error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_workflow(self, project_id: str, requirement: str) -> None:
        """Start a new workflow for a project.

        Initializes context, state machine, file manager, git repo,
        and publishes the initial PROJECT_CREATED event.
        """
        # Ensure project exists in state store (idempotent if already created)
        if self.state_store.get_project(project_id) is None:
            self.state_store.create_project(project_id, requirement)

        # Initialize project state
        context = AgentContext(requirement=requirement, project_id=project_id)
        context.language = settings.default_language
        self._contexts[project_id] = context

        self._state_machines[project_id] = StateMachine(
            max_iterations=settings.max_review_iterations
        )
        self._code_runners[project_id] = CodeRunner(
            timeout=settings.code_execution_timeout
        )

        # File system setup
        fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
        gm = GitManager(base_dir=settings.output_dir)
        gm.init_repo(project_id)

        # Notify frontend
        await self._send_terminal(project_id, "agent", f"Initialized project {project_id}\n")

        # Start workflow
        sm = self._state_machines[project_id]
        sm.transition_to(WorkflowState.PLANNING)
        self.state_store.update_state(project_id, WorkflowState.PLANNING)
        await self._notify_workflow_state(project_id, sm)

        # Publish initial event
        event = Event(
            type=EventType.PROJECT_CREATED,
            project_id=project_id,
            payload={"requirement": requirement},
        )
        await self.event_bus.publish(event)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _on_event(self, event: Event) -> Event | None:
        """Main event handler — routes events to plugins or internal handlers."""
        project_id = event.project_id
        action = self.workflow_map.get(event.type)

        if action is None:
            logger.warning("No workflow action for event %s", event.type.value)
            return None

        if action.startswith("_"):
            # Internal handler
            handler = getattr(self, action, None)
            if handler:
                return await handler(event)
            logger.error("Unknown internal action: %s", action)
            return None

        # Plugin handler
        plugin = self.registry.get(action)
        if plugin is None:
            logger.error("Plugin not found: %s", action)
            return Event(
                type=EventType.ERROR,
                project_id=project_id,
                payload={"error": f"Plugin '{action}' not registered"},
            )

        context = self._contexts.get(project_id)
        if context is None:
            logger.error("No context for project %s", project_id)
            return Event(
                type=EventType.ERROR,
                project_id=project_id,
                payload={"error": "Project context not found"},
            )

        # Execute plugin
        try:
            output = await plugin.execute(context, event)
        except Exception as exc:
            logger.exception("Plugin %s failed for %s", plugin.name, project_id)
            return Event(
                type=EventType.ERROR,
                project_id=project_id,
                payload={"plugin": plugin.name, "error": str(exc)},
            )

        # Update context based on plugin output
        self._update_context(context, plugin, output)

        # Persist files
        fm = FileManager(base_dir=os.path.join(settings.output_dir, project_id))
        if plugin.name == "pm":
            fm.write_file("spec.md", output.content)
        elif plugin.name == "architect":
            fm.write_file("architecture.md", output.content)
        elif plugin.name == "reviewer":
            fm.write_file("review.md", output.content)
        elif output.files:
            for filepath, content in output.files.items():
                fm.write_file(filepath, content)

        # Git commit
        gm = GitManager(base_dir=settings.output_dir)
        commit_msg = self._commit_message(plugin, output)
        gm.commit(project_id, commit_msg)

        # Notify frontend
        await self._send_terminal(
            project_id, "agent",
            f"{plugin.name.capitalize()} Agent completed: {commit_msg}\n"
        )

        # Update state store
        self.state_store.update_output(project_id, plugin.name, output.content)

        # State transition
        sm = self._state_machines.get(project_id)
        if sm:
            await self._transition_state(project_id, sm, plugin, output)

        # Produce next event
        if plugin.produces:
            return Event(
                type=plugin.produces,
                project_id=project_id,
                payload={
                    "agent": plugin.name,
                    "output": output.content,
                    "metadata": output.metadata,
                },
            )
        return None

    async def _on_error(self, event: Event) -> None:
        """Handle error events."""
        project_id = event.project_id
        error_msg = event.payload.get("error", "Unknown error")
        logger.error("Workflow error for %s: %s", project_id, error_msg)
        await self.ws_manager.send_message(project_id, {
            "type": "error",
            "project_id": project_id,
            "message": error_msg,
        })

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    async def _syntax_check(self, event: Event) -> Event | None:
        """Run syntax validation on generated code."""
        project_id = event.project_id
        context = self._contexts.get(project_id)
        sm = self._state_machines.get(project_id)

        if not context or not sm:
            return None

        code_runner = self._code_runners.get(project_id)
        if not code_runner:
            return Event(
                type=EventType.SYNTAX_CHECKED,
                project_id=project_id,
                payload={"syntax_errors": []},
            )

        syntax_errors = []
        for filepath, content in context.code.items():
            language = code_runner.detect_language(filepath)
            if language:
                is_valid, error = code_runner.validate_syntax(content, language)
                if not is_valid:
                    syntax_errors.append(f"{filepath}: {error}")

        if syntax_errors:
            logger.warning(
                "Syntax errors in %s iteration %d: %s",
                project_id, sm._review_count, syntax_errors,
            )
            for err in syntax_errors:
                await self._send_terminal(project_id, "stderr", err + "\n")

            if sm.can_iterate():
                context.review_feedback = (
                    "The generated code has syntax errors. Please fix them.\n\n"
                    + "\n".join(syntax_errors)
                )
                context.iteration = sm._review_count
                self.state_store.increment_iteration(project_id)

                # Stay in CODING state, loop back to coder
                await self.ws_manager.send_message(project_id, {
                    "type": "agent_status",
                    "project_id": project_id,
                    "agent": "coder",
                    "status": "running",
                    "output": {"summary": f"Fixing {len(syntax_errors)} syntax error(s)..."},
                })
                return Event(
                    type=EventType.ITERATION_STARTED,
                    project_id=project_id,
                    payload={"reason": "syntax_errors", "errors": syntax_errors},
                )
            # Out of iterations — proceed to reviewer for final assessment

        return Event(
            type=EventType.SYNTAX_CHECKED,
            project_id=project_id,
            payload={"syntax_errors": syntax_errors},
        )

    async def _review_decision(self, event: Event) -> Event | None:
        """Decide whether to complete the workflow or iterate."""
        project_id = event.project_id
        context = self._contexts.get(project_id)
        sm = self._state_machines.get(project_id)

        if not context or not sm:
            return None

        review_passed = event.payload.get("metadata", {}).get("passed", False)

        if not review_passed and sm.can_iterate():
            # Set up iteration context
            context.review_feedback = event.payload.get("output", "")
            context.iteration = sm._review_count
            self.state_store.increment_iteration(project_id)

            # Transition back to CODING
            sm.transition_to(WorkflowState.CODING)
            self.state_store.update_state(project_id, WorkflowState.CODING)
            await self._notify_workflow_state(project_id, sm)

            return Event(
                type=EventType.ITERATION_STARTED,
                project_id=project_id,
                payload={"reason": "review_feedback", "review": event.payload.get("output", "")},
            )

        # Workflow complete
        sm.transition_to(WorkflowState.DONE)
        self.state_store.update_state(project_id, WorkflowState.DONE)
        await self._notify_workflow_state(project_id, sm)

        return Event(
            type=EventType.WORKFLOW_COMPLETED,
            project_id=project_id,
            payload={"passed": review_passed},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_context(self, context: AgentContext, plugin: AgentPlugin, output: AgentOutput) -> None:
        """Update the AgentContext with plugin output."""
        if plugin.name == "pm":
            context.spec = output.content
        elif plugin.name == "architect":
            context.architecture = output.content
        elif plugin.name == "coder":
            context.code = output.files
        # Reviewer output is handled via review_feedback on iteration

    def _commit_message(self, plugin: AgentPlugin, output: AgentOutput) -> str:
        """Generate a git commit message for a plugin's output."""
        sm = self._state_machines.get(output.metadata.get("project_id", ""))
        iteration = f" (iteration {sm._review_count})" if sm and sm._review_count > 0 else ""
        msg_map = {
            "pm": "spec: add functional specification",
            "architect": "arch: add system architecture",
            "coder": f"coder: generate code{iteration}",
            "reviewer": f"review: add review report{iteration}",
        }
        return msg_map.get(plugin.name, f"{plugin.name}: update")

    async def _transition_state(
        self, project_id: str, sm: StateMachine, plugin: AgentPlugin, output: AgentOutput
    ) -> None:
        """Update workflow state based on which plugin just completed."""
        state_map = {
            "pm": WorkflowState.PLANNING,
            "architect": WorkflowState.DESIGNING,
            "coder": WorkflowState.CODING,
            "reviewer": WorkflowState.REVIEWING,
        }
        if plugin.name in state_map:
            sm.transition_to(state_map[plugin.name])
            self.state_store.update_state(project_id, state_map[plugin.name])
            await self._notify_workflow_state(project_id, sm)

    async def _send_terminal(self, project_id: str, stream: str, content: str) -> None:
        """Send a terminal output line to the frontend."""
        await self.ws_manager.send_message(project_id, {
            "type": "terminal_output",
            "project_id": project_id,
            "stream": stream,
            "content": content,
        })

    async def _notify_workflow_state(self, project_id: str, sm: StateMachine) -> None:
        """Send workflow state update via WebSocket."""
        from backend.orchestrator.state_machine import WorkflowState as WS
        progress_map = {
            WS.IDLE: 0,
            WS.PLANNING: 10,
            WS.DESIGNING: 30,
            WS.CODING: 50,
            WS.REVIEWING: 80,
            WS.DONE: 100,
        }
        await self.ws_manager.send_message(project_id, {
            "type": "workflow_state",
            "project_id": project_id,
            "state": sm.current.value,
            "overall_progress": progress_map.get(sm.current, 0),
            "iteration_count": sm._review_count,
        })
