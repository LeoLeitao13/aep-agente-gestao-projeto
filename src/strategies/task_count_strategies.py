"""Strategies de contagem por categoria de tarefa."""
from __future__ import annotations

from ..models import Task
from .base_strategy import IndicatorResult, IndicatorStrategy


class PlannedTasksStrategy(IndicatorStrategy):
    """Total planejado = tudo que foi inserido no plano, inclusive canceladas.

    Regra adotada: total de tarefas no backlog do sprint (|tasks|)."""
    name = "tarefas_planejadas"
    unit = "qtd"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        return IndicatorResult(self.name, len(tasks), self.unit)


class CompletedTasksStrategy(IndicatorStrategy):
    name = "tarefas_concluidas"
    unit = "qtd"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        return IndicatorResult(
            self.name,
            sum(1 for t in tasks if t.is_concluida),
            self.unit,
        )


class CancelledTasksStrategy(IndicatorStrategy):
    name = "tarefas_canceladas"
    unit = "qtd"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        return IndicatorResult(
            self.name,
            sum(1 for t in tasks if t.is_cancelada),
            self.unit,
        )


class AdjustmentTasksStrategy(IndicatorStrategy):
    """Tarefas de ajuste/retrabalho — inferidas via labels/summary."""
    name = "tarefas_ajuste"
    unit = "qtd"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        return IndicatorResult(
            self.name,
            sum(1 for t in tasks if t.is_ajuste),
            self.unit,
        )
