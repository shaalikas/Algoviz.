import json
import os
from typing import Any

import requests

from .fallback import generate_fallback
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class AIAnalyzer:
    """Create compact repository explanations with a Groq API + local fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY")
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    @staticmethod
    def compact_metadata(metadata: dict, max_items: int = 40) -> dict:
        """Keep only useful, bounded metadata fields for the AI request."""
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")

        allowed = {
            "repository", "name", "language", "files", "dependencies",
            "architecture", "detected_risks", "risks",
            "circular_dependencies",
        }
        compact = {}

        for key in allowed:
            if key not in metadata:
                continue
            value = metadata[key]

            if key == "files" and isinstance(value, list):
                compact[key] = [
                    AIAnalyzer._compact_file(item) for item in value[:max_items]
                ]
            elif key in {"dependencies", "detected_risks", "risks", "circular_dependencies"} and isinstance(value, list):
                compact[key] = value[:max_items]
            elif key == "architecture":
                compact[key] = AIAnalyzer._compact_architecture(value, max_items)
            elif key == "repository" and isinstance(value, dict):
                compact[key] = {
                    k: value[k] for k in ("name", "language", "description", "entry_points")
                    if k in value
                }
            else:
                compact[key] = value

        return compact

    @staticmethod
    def _compact_file(item: Any) -> Any:
        if isinstance(item, str):
            return item
        if not isinstance(item, dict):
            return item
        keys = (
            "path", "language", "imports", "dependencies",
            "classes", "functions", "role", "entry_point"
        )
        result = {}
        for key in keys:
            if key in item:
                value = item[key]
                if isinstance(value, list):
                    result[key] = value[:25]
                else:
                    result[key] = value
        return result

    @staticmethod
    def _compact_architecture(value: Any, max_items: int) -> Any:
        if isinstance(value, dict):
            result = {}
            for key in ("layers", "components", "entry_points", "data_flow", "notes"):
                if key in value:
                    v = value[key]
                    result[key] = v[:max_items] if isinstance(v, list) else v
            return result
        if isinstance(value, list):
            return value[:max_items]
        return value

    def analyze(self, metadata: dict) -> dict:
        compact = self.compact_metadata(metadata)

        if not self.api_key:
            return {
                "source": "local fallback",
                "model": None,
                "explanation": generate_fallback(compact),
                "metadata": compact,
            }

        try:
            explanation = self._call_api(compact)
            return {
                "source": "AI API",
                "model": self.model,
                "explanation": explanation,
                "metadata": compact,
            }
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            return {
                "source": "local fallback",
                "model": None,
                "error": str(exc),
                "explanation": generate_fallback(compact),
                "metadata": compact,
            }

    def _call_api(self, compact: dict) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        metadata=json.dumps(compact, separators=(",", ":"), ensure_ascii=False)
                    ),
                },
            ],
            "temperature": 0.1,
        }

        response = requests.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError("API returned invalid JSON") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("API response did not contain choices[0].message.content") from exc

        if not isinstance(content, str) or not content.strip():
            raise ValueError("API returned an empty explanation")

        return content.strip()
