"""AI provider clients: MiniMax, Ollama, OpenAI-compatible, Anthropic."""

import base64
import json
import os
import requests


def _make_base64_image(jpeg_bytes: bytes) -> str:
    """Return data URI for JPEG bytes."""
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


# ---------------------------------------------------------------------------
# MiniMax
# ---------------------------------------------------------------------------

def chat_minimax(
    api_key: str,
    api_url: str,
    model: str,
    system_prompt: str,
    instruction: str,
    image_bytes: bytes,
) -> str:
    """Send screenshot + instruction to MiniMax chat completion API.

    Returns the text content of the assistant's response.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "name": "Computer Agent", "content": system_prompt},
            {
                "role": "user",
                "name": "User",
                "content": [
                    {"type": "text", "text": f"INSTRUCTION: {instruction}"},
                    {"type": "image_url", "image_url": {"url": _make_base64_image(image_bytes)}},
                ],
            },
        ],
        "temperature": 0.1,
        "max_completion_tokens": 2048,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(f"{api_url}/v1/text/chatcompletion_v2", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    choices = data.get("choices")
    if not choices or choices[0] is None:
        status_msg = data.get("base_resp", {}).get("status_msg", "unknown error")
        raise ValueError(f"MiniMax API error: {status_msg} (code {data.get('base_resp', {}).get('status_code')})")

    choice = choices[0]
    message = choice.get("message", {})
    content = message.get("content", "")

    # Reasoning models (M2 series) may put the actual response in reasoning_content
    # when content is empty due to token budget
    if not content and message.get("reasoning_content"):
        content = message["reasoning_content"]

    return content


# ---------------------------------------------------------------------------
# Ollama (local, OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------

def chat_ollama(
    base_url: str,
    model: str,
    system_prompt: str,
    instruction: str,
    image_bytes: bytes,
) -> str:
    """Send screenshot + instruction to Ollama's OpenAI-compatible API.

    Ollama accepts base64 images directly in the content array.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"INSTRUCTION: {instruction}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                ],
            },
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

def chat_anthropic(
    api_key: str,
    model: str,
    system_prompt: str,
    instruction: str,
    image_bytes: bytes,
) -> str:
    """Send screenshot + instruction to Anthropic Claude API."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": f"INSTRUCTION: {instruction}"},
                ],
            }
        ],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


# ---------------------------------------------------------------------------
# OpenAI-compatible (any OpenAI-compatible server)
# ---------------------------------------------------------------------------

def chat_openai(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    instruction: str,
    image_bytes: bytes,
) -> str:
    """Send screenshot + instruction to any OpenAI-compatible endpoint."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"INSTRUCTION: {instruction}"},
                    {"type": "image_url", "image_url": {"url": _make_base64_image(image_bytes)}},
                ],
            },
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def chat(
    provider: str,
    instruction: str,
    image_bytes: bytes,
    system_prompt: str,
    *,
    # MiniMax
    minimax_api_key: str = "",
    minimax_api_url: str = "https://api.minimax.io",
    minimax_model: str = "MiniMax-Text-01",
    # Ollama
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "llama3.2-vision",
    # OpenAI
    openai_api_key: str = "",
    openai_base_url: str = "https://api.openai.com/v1",
    openai_model: str = "gpt-4o",
    # Anthropic
    anthropic_api_key: str = "",
    anthropic_model: str = "claude-sonnet-4-20250514",
) -> str:
    """Unified chat function that dispatches to the right provider."""

    if provider == "minimax":
        return chat_minimax(
            api_key=minimax_api_key,
            api_url=minimax_api_url,
            model=minimax_model,
            system_prompt=system_prompt,
            instruction=instruction,
            image_bytes=image_bytes,
        )
    elif provider == "ollama":
        return chat_ollama(
            base_url=ollama_base_url,
            model=ollama_model,
            system_prompt=system_prompt,
            instruction=instruction,
            image_bytes=image_bytes,
        )
    elif provider == "openai":
        return chat_openai(
            api_key=openai_api_key,
            base_url=openai_base_url,
            model=openai_model,
            system_prompt=system_prompt,
            instruction=instruction,
            image_bytes=image_bytes,
        )
    elif provider == "anthropic":
        return chat_anthropic(
            api_key=anthropic_api_key,
            model=anthropic_model,
            system_prompt=system_prompt,
            instruction=instruction,
            image_bytes=image_bytes,
        )
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
