"""Filter de saída — grava o CSV padronizado da Entrega 2.

Formato:
    indicador,valor,unidade,detalhe
    tarefas_planejadas,42,qtd,
    ...
    horas_por_integrante,,,"{ 'Ana': {'estimadas':120,'realizadas':118}, ... }"
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .filter_base import BaseFilter, PipelineContext


class CsvWriterFilter(BaseFilter):
    HEADERS = ["indicador", "valor", "unidade", "detalhe"]

    def __init__(self, output_path: Path | str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def process(self, context: PipelineContext) -> PipelineContext:
        with self.output_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(self.HEADERS)
            for ind in context.indicators:
                value = "" if isinstance(ind.value, dict) else ind.value
                detail_source = ind.detail if ind.detail is not None else (
                    ind.value if isinstance(ind.value, dict) else None
                )
                detail = json.dumps(detail_source, ensure_ascii=False) if detail_source else ""
                writer.writerow([ind.name, value, ind.unit, detail])
        context.metadata["output_file"] = str(self.output_path)
        return context
