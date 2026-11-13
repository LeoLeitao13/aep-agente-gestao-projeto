"""Factory Method para o conjunto de Strategies de indicadores."""
from __future__ import annotations

from ..strategies import (
    AdjustmentTasksStrategy,
    CancelledTasksStrategy,
    CompletedTasksStrategy,
    EstimatedHoursStrategy,
    HoursPerAssigneeStrategy,
    IndicatorStrategy,
    PlannedTasksStrategy,
    RealizedHoursStrategy,
    ReworkRateStrategy,
)


class StrategyFactory:
    """Cria o portfólio padrão de indicadores exigido pela AEP."""

    @staticmethod
    def default_set() -> list[IndicatorStrategy]:
        return [
            PlannedTasksStrategy(),
            CompletedTasksStrategy(),
            CancelledTasksStrategy(),
            AdjustmentTasksStrategy(),
            ReworkRateStrategy(),
            EstimatedHoursStrategy(),
            RealizedHoursStrategy(),
            HoursPerAssigneeStrategy(),
        ]

    @staticmethod
    def by_name(name: str) -> IndicatorStrategy:
        registry = {s.name: s for s in StrategyFactory.default_set()}
        if name not in registry:
            raise KeyError(f"Indicador desconhecido: {name}")
        return registry[name]
