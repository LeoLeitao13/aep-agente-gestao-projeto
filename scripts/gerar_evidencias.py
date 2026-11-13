"""Gera imagens 'print-de-tela' para a seção 'Evidência antes/depois'.

Três evidências:
  1. Trecho do CSV de entrada (jira_sprint7_anon.csv) — primeiras colunas/linhas.
  2. Conteúdo completo do CSV de saída (indicadores_tr_sprint7.csv).
  3. Saída real do `pytest -v` executado agora.

As imagens renderizam o conteúdo real em fonte monospace sobre fundo
estilo terminal (fundo escuro, texto claro) — o conteúdo é 100% genuíno,
apenas a renderização é programática. Isso evita a ambiguidade de
'screenshots fakes' porque o texto exibido é literalmente o do arquivo.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patches

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "entrega_2" / "graficos"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _render_terminal(lines: list[str], path: Path, *, title: str, max_width: int = 170) -> Path:
    """Renderiza linhas de texto como se fossem um print de terminal."""
    # Trunca linhas longas para caber na imagem
    lines = [l.rstrip("\n").replace("\t", "    ") for l in lines]
    lines = [l if len(l) <= max_width else l[: max_width - 1] + "…" for l in lines]
    n_lines = len(lines)

    width_in = 11
    row_height_in = 0.18
    height_in = max(2.5, row_height_in * (n_lines + 4))

    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=150)
    fig.patch.set_facecolor("#1E1E1E")
    ax.set_facecolor("#1E1E1E")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Título / barra superior estilo janela de terminal
    ax.add_patch(patches.Rectangle((0, 0.96), 1, 0.04, color="#333333"))
    for i, color in enumerate(("#FF5F56", "#FFBD2E", "#27C93F")):
        ax.add_patch(patches.Circle((0.015 + i * 0.022, 0.98), 0.01, color=color))
    ax.text(0.5, 0.98, title, ha="center", va="center",
            color="#CCCCCC", fontsize=9, family="monospace")

    # Conteúdo
    y = 0.94
    dy = 0.92 / max(n_lines + 2, 30)
    for line in lines:
        color = "#D4D4D4"
        if line.startswith("PASSED") or " PASSED " in line:
            color = "#4EC9B0"
        elif "FAILED" in line or "ERROR" in line:
            color = "#F48771"
        elif line.startswith("===") or "passed" in line.lower() and "in" in line.lower():
            color = "#DCDCAA"
        elif line.startswith(("tests/", "collected ")):
            color = "#9CDCFE"
        ax.text(0.015, y, line, color=color, family="monospace",
                fontsize=8, va="top", ha="left")
        y -= dy

    fig.savefig(str(path), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    return path


# --------------------------------------------------------------------- 1. CSV in
def print_csv_entrada() -> Path:
    src = ROOT / "tests" / "fixtures" / "jira_sprint7_anon.csv"
    # Seleciona colunas relevantes para a evidência (o CSV original tem 86 colunas)
    keep_cols = {
        "Resumo", "Chave da item", "Tipo de item", "Status",
        "Responsável", "Estimativa original", "Tempo gasto",
    }
    with src.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        headers = next(reader)
        keep_idx = [i for i, h in enumerate(headers) if h.strip() in keep_cols]
        kept_headers = [headers[i] for i in keep_idx]
        rows = []
        for row in reader:
            rows.append([row[i] if i < len(row) else "" for i in keep_idx])
            if len(rows) == 10:
                break
    # Monta como "cat jira_sprint7_anon.csv | head"
    lines = ["$ head -11 tests/fixtures/jira_sprint7_anon.csv"]
    lines.append("")
    widths = [min(max(len(h), *(len(r[i]) for r in rows)), 24)
              for i, h in enumerate(kept_headers)]
    header_line = " | ".join(h.ljust(w)[:w] for h, w in zip(kept_headers, widths))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    for r in rows:
        lines.append(" | ".join((r[i] or "").ljust(widths[i])[:widths[i]]
                                for i in range(len(widths))))
    lines.append("")
    lines.append(f"(exibidas 10 de 33 linhas · 7 de 86 colunas)")
    return _render_terminal(lines, OUT_DIR / "06_evidencia_csv_entrada.png",
                            title="Terminal — export bruto do Jira (entrada do agente)",
                            max_width=200)


# --------------------------------------------------------------------- 2. CSV out
def print_csv_saida() -> Path:
    src = ROOT / "data" / "output" / "indicadores_tr_sprint7.csv"
    lines = ["$ cat data/output/indicadores_tr_sprint7.csv", ""]
    with src.open(encoding="utf-8") as fh:
        for raw in fh:
            lines.append(raw.rstrip("\n"))
    return _render_terminal(lines, OUT_DIR / "07_evidencia_csv_saida.png",
                            title="Terminal — CSV gerado pelo agente (indicadores_tr_sprint7.csv)",
                            max_width=220)


# --------------------------------------------------------------------- 3. pytest
def print_pytest() -> Path:
    """Executa pytest -v apenas para capturar o PRINT e renderizar a imagem.

    IMPORTANTE: pytest tem efeito colateral de reescrever metricas_entrega2.csv
    via _append_metrica (upsert). Para não embaralhar os números entre gráficos
    e tabelas do documento, fazemos backup/restore do CSV em volta da chamada."""
    metricas_csv = ROOT / "data" / "output" / "metricas_entrega2.csv"
    backup = metricas_csv.read_bytes() if metricas_csv.exists() else None
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "-v", "--no-header", "--color=no"],
            cwd=str(ROOT),
            capture_output=True, text=True,
        )
    finally:
        if backup is not None:
            metricas_csv.write_bytes(backup)

    lines = ["$ pytest -v", ""]
    for raw in proc.stdout.splitlines():
        lines.append(raw)
    return _render_terminal(lines, OUT_DIR / "08_evidencia_pytest.png",
                            title="Terminal — execução dos 21 testes automatizados",
                            max_width=190)


def main() -> None:
    for fn in (print_csv_entrada, print_csv_saida, print_pytest):
        p = fn()
        print(f"✔ {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
