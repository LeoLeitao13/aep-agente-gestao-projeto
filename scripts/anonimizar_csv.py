"""Gera uma versão anonimizada do export do Jira para uso como fixture pública.

Substitui nomes/IDs de pessoas por Dev1..DevN. Preserva estrutura do CSV
(mesmas colunas, mesma ordem, mesmo número de linhas) para que o
teste de regressão continue válido — só os rótulos de pessoa mudam.

Uso:
    python scripts/anonimizar_csv.py <entrada.csv> <saida.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

# Colunas que contêm nomes/IDs de pessoas no export do Jira em PT-BR.
PERSON_COLUMNS = {
    "Líder do projeto", "ID do líder do projeto",
    "Responsável", "ID do responsável",
    "Relator", "ID do relator",
    "Criador", "ID do criador",
    "Seguidores", "ID dos seguidores",
}


def anonimizar(entrada: Path, saida: Path) -> None:
    with entrada.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    headers = rows[0]

    # Índices de todas as colunas (inclusive duplicadas) que contêm PII
    person_indices = [i for i, h in enumerate(headers) if h.strip() in PERSON_COLUMNS]

    # Mapeia valores originais -> Dev1, Dev2, ...
    seen: dict[str, str] = {}

    def replace(value: str) -> str:
        raw = value.strip()
        if not raw:
            return value
        # Múltiplos valores separados por vírgula (ex.: lista de seguidores)
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        out = []
        for p in parts:
            if p not in seen:
                seen[p] = f"Dev{len(seen) + 1}"
            out.append(seen[p])
        return ", ".join(out)

    for row in rows[1:]:
        for idx in person_indices:
            if idx < len(row):
                row[idx] = replace(row[idx])

    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)

    print(f"✔ {saida} ({len(rows) - 1} linhas, {len(seen)} identidades substituídas)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python scripts/anonimizar_csv.py <entrada> <saida>")
        sys.exit(1)
    anonimizar(Path(sys.argv[1]), Path(sys.argv[2]))
