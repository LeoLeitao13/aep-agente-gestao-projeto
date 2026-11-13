"""Gera gráficos (PNG) usados no documento da Entrega 2.

Fontes:
  * `data/output/indicadores_tr_sprint7.csv` — indicadores do dado real
  * `data/output/metricas_entrega2.csv`      — métricas dos 6 cenários de teste

Saída: `entrega_2/graficos/*.png`
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "entrega_2" / "graficos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 11, "figure.dpi": 140})


# ------------------------------------------------------------- dados
def _load_indicadores_reais() -> dict:
    """Lê o CSV de indicadores gerado contra o Jira real."""
    path = ROOT / "data" / "output" / "indicadores_tr_sprint7.csv"
    out: dict = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                val = float(row["valor"]) if row["valor"] else None
            except ValueError:
                val = None
            detail = json.loads(row["detalhe"]) if row["detalhe"] else None
            out[row["indicador"]] = {"value": val, "detail": detail}
    return out


def _load_metricas_testes() -> list[dict]:
    path = ROOT / "data" / "output" / "metricas_entrega2.csv"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------- 1. Barras por status
def grafico_status(ind: dict) -> Path:
    labels = ["Planejadas", "Concluídas", "Canceladas", "Ajuste"]
    values = [
        ind["tarefas_planejadas"]["value"],
        ind["tarefas_concluidas"]["value"],
        ind["tarefas_canceladas"]["value"],
        ind["tarefas_ajuste"]["value"],
    ]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color=["#4C78A8", "#54A24B", "#B2B2B2", "#E45756"])
    ax.set_title("Distribuição de tarefas por categoria — Sprint 7 (TR)")
    ax.set_ylabel("Quantidade de tarefas")
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(int(v)), ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(values) * 1.2 + 2)
    fig.tight_layout()
    path = OUT_DIR / "01_status_tarefas.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------- 2. Horas por integrante
def grafico_horas_integrante(ind: dict) -> Path:
    detalhe = ind["horas_por_integrante"]["detail"] or {}
    integrantes = list(detalhe.keys())
    realizadas = [detalhe[i]["realizadas"] for i in integrantes]

    # Ordena por horas realizadas, decrescente
    order = sorted(range(len(integrantes)), key=lambda i: realizadas[i], reverse=True)
    integrantes = [integrantes[i] for i in order]
    realizadas = [realizadas[i] for i in order]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(integrantes, realizadas, color="#4C78A8")
    ax.invert_yaxis()
    ax.set_title("Horas realizadas por integrante — Sprint 7 (TR)")
    ax.set_xlabel("Horas")
    for bar, v in zip(bars, realizadas):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}h", va="center")
    ax.set_xlim(0, max(realizadas + [1]) * 1.25)
    fig.tight_layout()
    path = OUT_DIR / "02_horas_por_integrante.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# -------------------------------------- 3. Tempo de execução por cenário
def grafico_tempo_cenarios(metricas: list[dict]) -> Path:
    cen = [m["cenario"] for m in metricas]
    tempos_ms = [float(m["duracao_seg"]) * 1000 for m in metricas]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(cen, tempos_ms, color="#72B7B2")
    ax.set_title("Tempo de execução do pipeline por cenário de teste")
    ax.set_ylabel("Tempo (ms)")
    ax.tick_params(axis="x", rotation=25)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    for bar, v in zip(bars, tempos_ms):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    path = OUT_DIR / "03_tempo_execucao.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ----------------------------- 4. Taxa de acerto por cenário (consolidação)
def grafico_taxa_acerto(metricas: list[dict]) -> Path:
    cen = [m["cenario"] for m in metricas]
    taxas = [float(m["taxa_acerto_%"]) for m in metricas]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(cen, taxas, color="#54A24B")
    ax.axhline(100, color="#CCCCCC", linestyle="--", linewidth=1)
    ax.set_title("Taxa de acerto por cenário — Agente de Gestão")
    ax.set_ylabel("Taxa de acerto (%)")
    ax.set_ylim(0, 110)
    ax.tick_params(axis="x", rotation=25)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    for bar, v in zip(bars, taxas):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{v:.0f}%", ha="center", va="bottom", fontweight="bold")
    fig.tight_layout()
    path = OUT_DIR / "04_taxa_acerto.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------- 5. Consolidação (seção 4 do modelo)
def grafico_consolidacao(metricas: list[dict]) -> Path:
    """Barras agrupadas: nº testes / taxa sucesso / tempo médio."""
    n_testes = len(metricas)
    taxa_media = sum(float(m["taxa_acerto_%"]) for m in metricas) / n_testes
    tempo_medio_ms = sum(float(m["duracao_seg"]) for m in metricas) / n_testes * 1000

    labels = ["Nº de casos", "Taxa de sucesso (%)", "Tempo médio (ms)"]
    valores = [n_testes, round(taxa_media, 2), round(tempo_medio_ms, 2)]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, valores, color=["#4C78A8", "#54A24B", "#72B7B2"])
    ax.set_title("Consolidação do Agente de Gestão — Entrega 2")
    for bar, v in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                f"{v}", ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(valores) * 1.2)
    fig.tight_layout()
    path = OUT_DIR / "05_consolidacao.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    ind = _load_indicadores_reais()
    metricas = _load_metricas_testes()
    paths = [
        grafico_status(ind),
        grafico_horas_integrante(ind),
        grafico_tempo_cenarios(metricas),
        grafico_taxa_acerto(metricas),
        grafico_consolidacao(metricas),
    ]
    for p in paths:
        print(f"✔ {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
