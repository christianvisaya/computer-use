# computer-use

AI-powered GUI automation. Give it an instruction, watch it work.

```
computer-use --instruction="open google chrome and search youtube for dayz jlk"
```

## How it works

1. Takes a screenshot of your screen
2. Sends it to a vision-capable AI model
3. AI decides the next action (click, type, hotkey, launch, etc.)
4. Executes the action
5. Repeats until the task is done

## Setup

### 1. Install

```bash
git clone <repo>
cd computer-use
pip install -e .
```

### 2. Create your workspace

```bash
mkdir -p my-workspace
cd my-workspace
```

### 3. Create `.env`

**Anthropic (recommended — Claude Sonnet 4 has excellent vision):**
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Ollama (local, free):**
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b
```

**MiniMax:**
```env
AI_PROVIDER=minimax
MINIMAX_API_KEY=...
MINIMAX_MODEL=MiniMax-M2.7
```

**OpenAI:**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### 4. (Optional) Create `AGENTS.md`

Add extra instructions for the AI. See `computer-use-workspace/AGENTS.md` for examples — keyboard shortcuts, OS-specific rules, efficiency guidelines.

## Usage

```bash
# Basic
computer-use --instruction="open google chrome and search for cats"

# Custom workspace
computer-use --workspace /path/to/workspace --instruction="..." --max-steps 30

# Slower systems
computer-use --instruction="..." --wait-after-action 2.0
```

## Tips

- **Keyboard-first**: The AI prefers keyboard shortcuts over mouse clicks. Add app-specific shortcuts in `AGENTS.md`.
- **Be specific**: "open github and star the anthropic/claude-code repo" works better than vague instructions.
- **Max steps**: If tasks are taking too long, increase `--max-steps`. If it's looping, reduce it.
- **Screen Recording**: On macOS, grant Screen Recording permission in System Settings → Privacy & Security → Screen Recording, or screenshots will fail.

## Troubleshooting

**"Screenshot failed" on macOS**: Grant Screen Recording permission to Terminal/Python in System Settings.

**AI keeps relaunching the same app**: Use a vision model with strong reasoning (Claude Sonnet 4, qwen3.5:9b). Small models like gemma3:4b may ignore visual state.

**"Unable to find application"**: App name not recognized. Common names are auto-normalized (chrome → Google Chrome), but some apps may need the exact bundle name.

## Supported Actions

| Action | Description |
|--------|-------------|
| `click` | Mouse click at x,y |
| `double_click` | Double click |
| `right_click` | Context menu |
| `move_to` | Move mouse |
| `type` | Type text |
| `press` | Single key (enter, tab, etc.) |
| `hotkey` | Key combo (⌘C, Ctrl+V, etc.) |
| `launch` | Open app |
| `terminal` | Run shell command |
| `scroll` | Scroll mouse |
| `wait` | Pause |
| `done` | Task complete |
