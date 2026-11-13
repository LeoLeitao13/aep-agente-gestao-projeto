"""Strategy base (GoF) para cálculo de indicadores.

Cada regra de negócio é encapsulada em uma Strategy concreta — assim a
adição de um novo indicador não afeta o pipeline nem as demais regras.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..models import Task


@dataclass
class IndicatorResult:
    """Resultado de um cálculo. `value` pode ser escalar ou dict (p/ indicadores agregados)."""
    name: str
    value: Any
    unit: str = ""
    detail: dict | None = None


class IndicatorStrategy(ABC):
    name: str = "indicator"
    unit: str = ""

    @abstractmethod
    def calculate(self, tasks: list[Task]) -> IndicatorResult: ...
