from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class LLMResponse:
    provider: str
    model: str
    content: str
    confidence: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMGateway:
    """Provider seam for production LLM calls with a deterministic local fallback."""

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = provider or os.getenv(
            "AEGISAI_LLM_PROVIDER",
            os.getenv("TRUSTED_AGENTOPS_LLM_PROVIDER", "local"),
        )
        self.model = model or os.getenv(
            "AEGISAI_LLM_MODEL",
            os.getenv("TRUSTED_AGENTOPS_LLM_MODEL", "deterministic-policy-model"),
        )
        if self.provider == "openai" and self.model == "deterministic-policy-model":
            self.model = "gpt-4.1-mini"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_base_url = os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta",
        )
        self.timeout_seconds = float(os.getenv("AEGISAI_LLM_TIMEOUT_SECONDS", "20"))

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if self.provider == "local":
            content = self._local_response(system_prompt, user_prompt)
            return LLMResponse(
                provider=self.provider,
                model=self.model,
                content=content,
                confidence=0.84,
            )
        if self.provider == "openai":
            return self._openai_response(system_prompt, user_prompt)
        if self.provider == "gemini":
            return self._gemini_response(system_prompt, user_prompt)
        return LLMResponse(
            provider=self.provider,
            model=self.model,
            content=(
                "External provider call is intentionally abstracted in this portfolio. "
                "Wire this gateway to OpenAI, Azure OpenAI, Bedrock, or Vertex AI in production."
            ),
            confidence=0.75,
        )

    def _openai_response(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if not self.openai_api_key:
            return LLMResponse(
                provider="openai",
                model=self.model,
                content=(
                    "OpenAI provider selected, but OPENAI_API_KEY is not configured. "
                    "Set OPENAI_API_KEY or switch AEGISAI_LLM_PROVIDER=local for offline demos."
                ),
                confidence=0.0,
            )

        payload = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": 350,
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.openai_base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return LLMResponse(
                provider="openai",
                model=self.model,
                content=f"OpenAI LLM call failed: {exc}",
                confidence=0.0,
            )

        data = response.json()
        usage = data.get("usage") or {}
        return LLMResponse(
            provider="openai",
            model=self.model,
            content=self._extract_openai_text(data),
            confidence=0.9,
            prompt_tokens=int(usage.get("input_tokens") or 0),
            completion_tokens=int(usage.get("output_tokens") or 0),
        )

    @staticmethod
    def _extract_openai_text(data: dict[str, Any]) -> str:
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text:
            return output_text

        output = data.get("output", [])
        if not isinstance(output, list):
            return "OpenAI response returned without text output."

        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
        return "\n".join(chunks) if chunks else "OpenAI response returned without text output."

    def _gemini_response(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if not self.gemini_api_key:
            return LLMResponse(
                provider="gemini",
                model=self.model,
                content="Gemini selected but GEMINI_API_KEY is not configured.",
                confidence=0.0,
            )
        model = self.model if self.model != "deterministic-policy-model" else "gemini-2.0-flash"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
            "generationConfig": {"maxOutputTokens": 1024},
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.gemini_base_url}/models/{model}:generateContent",
                    params={"key": self.gemini_api_key},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                usage = data.get("usageMetadata") or {}
                return LLMResponse(
                    provider="gemini",
                    model=model,
                    content=text or "{}",
                    confidence=0.88,
                    prompt_tokens=int(usage.get("promptTokenCount") or 0),
                    completion_tokens=int(usage.get("candidatesTokenCount") or 0),
                )
        except (httpx.HTTPError, IndexError, KeyError) as exc:
            return LLMResponse(
                provider="gemini",
                model=model,
                content=f"Gemini call failed: {exc}",
                confidence=0.0,
            )

    @staticmethod
    def _local_response(system_prompt: str, user_prompt: str) -> str:
        combined = f"{system_prompt} {user_prompt}".lower()
        if "refund" in combined:
            return "Refund workflow selected. Gather payment evidence, evaluate policy thresholds, and route approval by amount."
        if "delete" in combined or "restricted" in combined:
            return "Restricted data workflow selected. Require identity validation, entitlement validation, and compliance control-plane review."
        if "dispute" in combined:
            return "Dispute workflow selected. Gather transaction evidence and prepare payment-processor response."
        return "Customer communication workflow selected. Ground response in evidence and avoid unapproved commitments."
