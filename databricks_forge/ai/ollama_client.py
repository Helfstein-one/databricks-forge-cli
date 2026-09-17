"""Ollama Client for Local LLM Orchestration."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Generator, List, Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class OllamaClient:
    """Client for local Ollama REST API."""

    def __init__(self, host: Optional[str] = None):
        self.host = (host or DEFAULT_OLLAMA_HOST).rstrip("/")

    def is_available(self) -> bool:
        """Checks if the local Ollama server is running and reachable."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Lists all locally installed model tags."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return models
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
        return []

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        stream: bool = False
    ) -> Generator[str, None, None] | str:
        """Sends chat messages to Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": stream,
        }

        if stream:
            return self._chat_stream(payload)
        else:
            resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    def _chat_stream(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Yields streaming chunks from Ollama /api/chat."""
        resp = requests.post(f"{self.host}/api/chat", json=payload, stream=True, timeout=120)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done", False):
                    break
