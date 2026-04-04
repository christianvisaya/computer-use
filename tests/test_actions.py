"""Tests for actions.py."""

import pytest

from computer_use.actions import parse_action, parse_action_with_reasoning, execute, ActionError


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

    def test_click_coordinate_format(self):
        """AI models may return {"coordinate": [x, y]} instead of {"x": ..., "y": ...}"""
        action = {"action": "click", "coordinate": [1175, 199]}
        result = execute(action)
        assert "1175" in result
        assert "199" in result

    def test_double_click_coordinate_format(self):
        action = {"action": "double_click", "coordinate": [500, 300]}
        result = execute(action)
        assert "500" in result
        assert "300" in result


class TestParseActionWithReasoning:
    def test_parses_analysis_and_action(self):
        raw = (
            "ANALYSIS: I see the Chrome dock icon. I will click it to open Chrome.\n"
            'ACTION: {"action": "launch", "app": "Google Chrome"}'
        )
        reasoning, action = parse_action_with_reasoning(raw)
        assert "Chrome" in reasoning
        assert action["action"] == "launch"
        assert action["app"] == "Google Chrome"

    def test_parses_reasoning_only_no_action_raises(self):
        raw = "ANALYSIS: I see the desktop but I'm not sure what to do."
        with pytest.raises(ValueError):
            parse_action_with_reasoning(raw)

    def test_backward_compatible_without_analysis(self):
        """parse_action_with_reasoning falls back to plain JSON when no ANALYSIS: marker."""
        raw = '{"action": "press", "key": "enter"}'
        reasoning, action = parse_action_with_reasoning(raw)
        assert reasoning == ""
        assert action["action"] == "press"

    def test_strips_code_fence_from_action(self):
        raw = "ANALYSIS: I'll press enter.\nACTION: ```json\n{\"action\": \"press\", \"key\": \"enter\"}\n```"
        _, action = parse_action_with_reasoning(raw)
        assert action["action"] == "press"
