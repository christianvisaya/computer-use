"""Tests for ai.py."""

import pytest
from unittest.mock import patch, MagicMock

from computer_use.ai import chat, _make_base64_image


class TestMakeBase64Image:
    def test_returns_data_uri(self):
        result = _make_base64_image(b"\xff\xd8\xff\xe0")
        assert result.startswith("data:image/jpeg;base64,")
        assert len(result) > 30


class TestChat:
    def test_minimax_chat_builds_correct_payload(self):
        fake_bytes = b"\xff\xd8\xff\xe0"
        fake_response = {
            "choices": [
                {"message": {"content": '{"action": "done", "reason": "ok"}'}}
            ]
        }
        with patch("computer_use.ai.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=fake_response),
            )
            result = chat(
                provider="minimax",
                instruction="open terminal",
                image_bytes=fake_bytes,
                system_prompt="You are an agent.",
                minimax_api_key="testkey",
                minimax_api_url="https://api.minimax.io",
                minimax_model="MiniMax-Text-01",
            )
            assert "done" in result
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer testkey"

    def test_ollama_chat_builds_correct_payload(self):
        fake_bytes = b"\xff\xd8\xff\xe0"
        fake_response = {
            "choices": [
                {"message": {"content": '{"action": "wait", "seconds": 1}'}}
            ]
        }
        with patch("computer_use.ai.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=fake_response),
            )
            result = chat(
                provider="ollama",
                instruction="wait",
                image_bytes=fake_bytes,
                system_prompt="You are an agent.",
                ollama_base_url="http://localhost:11434",
                ollama_model="llama3.2-vision",
            )
            assert "wait" in result

    def test_openai_chat_builds_correct_payload(self):
        fake_bytes = b"\xff\xd8\xff\xe0"
        fake_response = {
            "choices": [
                {"message": {"content": '{"action": "launch", "app": "Safari"}'}}
            ]
        }
        with patch("computer_use.ai.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=fake_response),
            )
            result = chat(
                provider="openai",
                instruction="open safari",
                image_bytes=fake_bytes,
                system_prompt="You are an agent.",
                openai_api_key="sk-test",
                openai_base_url="https://api.openai.com/v1",
                openai_model="gpt-4o",
            )
            assert "launch" in result

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown AI provider"):
            chat(provider="bedrock", instruction="hi", image_bytes=b"fake", system_prompt="")
