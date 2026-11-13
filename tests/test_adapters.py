"""Testes unitários do DocxJiraAdapter."""
from __future__ import annotations

from src.adapters import DocxJiraAdapter


def test_adapter_extrai_registros_de_tabela(tmp_docx, jira_row_cls):
    rows = [
        jira_row_cls("AEP-1", "Login", "Done", "Ana", "8h", "7h", "feature", "Task"),
        jira_row_cls("AEP-2", "Ajuste de login", "In Progress", "Bruno", "4h", "2h", "ajuste", "Task"),
    ]
    docx_path = tmp_docx(rows)

    records = DocxJiraAdapter().adapt(docx_path)

    assert len(records) == 2
    assert records[0]["key"] == "AEP-1"
    assert records[0]["estimated_hours"] == 8.0
    assert records[1]["labels"] == ["ajuste"]


def test_adapter_parseia_formatos_mistos_de_horas(tmp_docx, jira_row_cls):
    rows = [
        jira_row_cls("AEP-1", "x", "Done", "A", "1d 4h", "90m", "", "Task"),
        jira_row_cls("AEP-2", "y", "Done", "B", "2,5h", "0", "", "Task"),
    ]
    records = DocxJiraAdapter().adapt(tmp_docx(rows))
    assert records[0]["estimated_hours"] == 12.0   # 8+4
    assert records[0]["realized_hours"] == 1.5     # 90 minutos
    assert records[1]["estimated_hours"] == 2.5
