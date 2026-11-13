"""Adapter para exports do Jira em formato .docx.

Suporta dois layouts comuns:
    (A) Tabelas com cabeçalho (Key/Summary/Status/Assignee/Estimate/Logged/Labels).
    (B) Blocos de parágrafos "Chave: Valor" por issue (fallback).

A camada LLM é opcional e usada só para registros ambíguos.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.table import Table

from .base_adapter import BaseInputAdapter

_HOURS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(h|hora|horas|hr|hrs)?", re.IGNORECASE)

# Sinônimos de cabeçalhos aceitos (lower-cased)
_HEADER_SYNONYMS = {
    "key": {"key", "chave", "issue key", "id"},
    "summary": {"summary", "resumo", "título", "titulo"},
    "status": {"status", "situação", "situacao"},
    "assignee": {"assignee", "responsável", "responsavel", "atribuído", "atribuido"},
    "estimated_hours": {"estimate", "estimativa", "original estimate", "estimativa original", "tempo estimado"},
    "realized_hours": {"logged", "time spent", "tempo gasto", "tempo registrado", "horas realizadas"},
    "labels": {"labels", "rótulos", "rotulos", "etiquetas"},
    "issue_type": {"type", "tipo", "issue type", "tipo de item"},
}


def _parse_hours(raw: str) -> float:
    """Converte '3h 30m', '2.5h', '4 horas' -> horas decimais."""
    if not raw:
        return 0.0
    txt = str(raw).strip().lower()
    if not txt or txt in {"-", "0", "none", "n/a"}:
        return 0.0

    total = 0.0
    weeks = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:w|sem)", txt)
    days = re.search(r"(\d+(?:[.,]\d+)?)\s*d", txt)
    hours = re.search(r"(\d+(?:[.,]\d+)?)\s*h", txt)
    minutes = re.search(r"(\d+(?:[.,]\d+)?)\s*m(?!s)", txt)

    if any((weeks, days, hours, minutes)):
        if weeks:
            total += float(weeks.group(1).replace(",", ".")) * 40
        if days:
            total += float(days.group(1).replace(",", ".")) * 8
        if hours:
            total += float(hours.group(1).replace(",", "."))
        if minutes:
            total += float(minutes.group(1).replace(",", ".")) / 60
        return round(total, 2)

    # Valor numérico puro
    m = _HOURS_RE.match(txt)
    return float(m.group(1).replace(",", ".")) if m else 0.0


def _map_header(cell: str) -> str | None:
    """Mapeia texto de cabeçalho para a chave canônica."""
    key = cell.strip().lower()
    for canonical, synonyms in _HEADER_SYNONYMS.items():
        if key in synonyms:
            return canonical
    return None


class DocxJiraAdapter(BaseInputAdapter):
    """Adapter concreto: lê .docx de export do Jira."""

    def adapt(self, source: Path | str) -> list[dict]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        doc = Document(str(path))
        records: list[dict] = []

        for table in doc.tables:
            records.extend(self._extract_from_table(table))

        if not records:
            records = list(self._extract_from_paragraphs(doc.paragraphs))

        return records

    # --------------------------------------------------------------- tabela
    def _extract_from_table(self, table: Table) -> list[dict]:
        rows = table.rows
        if len(rows) < 2:
            return []

        header_cells = [c.text for c in rows[0].cells]
        header_map: dict[int, str] = {}
        for idx, cell in enumerate(header_cells):
            mapped = _map_header(cell)
            if mapped:
                header_map[idx] = mapped

        if "key" not in header_map.values() and "summary" not in header_map.values():
            return []

        extracted = []
        for row in rows[1:]:
            record = self._empty_record()
            for idx, cell in enumerate(row.cells):
                field = header_map.get(idx)
                if not field:
                    continue
                value = cell.text.strip()
                if field in ("estimated_hours", "realized_hours"):
                    record[field] = _parse_hours(value)
                elif field == "labels":
                    record[field] = [l.strip() for l in re.split(r"[,;]", value) if l.strip()]
                else:
                    record[field] = value
            if record["key"] or record["summary"]:
                extracted.append(record)
        return extracted

    # ----------------------------------------------------------- parágrafos
    def _extract_from_paragraphs(self, paragraphs) -> Iterable[dict]:
        """Fallback: parágrafos do tipo 'Chave: Valor'. Issues separados
        por chaves tipo 'PROJ-123' ou linha em branco."""
        current = self._empty_record()
        issue_header = re.compile(r"^([A-Z][A-Z0-9]+-\d+)\b")

        for para in paragraphs:
            text = para.text.strip()
            if not text:
                if current["key"] or current["summary"]:
                    yield current
                    current = self._empty_record()
                continue

            m = issue_header.match(text)
            if m:
                if current["key"] or current["summary"]:
                    yield current
                current = self._empty_record()
                current["key"] = m.group(1)
                remainder = text[m.end():].strip(" -:")
                if remainder:
                    current["summary"] = remainder
                continue

            if ":" in text:
                k, v = text.split(":", 1)
                field = _map_header(k)
                if field in ("estimated_hours", "realized_hours"):
                    current[field] = _parse_hours(v)
                elif field == "labels":
                    current[field] = [l.strip() for l in re.split(r"[,;]", v) if l.strip()]
                elif field:
                    current[field] = v.strip()

        if current["key"] or current["summary"]:
            yield current

    @staticmethod
    def _empty_record() -> dict:
        return {
            "key": "",
            "summary": "",
            "status": "",
            "assignee": "",
            "estimated_hours": 0.0,
            "realized_hours": 0.0,
            "labels": [],
            "issue_type": "",
        }
