"""Tests for workspace.py."""

import os
import tempfile
import pytest

from computer_use.workspace import load_workspace, validate_config


class TestLoadWorkspace:
    def test_load_minimax_env(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            with open(env_path, "w") as f:
                f.write("AI_PROVIDER=minimax\n")
                f.write("MINIMAX_API_KEY=mykey123\n")
                f.write("MINIMAX_MODEL=MiniMax-Text-01\n")

            config = load_workspace(td)

            assert config["ai_provider"] == "minimax"
            assert config["minimax_api_key"] == "mykey123"
            assert config["minimax_model"] == "MiniMax-Text-01"

    def test_load_ollama_env(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            with open(env_path, "w") as f:
                f.write("AI_PROVIDER=ollama\n")
                f.write("OLLAMA_MODEL=llama3.2-vision\n")

            config = load_workspace(td)

            assert config["ai_provider"] == "ollama"
            assert config["ollama_model"] == "llama3.2-vision"

    def test_load_openai_env(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = os.path.join(td, ".env")
            with open(env_path, "w") as f:
                f.write("AI_PROVIDER=openai\n")
                f.write("OPENAI_API_KEY=sk-abc\n")
                f.write("OPENAI_MODEL=gpt-4o\n")

            config = load_workspace(td)

            assert config["ai_provider"] == "openai"
            assert config["openai_api_key"] == "sk-abc"

    def test_load_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            agents_path = os.path.join(td, "AGENTS.md")
            with open(agents_path, "w") as f:
                f.write("Be extra careful with delete actions.\n")

            config = load_workspace(td)

            assert "Be extra careful" in config["agents_md"]

    def test_defaults_when_no_env(self):
        with tempfile.TemporaryDirectory() as td:
            config = load_workspace(td)

            assert config["ai_provider"] == "minimax"
            assert config["minimax_api_url"] == "https://api.minimax.io"
            assert config["ollama_model"] == "llama3.2-vision"


class TestValidateConfig:
    def test_minimax_requires_api_key(self):
        config = {"ai_provider": "minimax", "minimax_api_key": ""}
        with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
            validate_config(config)

    def test_minimax_passes_with_key(self):
        config = {"ai_provider": "minimax", "minimax_api_key": "key123"}
        # Should not raise
        validate_config(config)

    def test_ollama_no_key_required(self):
        config = {"ai_provider": "ollama", "ollama_base_url": "http://localhost:11434"}
        validate_config(config)  # Should not raise

    def test_openai_requires_api_key(self):
        config = {"ai_provider": "openai", "openai_api_key": ""}
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            validate_config(config)

    def test_unknown_provider(self):
        config = {"ai_provider": "bedrock"}
        with pytest.raises(ValueError, match="Unknown AI_PROVIDER"):
            validate_config(config)
