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

        # Sem tarefas concluídas no período: taxa matematicamente indefinida (0/0).
        # Devolvemos None e o CSV grava "N/A" — nunca 0%, que seria enganoso.
        if concluidas == 0:
            return IndicatorResult(
                self.name,
                None,
                self.unit,
                detail={
                    "ajustes": ajustes,
                    "concluidas": 0,
                    "nota": "indicador não aplicável: nenhuma tarefa concluída no período",
                },
            )

        rate = ajustes / concluidas * 100
        return IndicatorResult(
            self.name,
            round(rate, 2),
            self.unit,
            detail={"ajustes": ajustes, "concluidas": concluidas},
        )
