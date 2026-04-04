"""Execute actions returned by the AI agent."""

import json
import time
from typing import Any

import pyautogui

from computer_use.platform import launch_app, run_terminal

# Fail-safe: move mouse to corner to abort
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class ActionError(Exception):
    """Raised when an action fails after retries."""


def parse_action(raw: str) -> dict[str, Any]:
    """Extract action dict from AI response text.

    Handles two formats:
      - JSON:      {"action": "launch", "app": "Google Chrome"}
      - XML tool:  <invoke name="launch">...</invoke>

    """
    raw = raw.strip()

    # Try JSON first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    # Try XML tool call format: <invoke name="action_name">...\n<parameter name="key">value</parameter>...
    invoke_start = raw.find('<invoke name="')
    if invoke_start != -1:
        name_start = invoke_start + len('<invoke name="')
        name_end = raw.find('"', name_start)
        action_name = raw[name_start:name_end]

        action: dict[str, Any] = {"action": action_name}

        # Extract all <parameter name="key">value</parameter> pairs
        param_pos = 0
        while True:
            param_idx = raw.find('<parameter name="', param_pos)
            if param_idx == -1 or (invoke_start > 0 and param_idx > invoke_start + 1000):
                break
            k_start = param_idx + len('<parameter name="')
            k_end = raw.find('"', k_start)
            key = raw[k_start:k_end]
            val_start = raw.find(">", param_idx) + 1
            val_end = raw.find("</parameter>", val_start)
            value = raw[val_start:val_end].strip()
            action[key] = value
            param_pos = val_end

        if action.get("action"):
            return action

    raise ValueError(f"Could not parse action from AI response: {raw!r}")


def execute(action: dict[str, Any]) -> str:
    """Execute a single action dict and return a human-readable summary."""
    action_type = action.get("action", "")

    try:
        if action_type == "click":
            x = int(action["x"])
            y = int(action["y"])
            button = action.get("button", "left")
            pyautogui.click(x, y, button=button)
            return f"click at ({x}, {y})"

        elif action_type == "double_click":
            x = int(action["x"])
            y = int(action["y"])
            pyautogui.doubleClick(x, y)
            return f"double-click at ({x}, {y})"

        elif action_type == "right_click":
            x = int(action["x"])
            y = int(action["y"])
            pyautogui.click(x, y, button="right")
            return f"right-click at ({x}, {y})"

        elif action_type == "move_to":
            x = int(action["x"])
            y = int(action["y"])
            pyautogui.moveTo(x, y)
            return f"moved to ({x}, {y})"

        elif action_type == "type":
            text = action["text"]
            pyautogui.typewrite(text)
            return f"typed: {text!r}"

        elif action_type == "press":
            key = action["key"]
            pyautogui.press(key)
            return f"pressed: {key}"

        elif action_type == "hotkey":
            keys = action["keys"]
            pyautogui.hotkey(*keys)
            return f"hotkey: {'+'.join(keys)}"

        elif action_type == "launch":
            app = action["app"]
            launch_app(app, action.get("linux_window_class"), action.get("win_program"))
            return f"launched: {app}"

        elif action_type == "terminal":
            command = action["command"]
            timeout = int(action.get("timeout", 10))
            output = run_terminal(command, timeout)
            return f"terminal output ({len(output)} chars)"

        elif action_type == "scroll":
            x = int(action.get("x", 0))
            y = int(action["y"])
            pyautogui.scroll(y, x=x)
            return f"scrolled y={y}"

        elif action_type == "wait":
            seconds = float(action.get("seconds", 1))
            time.sleep(seconds)
            return f"waited {seconds}s"

        elif action_type == "done":
            return f"done: {action.get('reason', 'Task complete')}"

        else:
            return f"unknown action: {action_type}"

    except Exception as e:
        raise ActionError(f"Action '{action_type}' failed: {e}") from e


def execute_with_retries(action: dict[str, Any], retries: int = 2) -> str:
    """Execute an action with up to `retries` attempts."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return execute(action)
        except ActionError as e:
            last_error = e
            if attempt < retries:
                time.sleep(1)
    raise ActionError(f"Action failed after {retries + 1} attempts: {last_error}") from last_error
