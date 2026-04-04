"""Main agent: screenshot → AI → action → repeat loop."""

import sys
import time
from termcolor import colored

from computer_use import ai, actions, screenshot


SYSTEM_PROMPT_TEMPLATE = """You are a computer control agent. You see the user's screen and decide the next action.

You must respond with a JSON object describing ONE action to take right now.

Available action types:

1. click — Move mouse and click
   {{ "action": "click", "x": 150, "y": 300, "button": "left" }}

2. double_click — Double click
   {{ "action": "double_click", "x": 150, "y": 300, "button": "left" }}

3. right_click — Right-click (context menu)
   {{ "action": "right_click", "x": 150, "y": 300 }}

4. move_to — Move mouse without clicking
   {{ "action": "move_to", "x": 150, "y": 300 }}

5. type — Type text
   {{ "action": "type", "text": "hello world" }}

6. press — Press a special key (see pyautogui.KEYBOARD_KEYS)
   {{ "action": "press", "key": "enter" }}
   {{ "action": "press", "key": "tab" }}
   {{ "action": "press", "key": "ctrl" }}  # modifier only

7. hotkey — Press key combination
   {{ "action": "hotkey", "keys": ["ctrl", "a"] }}  # Select all
   {{ "action": "hotkey", "keys": ["command", "tab"] }}  # macOS app switch

8. launch — Open an application
   {{ "action": "launch", "app": "Google Chrome" }}    # macOS
   {{ "action": "launch", "app": "chrome", "linux_window_class": "google-chrome" }}
   {{ "action": "launch", "app": "chrome", "win_program": "chrome" }}   # Windows

9. terminal — Run a shell command and wait for it to finish
   {{ "action": "terminal", "command": "ls -la", "timeout": 10 }}

10. scroll — Scroll the mouse
    {{ "action": "scroll", "x": 0, "y": -300 }}   # negative = up, positive = down

11. wait — Just wait
    {{ "action": "wait", "seconds": 2 }}

12. done — Task is complete
    {{ "action": "done", "reason": "Browser is open on youtube.com" }}

Important rules:
- ALWAYS inspect the screenshot carefully before acting. Identify the correct x,y coordinates.
- After ANY action that causes a GUI change, take another screenshot to verify before continuing.
- For typing, use the `type` action. For single keys, use `press`.
- If pyautogui fails (e.g., GUI not ready), retry up to 2 times with 1s wait.
- The screen resolution and UI scale matters. Use coordinates that match what you see.
- macOS: Command key = "command", Control = "ctrl", Option = "option"
- Linux: Super/Win key = "super"
- Windows: Win key = "win"
- If you are uncertain about an element's exact position, move the mouse first then click.
- IMPORTANT: If Chrome (or the target app) is already open, do NOT launch it again. Click its window or use it directly.

{agents_md}
"""


def run(
    instruction: str,
    config: dict,
    max_steps: int = 50,
    wait_after_action: float = 1.0,
) -> None:
    """Run the screenshot→act loop."""
    provider = config["ai_provider"]
    agents_md = config.get("agents_md", "")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(agents_md=agents_md)

    step = 0
    while step < max_steps:
        step += 1

        # Capture screen
        try:
            image_bytes = screenshot.capture_screen()
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] Screenshot failed: {e}", "red"))
            break

        # Call AI
        try:
            response = ai.chat(
                provider=provider,
                instruction=instruction,
                image_bytes=image_bytes,
                system_prompt=system_prompt,
                minimax_api_key=config.get("minimax_api_key", ""),
                minimax_api_url=config.get("minimax_api_url", "https://api.minimax.io"),
                minimax_model=config.get("minimax_model", "MiniMax-Text-01"),
                ollama_base_url=config.get("ollama_base_url", "http://localhost:11434"),
                ollama_model=config.get("ollama_model", "llama3.2-vision"),
                openai_api_key=config.get("openai_api_key", ""),
                openai_base_url=config.get("openai_base_url", "https://api.openai.com/v1"),
                openai_model=config.get("openai_model", "gpt-4o"),
                anthropic_api_key=config.get("anthropic_api_key", ""),
                anthropic_model=config.get("anthropic_model", "claude-sonnet-4-20250514"),
            )
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] AI call failed: {e}", "red"))
            break

        # Parse action
        try:
            action = actions.parse_action(response)
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] Could not parse AI response: {e}", "red"))
            print(f"  Raw response: {response[:300]}")
            break

        action_type = action.get("action", "")

        # Execute
        try:
            result = actions.execute_with_retries(action)
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] Action execution failed: {e}", "red"))
            break

        # Log
        if action_type == "done":
            print(colored(f"[Step {step}/{max_steps}] {result}", "green"))
            break

        print(colored(f"[Step {step}/{max_steps}] → {result}", "cyan"))

        if step >= max_steps:
            print(colored(f"Reached max steps ({max_steps}). Stopping.", "yellow"))
            break

        # Wait before next screenshot
        time.sleep(wait_after_action)

    if step >= max_steps:
        print(colored("Max steps reached. Task may be incomplete.", "yellow"))
