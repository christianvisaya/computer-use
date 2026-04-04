"""Tests for actions.py."""

import pytest

from computer_use.actions import parse_action, execute, ActionError


class TestParseAction:
    def test_full_json(self):
        raw = '{"action": "click", "x": 100, "y": 200}'
        result = parse_action(raw)
        assert result == {"action": "click", "x": 100, "y": 200}

    def test_json_with_surrounding_text(self):
        raw = 'Here is my plan:\n{"action": "type", "text": "hello"}\nDone.'
        result = parse_action(raw)
        assert result == {"action": "type", "text": "hello"}

    def test_json_with_reason(self):
        raw = '{"action": "done", "reason": "Task finished"}'
        result = parse_action(raw)
        assert result["action"] == "done"
        assert result["reason"] == "Task finished"

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError):
            parse_action("not json at all")

    def test_xml_tool_call_launch(self):
        raw = (
            "I'll open Google Chrome now.\n\n"
            '<invoke name="launch">\n'
            '<parameter name="app">Google Chrome</parameter>\n'
            "</invoke>\n"
        )
        result = parse_action(raw)
        assert result == {"action": "launch", "app": "Google Chrome"}

    def test_xml_tool_call_with_multiple_params(self):
        raw = (
            '<invoke name="hotkey">\n'
            '<parameter name="keys">["ctrl", "a"]</parameter>\n'
            "</invoke>\n"
        )
        result = parse_action(raw)
        assert result["action"] == "hotkey"
        assert result["keys"] == '["ctrl", "a"]'


class TestExecute:
    def test_parse_wait_action(self):
        action = {"action": "wait", "seconds": 0.01}
        result = execute(action)
        assert "waited" in result

    def test_parse_done_action(self):
        action = {"action": "done", "reason": "All good"}
        result = execute(action)
        assert "All good" in result

    def test_parse_unknown_action(self):
        action = {"action": "fly", "x": 10}
        result = execute(action)
        assert "unknown action" in result

    def test_move_to_action_format(self):
        action = {"action": "move_to", "x": 150, "y": 300}
        result = execute(action)
        assert "150" in result
        assert "300" in result

    def test_press_action_format(self):
        action = {"action": "press", "key": "enter"}
        result = execute(action)
        assert "enter" in result

    def test_scroll_action_format(self):
        action = {"action": "scroll", "x": 0, "y": -300}
        result = execute(action)
        assert "-300" in result

    def test_type_action_format(self):
        action = {"action": "type", "text": "hello world"}
        result = execute(action)
        assert "hello world" in result
