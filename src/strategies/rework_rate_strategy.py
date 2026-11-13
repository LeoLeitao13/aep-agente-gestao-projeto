"""Strategy para taxa de retrabalho = tarefas de ajuste / concluídas."""
from __future__ import annotations

from ..models import Task
from .base_strategy import IndicatorResult, IndicatorStrategy


class ReworkRateStrategy(IndicatorStrategy):
    name = "taxa_retrabalho"
    unit = "%"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        concluidas = sum(1 for t in tasks if t.is_concluida)
        ajustes = sum(1 for t in tasks if t.is_ajuste)

        rate = (ajustes / concluidas * 100) if concluidas else 0.0
        return IndicatorResult(
            self.name,
            round(rate, 2),
            self.unit,
            detail={"ajustes": ajustes, "concluidas": concluidas},
        )
