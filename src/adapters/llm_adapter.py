"""Adapter de LLM (Adapter GoF) — isola a dependência do provedor.

Expondo uma interface única `complete(prompt) -> str` conseguimos:
  * trocar OpenAI por outro provedor sem mexer no pipeline;
  * usar `NullLLMAdapter` em testes/ambientes sem chave.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from ..config.settings import settings


class BaseLLMAdapter(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, system: str = "") -> str: ...

    def extract_json(self, prompt: str, *, system: str = "") -> Any:
        """Helper: pede resposta JSON e faz parse defensivo."""
        raw = self.complete(prompt, system=system)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise


class NullLLMAdapter(BaseLLMAdapter):
    """Adapter inerte usado quando a chave do LLM não está configurada.

    Mantém o contrato sem fazer chamada externa — útil para rodar o
    pipeline 100% determinístico em Python."""

    def complete(self, prompt: str, *, system: str = "") -> str:  # noqa: ARG002
        return "{}"


class LLMAdapter(BaseLLMAdapter):
    """Adapter concreto OpenAI. Chamada lazy para não exigir openai em testes."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def complete(self, prompt: str, *, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
        )
        return response.choices[0].message.content or ""
