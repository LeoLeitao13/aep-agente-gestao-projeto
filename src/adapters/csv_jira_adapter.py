"""Adapter para exports CSV do Jira (UI em PT-BR).

Exemplo de colunas relevantes:
    Resumo, Chave da item, Tipo de item, Status, Responsável,
    Estimativa original, Tempo gasto, Sprint

Observação importante: o Jira exporta `Estimativa original` e `Tempo gasto`
em SEGUNDOS. Convertemos para horas decimais.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .base_adapter import BaseInputAdapter

# Cabeçalhos aceitos (lower) → chave canônica
_COLUMN_MAP = {
    "resumo": "summary",
    "summary": "summary",
    "chave da item": "key",
    "chave": "key",
    "key": "key",
    "tipo de item": "issue_type",
    "issue type": "issue_type",
    "tipo": "issue_type",
    "status": "status",
    "responsável": "assignee",
    "responsavel": "assignee",
    "assignee": "assignee",
    "estimativa original": "estimated_hours",
    "original estimate": "estimated_hours",
    "tempo gasto": "realized_hours",
    "time spent": "realized_hours",
    "rótulos": "labels",
    "rotulos": "labels",
    "labels": "labels",
    "sprint": "sprint",
}


def _seconds_to_hours(raw: str) -> float:
    """Converte segundos (string) em horas decimais; vazio/None → 0."""
    if not raw:
        return 0.0
    raw = raw.strip().replace(",", ".")
    if not raw:
        return 0.0
    try:
        return round(float(raw) / 3600.0, 2)
    except ValueError:
        return 0.0


class CsvJiraAdapter(BaseInputAdapter):
    """Adapter concreto: CSV do Jira Cloud (UI em PT-BR ou EN-US)."""

    def adapt(self, source: Path | str) -> list[dict]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            headers = next(reader)
            # Jira repete colunas com o mesmo nome (ex.: "Sprint", "Seguidores");
            # agrupamos TODOS os índices por chave canônica para concatenar valores.
            canonical_indices: dict[str, list[int]] = {}
            for idx, raw_header in enumerate(headers):
                canonical = _COLUMN_MAP.get(raw_header.strip().lower())
                if canonical:
                    canonical_indices.setdefault(canonical, []).append(idx)

            records: list[dict] = []
            for row in reader:
                if not any(c.strip() for c in row):
                    continue
                record = self._row_to_record(row, canonical_indices)
                if record["key"] or record["summary"]:
                    records.append(record)
            return records

    # ---------------------------------------------------------------- helpers
    def _row_to_record(self, row: list[str], indices: dict[str, list[int]]) -> dict:
        def _collect(field: str) -> list[str]:
            return [row[i].strip() for i in indices.get(field, []) if i < len(row) and row[i].strip()]

        labels = []
        for raw in _collect("labels"):
            labels.extend([l.strip() for l in raw.replace(";", ",").split(",") if l.strip()])

        return {
            "key": (_collect("key") or [""])[0],
            "summary": (_collect("summary") or [""])[0],
            "status": (_collect("status") or [""])[0],
            "assignee": (_collect("assignee") or [""])[0],
            "estimated_hours": _seconds_to_hours((_collect("estimated_hours") or [""])[0]),
            "realized_hours": _seconds_to_hours((_collect("realized_hours") or [""])[0]),
            "labels": labels,
            "issue_type": (_collect("issue_type") or [""])[0],
            "sprint": ", ".join(_collect("sprint")),
        }
