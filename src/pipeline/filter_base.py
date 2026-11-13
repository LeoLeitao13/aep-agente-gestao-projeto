"""Base do estilo arquitetural Pipe-and-Filter.

Um `PipelineContext` carrega o estado trafegado entre filtros.
Cada `BaseFilter` consome e devolve o mesmo contexto — mantendo baixo
acoplamento e permitindo reordenar/substituir filtros livremente.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..models import Task
from ..strategies import IndicatorResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Estado trafegado através dos filtros."""
    raw_records: list[dict] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    indicators: list[IndicatorResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseFilter(ABC):
    """Interface comum para todos os filtros do pipeline."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def __call__(self, context: PipelineContext) -> PipelineContext:
        logger.info("→ Filtro %s iniciando (records=%d, tasks=%d)",
                    self.name, len(context.raw_records), len(context.tasks))
        result = self.process(context)
        logger.info("← Filtro %s concluído", self.name)
        return result

    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext: ...
