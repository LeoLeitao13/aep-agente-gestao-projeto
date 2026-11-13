"""Registra o cenário C7 — execução contra o export REAL do Jira (anonimizado).

Esse é o teste mais forte do projeto (dado produtivo, não sintético), por isso
precisa aparecer na tabela de casos de teste e na consolidação estatística.

O script lê a fixture `tests/fixtures/jira_sprint7_anon.csv`, executa o
pipeline uma vez cronometrada, compara os indicadores obtidos contra o
gabarito (mesmo do test_regression_real_jira.py) e grava/atualiza uma linha
no `data/output/metricas_entrega2.csv` com o nome 'C7_jira_real_anonimizado'.

Idempotente: se já existir uma linha C7, substitui; senão, acrescenta.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.controller import PipelineController  # noqa: E402
FIXTURE = ROOT / "tests" / "fixtures" / "jira_sprint7_anon.csv"
METRICAS_CSV = ROOT / "data" / "output" / "metricas_entrega2.csv"

GABARITO = {
    "tarefas_planejadas": 33,
    "tarefas_concluidas": 3,
    "tarefas_canceladas": 0,
    "tarefas_ajuste": 1,
    "taxa_retrabalho": 33.33,
    "horas_estimadas": 0.0,
    "horas_realizadas": 7.92,
}


def run_once() -> tuple[float, float, list[dict]]:
    out = ROOT / "data" / "output" / "indicadores_tr_sprint7.csv"
    t0 = time.perf_counter()
    report = PipelineController(use_llm=False).run(FIXTURE, out)
    dur = time.perf_counter() - t0

    ind_dict = {i.name: i.value for i in report.context.indicators}
    acertos = sum(1 for k, v in GABARITO.items() if ind_dict.get(k) == v)
    acerto_pct = round(acertos / len(GABARITO) * 100, 2)

    indicadores_json = [
        {"name": i.name, "value": i.value, "unit": i.unit, "detail": i.detail}
        for i in report.context.indicators
    ]
    return dur, acerto_pct, indicadores_json


def upsert_c7(duracao: float, acerto: float, indicadores: list[dict]) -> None:
    METRICAS_CSV.parent.mkdir(parents=True, exist_ok=True)
    header = ["cenario", "duracao_seg", "taxa_acerto_%", "indicadores_json"]

    existing: list[dict] = []
    if METRICAS_CSV.exists():
        with METRICAS_CSV.open(encoding="utf-8") as fh:
            existing = [row for row in csv.DictReader(fh)
                        if row["cenario"] != "C7_jira_real_anonimizado"]

    row_c7 = {
        "cenario": "C7_jira_real_anonimizado",
        "duracao_seg": str(duracao),
        "taxa_acerto_%": str(acerto),
        "indicadores_json": json.dumps(indicadores, ensure_ascii=False),
    }
    existing.append(row_c7)

    with METRICAS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in existing:
            writer.writerow(row)


if __name__ == "__main__":
    dur, acerto, inds = run_once()
    upsert_c7(dur, acerto, inds)
    print(f"✔ C7 registrado em {METRICAS_CSV.relative_to(ROOT)}")
    print(f"  duracao={dur*1000:.2f} ms  acerto={acerto:.2f}%")
