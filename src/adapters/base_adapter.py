"""Contrato base do Adapter (GoF).

Converte uma fonte externa (docx, csv, xlsx, API...) em lista de dicts
no formato canônico esperado pelo pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseInputAdapter(ABC):
    """Interface comum para todos os adaptadores de entrada."""

    @abstractmethod
    def adapt(self, source: Path | str) -> list[dict]:
        """Lê a fonte e devolve lista de registros brutos normalizados.

        Cada dict deve ter minimamente:
            key, summary, status, assignee, estimated_hours,
            realized_hours, labels (list), issue_type
        """
        raise NotImplementedError
