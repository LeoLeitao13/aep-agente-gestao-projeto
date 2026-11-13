"""Controller (GRASP) — orquestra o pipeline Pipe-and-Filter.

Responsabilidades:
  * receber a requisição do caller (CLI, UI, testes);
  * montar a cadeia de filtros via Factory;
  * executar em sequência, mantendo métricas;
  * expor o resultado final (contexto + relatório).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..factories import FilterFactory
from ..pipeline import PipelineContext


@dataclass
class PipelineReport:
    duration_seconds: float
    filters_timing: dict[str, float] = field(default_factory=dict)
    context: PipelineContext | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "duracao_total_seg": round(self.duration_seconds, 4),
            "tempos_por_filtro": {k: round(v, 4) for k, v in self.filters_timing.items()},
            "metadata": self.context.metadata if self.context else {},
            "indicadores": [
                {"name": i.name, "value": i.value, "unit": i.unit, "detail": i.detail}
                for i in (self.context.indicators if self.context else [])
            ],
        }


class PipelineController:
    """Fachada única usada por CLI e testes."""

    def __init__(self, *, use_llm: bool = False) -> None:
        self.use_llm = use_llm

    def run(self, source: Path | str, output_path: Path | str) -> PipelineReport:
        filters = FilterFactory.build_pipeline(source, output_path, use_llm=self.use_llm)
        context = PipelineContext()

        timings: dict[str, float] = {}
        start = time.perf_counter()
        for flt in filters:
            t0 = time.perf_counter()
            context = flt(context)
            timings[flt.name] = time.perf_counter() - t0
        total = time.perf_counter() - start

        return PipelineReport(duration_seconds=total, filters_timing=timings, context=context)
