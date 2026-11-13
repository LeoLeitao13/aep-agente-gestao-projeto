"""Filter que aplica o portfólio de Strategies e gera os indicadores."""
from __future__ import annotations

from ..strategies import IndicatorStrategy
from .filter_base import BaseFilter, PipelineContext


class IndicatorFilter(BaseFilter):
    def __init__(self, strategies: list[IndicatorStrategy]) -> None:
        self.strategies = strategies

    def process(self, context: PipelineContext) -> PipelineContext:
        context.indicators = [s.calculate(context.tasks) for s in self.strategies]
        return context
