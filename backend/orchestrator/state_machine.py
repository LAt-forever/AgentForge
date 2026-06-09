"""State machine for managing workflow transitions."""

from dataclasses import dataclass
from typing import Optional

from backend.core.state_store import WorkflowState


@dataclass
class Transition:
    """A valid state transition."""

    from_state: WorkflowState
    to_state: WorkflowState
    condition: Optional[callable] = None


class StateMachine:
    """Manages workflow state transitions with iteration limits."""

    TRANSITIONS = [
        Transition(WorkflowState.IDLE, WorkflowState.PLANNING),
        Transition(WorkflowState.PLANNING, WorkflowState.DESIGNING),
        Transition(WorkflowState.DESIGNING, WorkflowState.CODING),
        Transition(WorkflowState.CODING, WorkflowState.REVIEWING),
        Transition(WorkflowState.REVIEWING, WorkflowState.DONE),
        Transition(WorkflowState.REVIEWING, WorkflowState.CODING),  # loop back for fixes
    ]

    def __init__(self, max_iterations: int = 3):
        self.current = WorkflowState.IDLE
        self.max_iterations = max_iterations
        self._review_count = 0
        self._history = []

    def transition_to(self, new_state: WorkflowState) -> bool:
        """Attempt to transition to a new state.

        Returns True if the transition was valid and applied, False otherwise.
        """
        # Check if this is a valid transition
        valid = False
        for t in self.TRANSITIONS:
            if t.from_state == self.current and t.to_state == new_state:
                valid = True
                break

        if not valid:
            return False

        # If REVIEWING -> CODING, check iteration limit
        if self.current == WorkflowState.REVIEWING and new_state == WorkflowState.CODING:
            if self._review_count >= self.max_iterations:
                return False

        # Increment review count when entering REVIEWING
        if new_state == WorkflowState.REVIEWING:
            self._review_count += 1

        self._history.append(new_state)
        self.current = new_state
        return True

    def can_iterate(self) -> bool:
        """Return whether more review iterations are allowed."""
        return self._review_count < self.max_iterations

    def get_history(self) -> list[WorkflowState]:
        """Return the history of state transitions."""
        return list(self._history)

    def reset(self) -> None:
        """Reset the state machine to initial state."""
        self.current = WorkflowState.IDLE
        self._review_count = 0
        self._history = []
