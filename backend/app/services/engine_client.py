from typing import Any

import httpx


class EngineUnavailable(Exception):
    pass


class EngineTimeout(Exception):
    pass


class EngineFailure(Exception):
    pass


class EngineClient:
    """HTTP adapter to the separate AlgoViz AI explanation service."""

    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"
        self.timeout = timeout

    async def analyze(self, metadata: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/analyze", json={"metadata": metadata})
        except httpx.TimeoutException as exc:
            raise EngineTimeout from exc
        except httpx.RequestError as exc:
            raise EngineUnavailable from exc

        if response.is_error:
            raise EngineFailure(f"AI engine returned HTTP {response.status_code}")
        try:
            result = response.json()
        except ValueError as exc:
            raise EngineFailure("AI engine returned invalid JSON") from exc
        if not isinstance(result, dict) or not isinstance(result.get("explanation"), str):
            raise EngineFailure("AI engine returned an invalid response")
        return result
