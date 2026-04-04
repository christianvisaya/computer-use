"""Main agent: screenshot → AI → action → repeat loop."""

import sys
import time
from termcolor import colored

from computer_use import ai, actions, screenshot


SYSTEM_PROMPT_TEMPLATE = """You are a computer control agent. You see the user's screen and decide the next action.

CRITICAL KEYBOARD-FIRST RULE: You MUST prefer keyboard shortcuts over mouse clicks. ONLY use mouse when keyboard navigation is impossible.

**Keyboard shortcuts (USE THESE, NOT click):**
- Open Chrome: `launch("Google Chrome")`
- Address bar / URL: `hotkey(["command", "l"])` on macOS, `hotkey(["ctrl", "l"])` on Linux/Windows
- Type URL after focusing address bar: use `type` action
- New tab: `hotkey(["command", "t"])`
- Switch app: `hotkey(["command", "tab"])`
- Select all: `hotkey(["command", "a"])`
- Copy: `hotkey(["command", "c"])`, Paste: `hotkey(["command", "v"])`

You must respond with TWO things:
1. Your ANALYSIS: Describe what you see in the screenshot and what you plan to do
2. A JSON action object

Format your response like this:
ANALYSIS: I can see [what you see]. I will [your plan].
ACTION: {"action": "...", ...}

Example:
ANALYSIS: I see the Chrome icon in the dock at bottom of screen. I will click it to open Chrome.
ACTION: {"action": "launch", "app": "Google Chrome"}

Example:
ANALYSIS: Chrome is open with an empty address bar. I will press Cmd+L to focus the address bar, then type the YouTube URL.
ACTION: {"action": "hotkey", "keys": ["command", "l"]}

Example:
ANALYSIS: Address bar is now focused. I will type the YouTube search URL.
ACTION: {"action": "type", "text": "https://www.youtube.com/results?search_query=dayz+jlk"}

Available actions (in priority order — use keyboard actions FIRST):

1. launch — Open app (only if NOT already open)
2. hotkey — Key combo (PREFERRED — use over click)
3. type — Type text
4. press — Single key (enter, tab, escape)
5. scroll — Scroll (usually avoidable)
6. click — LAST RESORT ONLY

Key rules:
- KEYBOARD FIRST: hotkey > type > press > click
- NEVER click into a text field then type — just use `type` directly
- For URLs: hotkey for address bar first, then `type` for URL
- If Chrome ALREADY OPEN: do NOT launch again. Click its window or use Cmd+Tab.
- After any GUI change, wait and re-screenshot to verify state
- macOS: Command=⌘, Option=⌥, Control=ctrl
- Linux: Super=⊞
- Windows: Win key

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

        # Parse reasoning and action from response
        try:
            reasoning, action = actions.parse_action_with_reasoning(response)
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] Could not parse AI response: {e}", "red"))
            print(f"  Raw response: {response[:500]}")
            break

        # Show AI's reasoning
        if reasoning:
            print(colored(f"[Step {step}/{max_steps}] 💭 {reasoning}", "magenta"))

        action_type = action.get("action", "")

        # Execute
        try:
            result = actions.execute_with_retries(action)
        except Exception as e:
            print(colored(f"[Step {step}/{max_steps}] Action execution failed: {e}", "red"))
            break

        # Log
        if action_type == "done":
            print(colored(f"[Step {step}/{max_steps}] ✓ {result}", "green"))
            break

        print(colored(f"[Step {step}/{max_steps}] → {result}", "cyan"))

        if step >= max_steps:
            print(colored(f"Reached max steps ({max_steps}). Stopping.", "yellow"))
            break

        # Wait before next screenshot
        time.sleep(wait_after_action)

    if step >= max_steps:
        print(colored("Max steps reached. Task may be incomplete.", "yellow"))
