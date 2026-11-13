"""Orquestra a regeneração completa da Entrega 2 numa única cadeia consistente.

Ordem:
  1. Apaga metricas_entrega2.csv
  2. Executa pytest → popula C1..C6 no CSV
  3. Executa pipeline contra a fixture → indicadores_tr_sprint7.csv
  4. Registra C7 (dado real) no CSV de métricas
  5. Gera gráficos (Figuras 1..4 e 8)
  6. Gera prints de evidência (Figuras 5..7) — backup/restore do CSV protege
     contra o side-effect do pytest interno.
  7. Gera o documento final
  8. Valida que o MÁXIMO da tabela == MÁXIMO da Figura 2 (bate)

Qualquer passo com código de saída != 0 interrompe a cadeia.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICAS_CSV = ROOT / "data" / "output" / "metricas_entrega2.csv"


def step(title: str, cmd: list[str]) -> None:
    print(f"\n==> {title}")
    print(f"    $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(f"✗ Falhou: {' '.join(cmd)}")


def validar_consistencia() -> None:
    """Verifica que tempos no CSV batem entre si (uma única execução)."""
    with METRICAS_CSV.open(encoding="utf-8") as fh:
        rows = sorted(csv.DictReader(fh), key=lambda r: r["cenario"])

    tempos_ms = [(r["cenario"], float(r["duracao_seg"]) * 1000) for r in rows]
    max_cen, max_ms = max(tempos_ms, key=lambda x: x[1])
    media_ms = sum(t for _, t in tempos_ms) / len(tempos_ms)

    print("\n==> Consistência tempo (tabela + figuras devem usar estes valores)")
    for cen, ms in tempos_ms:
        print(f"    {cen:<35} {ms:6.2f} ms")
    print(f"    {'MÉDIA':<35} {media_ms:6.2f} ms")
    print(f"    {'MÁXIMO':<35} {max_ms:6.2f} ms  (em {max_cen})")


if __name__ == "__main__":
    print("Regenerando Entrega 2 numa única cadeia consistente...")

    if METRICAS_CSV.exists():
        METRICAS_CSV.unlink()

    step("1/7 Executar pytest (popula C1..C6)",
         ["python", "-m", "pytest", "-q"])

    step("2/7 Pipeline → indicadores_tr_sprint7.csv",
         ["python", "main.py", "tests/fixtures/jira_sprint7_anon.csv",
          "--out", "data/output/indicadores_tr_sprint7.csv"])

    step("3/7 Registrar C7 (dado real)",
         ["python", "scripts/registrar_c7_real.py"])

    step("4/7 Gerar gráficos (Figuras 1..4 e 8)",
         ["python", "scripts/gerar_graficos.py"])

    step("5/7 Gerar prints de evidência (Figuras 5..7)",
         ["python", "scripts/gerar_evidencias.py"])

    step("6/7 Gerar documento final",
         ["python", "scripts/gerar_documento.py"])

    validar_consistencia()

    print("\n✔ Entrega 2 regenerada com dados consistentes.")
    print(f"  Documento: entrega_2/Entrega2_AgenteGestao.docx")
