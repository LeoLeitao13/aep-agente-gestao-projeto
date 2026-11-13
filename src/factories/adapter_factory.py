"""Factory Method para Adapters de entrada e para o LLM."""
from __future__ import annotations

from pathlib import Path

from ..adapters import (
    BaseInputAdapter,
    CsvJiraAdapter,
    DocxJiraAdapter,
    LLMAdapter,
    NullLLMAdapter,
)
from ..adapters.llm_adapter import BaseLLMAdapter
from ..config.settings import settings


class AdapterFactory:
    """Centraliza a criação de adaptadores conforme o contexto."""

    @staticmethod
    def for_source(source: Path | str) -> BaseInputAdapter:
        """Seleciona o Adapter conforme a extensão da fonte."""
        ext = Path(source).suffix.lower()
        if ext == ".docx":
            return DocxJiraAdapter()
        if ext == ".csv":
            return CsvJiraAdapter()
        raise ValueError(f"Nenhum adapter registrado para a extensão '{ext}'")

    @staticmethod
    def llm(force_null: bool = False) -> BaseLLMAdapter:
        """Devolve o LLM adequado — Null quando não houver chave ou em testes."""
        if force_null or not settings.llm_enabled:
            return NullLLMAdapter()
        return LLMAdapter()
