"""Strategies para indicadores de horas."""
from __future__ import annotations

from collections import defaultdict

from ..config.settings import settings
from ..models import Task
from .base_strategy import IndicatorResult, IndicatorStrategy


class EstimatedHoursStrategy(IndicatorStrategy):
    """Horas estimadas totais (regra: ~1.000h no projeto).

    Reporta valor somado + comparação com a meta configurada."""
    name = "horas_estimadas"
    unit = "h"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        total = sum(t.estimated_hours for t in tasks)
        meta = settings.horas_estimadas_totais
        return IndicatorResult(
            self.name,
            round(total, 2),
            self.unit,
            detail={
                "meta_horas": meta,
                "desvio_horas": round(total - meta, 2),
                "aderente": abs(total - meta) <= meta * 0.05,  # tolerância 5%
            },
        )


class RealizedHoursStrategy(IndicatorStrategy):
    """Horas realizadas = soma de time-spent das tarefas."""
    name = "horas_realizadas"
    unit = "h"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        return IndicatorResult(
            self.name,
            round(sum(t.realized_hours for t in tasks), 2),
            self.unit,
        )


class HoursPerAssigneeStrategy(IndicatorStrategy):
    """Horas por integrante — agrega estimado e realizado por assignee."""
    name = "horas_por_integrante"
    unit = "h"

    def calculate(self, tasks: list[Task]) -> IndicatorResult:
        agg: dict[str, dict[str, float]] = defaultdict(lambda: {"estimadas": 0.0, "realizadas": 0.0})
        for t in tasks:
            assignee = t.assignee.strip() or "Não atribuído"
            agg[assignee]["estimadas"] += t.estimated_hours
            agg[assignee]["realizadas"] += t.realized_hours

        rounded = {
            name: {k: round(v, 2) for k, v in values.items()}
            for name, values in sorted(agg.items())
        }
        return IndicatorResult(self.name, rounded, self.unit)
