"""Fixtures compartilhadas: geram .docx sintéticos espelhando exports do Jira."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from docx import Document


@dataclass
class JiraRow:
    key: str
    summary: str
    status: str
    assignee: str
    estimated: str
    logged: str
    labels: str = ""
    issue_type: str = "Task"


def _build_docx(rows: list[JiraRow], path: Path, headers: list[str] | None = None) -> Path:
    headers = headers or [
        "Key", "Summary", "Status", "Assignee",
        "Original Estimate", "Time Spent", "Labels", "Issue Type",
    ]
    doc = Document()
    doc.add_paragraph("Export Jira – Sprint AEP")
    table = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    for row in rows:
        cells = table.add_row().cells
        values = [
            row.key, row.summary, row.status, row.assignee,
            row.estimated, row.logged, row.labels, row.issue_type,
        ]
        for i, v in enumerate(values):
            cells[i].text = v
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    return path


@pytest.fixture
def tmp_docx(tmp_path):
    """Função-fábrica que cria um .docx sintético a partir de uma lista de JiraRow."""
    def _factory(rows: list[JiraRow], name: str = "export.docx", headers=None) -> Path:
        return _build_docx(rows, tmp_path / name, headers=headers)
    return _factory


@pytest.fixture
def jira_row_cls():
    return JiraRow
