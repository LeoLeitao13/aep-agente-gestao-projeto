"""Testes de integração do pipeline — 5+ cenários exigidos pela Entrega 2.

Cada cenário:
  * monta um .docx sintético simulando o export do Jira;
  * executa `PipelineController.run()`;
  * compara os indicadores calculados contra um gabarito;
  * registra tempo de execução + taxa de acerto no arquivo
    `data/output/metricas_entrega2.csv` (que pode ser colado na AEP).
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.controller import PipelineController

METRICAS_CSV = Path(__file__).resolve().parents[1] / "data" / "output" / "metricas_entrega2.csv"
METRICAS_CSV.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Cenario:
    nome: str
    rows: list
    esperado: dict  # indicador -> valor esperado


# --------------------------------------------------------------------------- utils
def _get_value(indicadores, nome):
    for ind in indicadores:
        if ind["name"] == nome:
            return ind["value"]
    raise AssertionError(f"Indicador ausente: {nome}")


def _taxa_acerto(esperado: dict, obtido_list: list) -> float:
    acertos = 0
    for nome, valor in esperado.items():
        atual = _get_value(obtido_list, nome)
        if atual == valor:
            acertos += 1
    return round(acertos / len(esperado) * 100, 2)


def _append_metrica(cenario: str, duracao: float, acerto: float, indicadores: list) -> None:
    is_new = not METRICAS_CSV.exists()
    with METRICAS_CSV.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if is_new:
            writer.writerow(["cenario", "duracao_seg", "taxa_acerto_%", "indicadores_json"])
        writer.writerow([cenario, duracao, acerto, json.dumps(indicadores, ensure_ascii=False)])


# ------------------------------------------------------------------- fábrica cenários
def _cenarios(jira_row_cls) -> list[Cenario]:
    return [
        Cenario(
            nome="C1_tipico_sprint_feliz",
            rows=[
                jira_row_cls("AEP-1", "Login", "Done", "Ana", "40h", "38h", "feature"),
                jira_row_cls("AEP-2", "Dashboard", "Done", "Bruno", "60h", "58h", "feature"),
                jira_row_cls("AEP-3", "Relatórios", "Done", "Ana", "30h", "32h", "feature"),
                jira_row_cls("AEP-4", "Deploy", "In Progress", "Carla", "20h", "10h", ""),
            ],
            esperado={
                "tarefas_planejadas": 4,
                "tarefas_concluidas": 3,
                "tarefas_canceladas": 0,
                "tarefas_ajuste": 0,
                "taxa_retrabalho": 0.0,
                "horas_estimadas": 150.0,
                "horas_realizadas": 138.0,
            },
        ),
        Cenario(
            nome="C2_sprint_com_retrabalho",
            rows=[
                jira_row_cls("AEP-10", "Feature A", "Done", "Ana", "50h", "48h", "feature"),
                jira_row_cls("AEP-11", "Feature B", "Done", "Bruno", "50h", "52h", "feature"),
                jira_row_cls("AEP-12", "Ajuste Feature A", "Done", "Ana", "10h", "12h", "ajuste"),
                jira_row_cls("AEP-13", "Ajuste Feature B", "Done", "Bruno", "10h", "8h", "ajuste"),
            ],
            esperado={
                "tarefas_concluidas": 4,
                "tarefas_ajuste": 2,
                "taxa_retrabalho": 50.0,  # 2 / 4
                "horas_estimadas": 120.0,
                "horas_realizadas": 120.0,
            },
        ),
        Cenario(
            nome="C3_tarefas_canceladas_e_backlog",
            rows=[
                jira_row_cls("AEP-20", "Login", "Done", "Ana", "40h", "39h", ""),
                jira_row_cls("AEP-21", "Export CSV", "Cancelled", "Bruno", "20h", "0h", ""),
                jira_row_cls("AEP-22", "Perfil usuário", "To Do", "Carla", "15h", "0h", ""),
                jira_row_cls("AEP-23", "Deploy", "Backlog", "Ana", "10h", "0h", ""),
            ],
            esperado={
                "tarefas_planejadas": 4,
                "tarefas_concluidas": 1,
                "tarefas_canceladas": 1,
                "horas_estimadas": 85.0,
                "horas_realizadas": 39.0,
            },
        ),
        Cenario(
            nome="C4_status_pt_br_misto",  # edge: termos pt-br, acento, caixas diferentes
            rows=[
                jira_row_cls("AEP-30", "Tela de cadastro", "Concluído", "Ana", "40h", "40h", ""),
                jira_row_cls("AEP-31", "Correção crítica", "Concluída", "Bruno", "6h", "8h", "hotfix"),
                jira_row_cls("AEP-32", "Setup CI/CD", "em andamento", "Carla", "12h", "4h", ""),
                jira_row_cls("AEP-33", "Prototipação", "A Fazer", "Daniel", "6h", "0h", ""),
            ],
            esperado={
                "tarefas_concluidas": 2,
                "tarefas_ajuste": 1,       # hotfix detectado
                "taxa_retrabalho": 50.0,   # 1 / 2
                "horas_estimadas": 64.0,
            },
        ),
        Cenario(
            nome="C5_borda_vazio",  # edge: zero tarefas (dividir por zero, horas 0 etc.)
            rows=[],
            esperado={
                "tarefas_planejadas": 0,
                "tarefas_concluidas": 0,
                "tarefas_canceladas": 0,
                "taxa_retrabalho": 0.0,
                "horas_estimadas": 0.0,
                "horas_realizadas": 0.0,
            },
        ),
        Cenario(
            nome="C6_meta_1000h_aderente",  # valida a regra das 1.000h
            rows=[
                jira_row_cls(f"AEP-{i}", f"Tarefa {i}", "Done", f"Dev{i%4}", "100h", "95h", "")
                for i in range(1, 11)
            ],
            esperado={
                "tarefas_planejadas": 10,
                "tarefas_concluidas": 10,
                "horas_estimadas": 1000.0,
                "horas_realizadas": 950.0,
            },
        ),
    ]


# ------------------------------------------------------------------- teste parametrizado
@pytest.mark.parametrize("cenario_idx", range(6), ids=[f"C{i+1}" for i in range(6)])
def test_pipeline_fim_a_fim(cenario_idx, tmp_docx, jira_row_cls, tmp_path):
    cenario = _cenarios(jira_row_cls)[cenario_idx]
    docx_path = tmp_docx(cenario.rows, name=f"{cenario.nome}.docx")
    out_csv = tmp_path / f"{cenario.nome}.csv"

    controller = PipelineController(use_llm=False)
    report = controller.run(docx_path, out_csv)

    indicadores = report.summary()["indicadores"]
    taxa = _taxa_acerto(cenario.esperado, indicadores)

    _append_metrica(cenario.nome, report.duration_seconds, taxa, indicadores)

    # Precisão mínima: 100 % para cenários típicos (estão explícitos); borda idem.
    assert taxa == 100.0, (
        f"[{cenario.nome}] taxa de acerto={taxa}%. "
        f"Esperado={cenario.esperado}. Obtido={indicadores}"
    )
    # Métrica de desempenho: pipeline precisa ser rápido
    assert report.duration_seconds < 5.0, f"Pipeline lento: {report.duration_seconds:.2f}s"
    assert out_csv.exists() and out_csv.stat().st_size > 0


def test_relatorio_consolidado_entrega2():
    """Após rodar os cenários, o CSV de métricas deve existir e ter header + linhas."""
    assert METRICAS_CSV.exists()
    with METRICAS_CSV.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        linhas = list(reader)
    assert header[:3] == ["cenario", "duracao_seg", "taxa_acerto_%"]
    assert len(linhas) >= 5, "A Entrega 2 exige no mínimo 5 cenários de teste"
