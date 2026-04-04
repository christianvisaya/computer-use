"""Load configuration from workspace .env and AGENTS.md."""

import os

from dotenv import load_dotenv


def load_workspace(workspace_path: str | None = None) -> dict:
    """Load .env and AGENTS.md from the workspace directory.

    Returns a dict with keys:
      - ai_provider: str (minimax | ollama | openai | anthropic)
      - minimax_api_key, minimax_api_url, minimax_model
      - ollama_base_url, ollama_model
      - openai_api_key, openai_base_url, openai_model
      - anthropic_api_key, anthropic_model
      - agents_md: str (contents of AGENTS.md or "")
      - workspace_dir: Path
    """
    if workspace_path is None:
        workspace_path = os.path.join(os.getcwd(), "computer-use-workspace")

    workspace_dir = os.path.abspath(workspace_path)
    env_path = os.path.join(workspace_dir, ".env")

    config = {
        "workspace_dir": workspace_dir,
        "agents_md": "",
        "ai_provider": "minimax",
        # MiniMax defaults
        "minimax_api_key": "",
        "minimax_api_url": "https://api.minimax.io",
        "minimax_model": "MiniMax-M2.7",
        # Ollama defaults
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.2-vision",
        # OpenAI defaults
        "openai_api_key": "",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_model": "gpt-4o",
        # Anthropic defaults
        "anthropic_api_key": "",
        "anthropic_model": "claude-sonnet-4-20250514",
    }

    if os.path.isfile(env_path):
        load_dotenv(env_path, override=True)
        config["ai_provider"] = os.getenv("AI_PROVIDER", "minimax")
        config["minimax_api_key"] = os.getenv("MINIMAX_API_KEY", "")
        config["minimax_api_url"] = os.getenv("MINIMAX_API_URL", "https://api.minimax.io")
        config["minimax_model"] = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
        config["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        config["ollama_model"] = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
        config["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
        config["openai_base_url"] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        config["openai_model"] = os.getenv("OPENAI_MODEL", "gpt-4o")
        config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
        config["anthropic_model"] = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    agents_md_path = os.path.join(workspace_dir, "AGENTS.md")
    if os.path.isfile(agents_md_path):
        with open(agents_md_path, "r") as f:
            config["agents_md"] = f.read()

    return config


def validate_config(config: dict) -> None:
    """Raise ValueError with a clear message if required config is missing."""
    provider = config["ai_provider"]

    if provider == "minimax":
        if not config["minimax_api_key"]:
            raise ValueError(
                "MINIMAX_API_KEY is required when AI_PROVIDER=minimax. "
                "Set it in your .env file or as an environment variable."
            )
    elif provider == "openai":
        if not config["openai_api_key"]:
            raise ValueError(
                "OPENAI_API_KEY is required when AI_PROVIDER=openai. "
                "Set it in your .env file or as an environment variable."
            )
    elif provider == "ollama":
        # Ollama needs no key
        pass
    elif provider == "anthropic":
        if not config["anthropic_api_key"]:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when AI_PROVIDER=anthropic. "
                "Set it in your .env file or as an environment variable."
            )
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}. Use minimax | ollama | openai | anthropic.")
