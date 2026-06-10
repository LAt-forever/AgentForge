"""Tests for StaticAnalyzer."""

from unittest.mock import MagicMock

from backend.tools.static_analyzer import StaticAnalyzer, Issue
from backend.tools.docker_sandbox import ExecutionResult


class TestIssueModel:
    def test_issue_fields(self):
        issue = Issue(
            tool="pylint", file="main.py", line=10, column=4,
            severity="error", message="undefined name", code="E0602",
        )
        assert issue.tool == "pylint"
        assert issue.line == 10
        assert issue.severity == "error"


class TestAnalyzePython:
    def test_parses_pylint_json(self):
        """pylint JSON output is parsed into Issues."""
        sandbox = MagicMock()
        pylint_json = (
            '[{"type":"error","module":"main","obj":"","line":3,"column":0,'
            '"path":"main.py","symbol":"undefined-variable",'
            '"message":"Undefined variable x","message-id":"E0602"}]'
        )
        sandbox.execute.side_effect = [
            ExecutionResult(stdout=pylint_json, stderr="", exit_code=1),
            ExecutionResult(stdout="", stderr="", exit_code=0),
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])

        pylint_issues = [i for i in issues if i.tool == "pylint"]
        assert len(pylint_issues) == 1
        assert pylint_issues[0].severity == "error"
        assert pylint_issues[0].line == 3
        assert pylint_issues[0].code == "E0602"

    def test_parses_mypy_output(self):
        """mypy text output is parsed into Issues."""
        sandbox = MagicMock()
        mypy_out = "main.py:5:1: error: Name 'foo' is not defined  [name-defined]\n"
        sandbox.execute.side_effect = [
            ExecutionResult(stdout="[]", stderr="", exit_code=0),  # pylint clean
            ExecutionResult(stdout=mypy_out, stderr="", exit_code=1),  # mypy
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])

        mypy_issues = [i for i in issues if i.tool == "mypy"]
        assert len(mypy_issues) == 1
        assert mypy_issues[0].line == 5
        assert mypy_issues[0].severity == "error"

    def test_no_files_returns_empty(self):
        """No python files → no analysis, empty list."""
        sandbox = MagicMock()
        analyzer = StaticAnalyzer(sandbox)
        assert analyzer.analyze_python("proj1", []) == []
        sandbox.execute.assert_not_called()

    def test_malformed_pylint_output_is_safe(self):
        """Garbage pylint output does not crash; yields no pylint issues."""
        sandbox = MagicMock()
        sandbox.execute.side_effect = [
            ExecutionResult(stdout="not json", stderr="", exit_code=1),
            ExecutionResult(stdout="", stderr="", exit_code=0),
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])
        assert [i for i in issues if i.tool == "pylint"] == []
