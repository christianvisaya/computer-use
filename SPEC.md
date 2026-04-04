# computer-use — SPEC

## 1. Overview

**Goal**: A stateless CLI tool that takes a natural-language instruction, controls the local GUI (mouse, keyboard, app launching, terminal) by viewing the screen after each action, and executes multi-step tasks autonomously.

**Core loop**:
```
screenshot → send to AI (vision model) → AI decides next action → execute → repeat
```

**Target OSes**: macOS, Ubuntu (Linux), Windows — with a unified action interface per OS.

**AI Providers**: MiniMax (cloud), Ollama (local), OpenAI-compatible (cloud/local), Anthropic Claude (cloud).

---

## 2. Project Structure

```
computer-use/
├── src/
│   └── computer_use/
│       ├── __init__.py
│       ├── cli.py              # CLI entry: computer-use --instruction="..."
│       ├── agent.py            # Main screenshot→act loop
│       ├── screenshot.py       # Cross-platform screen capture
│       ├── ai.py               # AI provider clients (MiniMax, Ollama, OpenAI, Anthropic)
│       ├── actions.py          # Action executor (pyautogui + subprocess)
│       ├── workspace.py        # Load .env + AGENTS.md from workspace
│       └── platform.py         # OS detection + platform-specific helpers
├── tests/
│   ├── __init__.py
│   ├── test_actions.py
│   ├── test_ai.py
│   ├── test_platform.py
│   ├── test_screenshot.py
│   └── test_workspace.py
├── computer-use-workspace/    # Example workspace (gitignored)
│   ├── .env
│   └── AGENTS.md
├── pyproject.toml
├── README.md
├── SPEC.md
└── .gitignore
```

---

## 3. CLI Interface

```bash
computer-use --instruction="open google chrome and search youtube for dayz jlk"
computer-use --instruction="open terminal and run htop" --workspace /path/to/workspace
computer-use --instruction="open firefox and go to github.com" --max-steps 30
```

**Arguments:**
| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--instruction` | Yes | — | Natural-language instruction |
| `--workspace` | No | `./computer-use-workspace` | Path to workspace folder |
| `--max-steps` | No | 50 | Max screenshot→act loops before giving up |
| `--wait-after-action` | No | `1.0` | Seconds to wait after each action |

---

## 4. AI Provider Architecture

Four providers are supported. Selection is driven by `.env` (`AI_PROVIDER`).

### 4.1 Provider Selection

| Provider | `AI_PROVIDER` value | Recommended model |
|-----------|---------------------|------------------|
| MiniMax | `minimax` | MiniMax-M2.7 |
| Ollama | `ollama` | qwen3.5:9b, llama3.2-vision |
| OpenAI-compatible | `openai` | gpt-4o |
| Anthropic | `anthropic` | claude-sonnet-4-20250514 |

If `AI_PROVIDER` is unset, default is `minimax`.

### 4.2 MiniMax

```env
AI_PROVIDER=minimax
MINIMAX_API_KEY=your_key_here
MINIMAX_API_URL=https://api.minimax.io
MINIMAX_MODEL=MiniMax-M2.7
```

Image format: `data:image/jpeg;base64,<b64>` inside `image_url.url` field.

### 4.3 Ollama (Local)

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b
```

No API key required. Ollama must be running (`ollama serve`).

### 4.4 OpenAI-Compatible

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### 4.5 Anthropic (Claude)

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

Image format: base64 JPEG in `image.source.data` with `image.source.type: "base64"`.

---

## 5. AI Prompt (System)

The AI receives:
- **System prompt**: built-in prompt + contents of `AGENTS.md`
- **User message**: current screenshot + `INSTRUCTION: <instruction>`
- **Temperature**: 0.1

### 5.1 Built-in System Prompt

