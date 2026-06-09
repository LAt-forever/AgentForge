"""Tests for the StateMachine."""

import pytest

from backend.core.state_store import WorkflowState
from backend.orchestrator.state_machine import StateMachine


class TestStateMachine:
    def test_initial_state(self):
        sm = StateMachine()
        assert sm.current == WorkflowState.IDLE

    def test_idle_to_planning(self):
        sm = StateMachine()
        assert sm.transition_to(WorkflowState.PLANNING) is True
        assert sm.current == WorkflowState.PLANNING

    def test_planning_to_designing(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        assert sm.transition_to(WorkflowState.DESIGNING) is True
        assert sm.current == WorkflowState.DESIGNING

    def test_designing_to_coding(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        assert sm.transition_to(WorkflowState.CODING) is True
        assert sm.current == WorkflowState.CODING

    def test_coding_to_reviewing(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        sm.transition_to(WorkflowState.CODING)
        assert sm.transition_to(WorkflowState.REVIEWING) is True
        assert sm.current == WorkflowState.REVIEWING

    def test_reviewing_to_done(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        sm.transition_to(WorkflowState.CODING)
        sm.transition_to(WorkflowState.REVIEWING)
        assert sm.transition_to(WorkflowState.DONE) is True
        assert sm.current == WorkflowState.DONE

    def test_reviewing_back_to_coding(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        sm.transition_to(WorkflowState.CODING)
        sm.transition_to(WorkflowState.REVIEWING)
        assert sm.transition_to(WorkflowState.CODING) is True
        assert sm.current == WorkflowState.CODING

    def test_invalid_transition(self):
        sm = StateMachine()
        assert sm.transition_to(WorkflowState.DONE) is False
        assert sm.current == WorkflowState.IDLE

    def test_review_loop_limit(self):
        sm = StateMachine(max_iterations=3)
        # First pass: IDLE -> PLANNING -> DESIGNING -> CODING -> REVIEWING
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        sm.transition_to(WorkflowState.CODING)
        sm.transition_to(WorkflowState.REVIEWING)  # review_count = 1
        assert sm.can_iterate() is True

        # Loop back to CODING 1st time
        sm.transition_to(WorkflowState.CODING)
        sm.transition_to(WorkflowState.REVIEWING)  # review_count = 2
        assert sm.can_iterate() is True

        # Loop back to CODING 2nd time
        sm.transition_to(WorkflowState.CODING)
        sm.transition_to(WorkflowState.REVIEWING)  # review_count = 3
        assert sm.can_iterate() is False

        # 3rd loop back should fail (max_iterations reached)
        assert sm.transition_to(WorkflowState.CODING) is False
        assert sm.current == WorkflowState.REVIEWING

    def test_get_history(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        history = sm.get_history()
        assert history == [WorkflowState.PLANNING, WorkflowState.DESIGNING]

    def test_reset(self):
        sm = StateMachine()
        sm.transition_to(WorkflowState.PLANNING)
        sm.transition_to(WorkflowState.DESIGNING)
        sm.reset()
        assert sm.current == WorkflowState.IDLE
        assert sm.get_history() == []
        assert sm.can_iterate() is True
