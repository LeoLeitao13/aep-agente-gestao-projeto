"""Regressão contra dados reais exportados do Jira (Sprint 7, anonimizados).

Trava os indicadores observados em 2026-11-12 no board usado como referência.
A fixture `jira_sprint7_anon.csv` é a cópia anonimizada do export real
(nomes trocados por Dev1..DevN via scripts/anonimizar_csv.py).

Qualquer mudança futura de código que altere esses números precisa ser
justificada e o gabarito atualizado nesta própria suíte.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.controller import PipelineController

FIXTURE = Path(__file__).parent / "fixtures" / "jira_sprint7_anon.csv"

GABARITO = {
    "tarefas_planejadas": 33,
    "tarefas_concluidas": 3,
    "tarefas_canceladas": 0,
    "tarefas_ajuste": 1,
    "taxa_retrabalho": 33.33,
    "horas_estimadas": 0.0,
    "horas_realizadas": 7.92,
}

HORAS_POR_INTEGRANTE = {
    "Dev1": {"estimadas": 0.0, "realizadas": 0.0},
    "Dev11": {"estimadas": 0.0, "realizadas": 0.0},
    "Dev3": {"estimadas": 0.0, "realizadas": 2.77},
    "Dev5": {"estimadas": 0.0, "realizadas": 2.0},
    "Dev7": {"estimadas": 0.0, "realizadas": 1.15},
    "Dev9": {"estimadas": 0.0, "realizadas": 0.0},
    "Não atribuído": {"estimadas": 0.0, "realizadas": 2.0},
}


@pytest.fixture(scope="module")
def indicadores(tmp_path_factory):
    out = tmp_path_factory.mktemp("regressao") / "ind.csv"
    report = PipelineController(use_llm=False).run(FIXTURE, out)
    return {i.name: i for i in report.context.indicators}


@pytest.mark.parametrize("nome,valor_esperado", GABARITO.items())
def test_indicadores_batem_com_board_real(nome, valor_esperado, indicadores):
    assert nome in indicadores, f"Indicador {nome} não produzido"
    assert indicadores[nome].value == valor_esperado, (
        f"Indicador {nome} divergiu do board real "
        f"(esperado={valor_esperado}, obtido={indicadores[nome].value})"
    )


def test_horas_por_integrante_bate_com_time_real(indicadores):
    obtido = indicadores["horas_por_integrante"].value
    assert obtido == HORAS_POR_INTEGRANTE