```
You are a computer control agent. You see the user's screen and decide the next action.

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

6. press — Press a special key
   {{ "action": "press", "key": "enter" }}
   {{ "action": "press", "key": "tab" }}

7. hotkey — Press key combination (KEYBOARD-FIRST — prefer over click)
   {{ "action": "hotkey", "keys": ["ctrl", "a"] }}
   {{ "action": "hotkey", "keys": ["command", "tab"] }}

8. launch — Open an application (only if app is NOT already open)
   {{ "action": "launch", "app": "Google Chrome" }}
   {{ "action": "launch", "app": "chrome", "linux_window_class": "google-chrome" }}
   {{ "action": "launch", "app": "chrome", "win_program": "chrome" }}

9. terminal — Run a shell command
   {{ "action": "terminal", "command": "ls -la", "timeout": 10 }}

10. scroll — Scroll the mouse
    {{ "action": "scroll", "x": 0, "y": -300 }}

11. wait — Just wait
    {{ "action": "wait", "seconds": 2 }}

12. done — Task is complete
    {{ "action": "done", "reason": "youtube.com is open and playing" }}

Important rules:
- ALWAYS inspect the screenshot carefully before acting.
- KEYBOARD-FIRST: Prefer hotkeys over mouse. Only use click when keyboard won't work.
- If Chrome or target app is ALREADY OPEN, do NOT launch again. Click its window or use ⌘Tab.
- Use ⌘L (macOS) or Ctrl+L to focus address bar before typing URLs.
- After ANY GUI change, take another screenshot to verify.
- macOS: Command=⌘, Option=⌥, Control=ctrl
- Linux: Super=⊞
- Windows: Win key
```

### 5.2 AGENTS.md

The contents of `workspace/AGENTS.md` are appended to the system prompt. Use it to customize agent behavior, add shortcuts, or define app-specific rules.

---

## 6. Config / .env

```env
# === Provider selection ===
AI_PROVIDER=anthropic   # minimax | ollama | openai | anthropic

# === Anthropic (recommended) ===
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# === MiniMax ===
MINIMAX_API_KEY=...
MINIMAX_API_URL=https://api.minimax.io
MINIMAX_MODEL=MiniMax-M2.7

# === Ollama (local) ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b

# === OpenAI ===
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

---

## 7. Screenshot Capture

- macOS: `screencapture -x -t jpg -` → fallback to PIL `ImageGrab.grab()`
- Linux/Windows: PIL `ImageGrab.grab()`
- Output: JPEG quality 80, base64-encoded (format varies by provider)

---

## 8. Action Execution

| Action | macOS | Linux | Windows |
|--------|-------|-------|---------|
| `launch` | `open -a "App"` | `xdg-open` / `gio open` | `start ""` |
| `terminal` | `bash -c` | `bash -c` | `cmd /c` |
| `hotkey/press/type/click` | pyautogui | pyautogui | pyautogui |

App name normalization maps common aliases (`chrome` → `Google Chrome`, etc.) for macOS `open -a`.

**Error handling**: Action retry up to 2x with 1s wait. If still failing → `done` with reason.

---

## 9. Agent Loop

```
1. Load workspace (.env + AGENTS.md), detect AI provider
2. Capture screenshot
3. Build messages: system prompt + AGENTS.md + screenshot + instruction
4. Call AI provider
5. Parse JSON from response (handles JSON and XML tool-call formats)
6. Execute action
7. Log (cyan=action, green=done, red=error)
8. If done → exit. If step >= max_steps → warn and exit.
9. Wait, goto step 2
```

---

## 10. Dependencies

```
pyautogui>=0.9.54
Pillow>=10.0.0
python-dotenv>=1.0.0
requests>=2.31.0
termcolor>=2.4.0
```

---

## 11. Installation

```bash
pip install -e .
# or
pip install .
```

---

## 12. Acceptance Criteria

- [x] `computer-use --instruction="open terminal"` launches terminal on current OS
- [x] Each step shows colored console output
- [x] `.env` missing required keys → clear error, no crash
- [x] `AGENTS.md` is loaded and appended to system prompt
- [x] Screenshot taken after each action
- [x] `action: done` stops the loop
- [x] `max_steps` limit enforced
- [x] Works on macOS, Linux, Windows
- [x] Ollama: clear error if not running
- [x] MiniMax/OpenAI/Anthropic: clear error on missing API key
- [x] App name normalization for common macOS apps
- [x] Keyboard-first behavior via AGENTS.md shortcuts
