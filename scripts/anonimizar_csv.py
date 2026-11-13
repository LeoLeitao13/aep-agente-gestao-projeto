"""Gera uma versão anonimizada do export do Jira para uso como fixture pública.

Substitui nomes/IDs de pessoas por Dev1..DevN, **pareando o nome e o ID da
mesma pessoa no mesmo número** — assim Antonio (Dev1) e seu ID atlassian
também viram Dev1, em vez de Dev1 e Dev2.

Pares reconhecidos (coluna_nome ↔ coluna_id):
    Líder do projeto      ↔ ID do líder do projeto
    Responsável           ↔ ID do responsável
    Relator               ↔ ID do relator
    Criador               ↔ ID do criador
    Seguidores            ↔ ID dos seguidores

Preserva estrutura do CSV (mesmas colunas, mesma ordem, mesmo número de linhas).

Uso:
    python scripts/anonimizar_csv.py <entrada.csv> <saida.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

# Pares (coluna_do_nome, coluna_do_id) — nome + id de uma mesma pessoa.
PAIRS = [
    ("Líder do projeto", "ID do líder do projeto"),
    ("Responsável", "ID do responsável"),
    ("Relator", "ID do relator"),
    ("Criador", "ID do criador"),
    ("Seguidores", "ID dos seguidores"),
]


def anonimizar(entrada: Path, saida: Path) -> None:
    with entrada.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    headers = rows[0]

    # Índices de cada coluna (pode haver duplicadas; cobrimos todas)
    def _idxs(name: str) -> list[int]:
        return [i for i, h in enumerate(headers) if h.strip() == name]

    pair_indices: list[tuple[list[int], list[int]]] = [
        (_idxs(name_col), _idxs(id_col)) for name_col, id_col in PAIRS
    ]

    # Mapeamento identidade (nome ou id) → "DevN"
    pessoa_para_dev: dict[str, str] = {}
    next_num = 1

    def assign(identificador: str) -> str:
        nonlocal next_num
        if identificador in pessoa_para_dev:
            return pessoa_para_dev[identificador]
        token = f"Dev{next_num}"
        pessoa_para_dev[identificador] = token
        next_num += 1
        return token

    def link(nome: str, id_: str) -> None:
        """Garante que nome e id compartilhem o mesmo DevN."""
        nome_dev = pessoa_para_dev.get(nome)
        id_dev = pessoa_para_dev.get(id_)
        if nome_dev and not id_dev:
            pessoa_para_dev[id_] = nome_dev
        elif id_dev and not nome_dev:
            pessoa_para_dev[nome] = id_dev
        elif not nome_dev and not id_dev:
            token = assign(nome)
            pessoa_para_dev[id_] = token
        # Se ambos já existem (com números diferentes), mantemos — divergência
        # improvável porque linkamos antes de alocar.

    def split_multi(raw: str) -> list[str]:
        return [p.strip() for p in raw.split(",") if p.strip()]

    # Passo 1 — link de pares (nome ↔ id) para cada linha
    for row in rows[1:]:
        for name_idxs, id_idxs in pair_indices:
            # Casa posicionalmente as duas listas de índices
            for name_idx, id_idx in zip(name_idxs, id_idxs):
                if name_idx >= len(row) or id_idx >= len(row):
                    continue
                nomes = split_multi(row[name_idx])
                ids = split_multi(row[id_idx])
                if len(nomes) == len(ids):
                    for n, i in zip(nomes, ids):
                        link(n, i)
                else:
                    # Quantidades diferentes: só garante que cada nome/id tem token
                    for n in nomes:
                        assign(n)
                    for i in ids:
                        assign(i)

    # Passo 2 — substituição efetiva em todas as colunas conhecidas
    all_person_idxs: set[int] = set()
    for name_idxs, id_idxs in pair_indices:
        all_person_idxs.update(name_idxs)
        all_person_idxs.update(id_idxs)

    def replace(value: str) -> str:
        if not value or not value.strip():
            return value
        parts = split_multi(value)
        out = [assign(p) for p in parts]
        return ", ".join(out)

    for row in rows[1:]:
        for idx in all_person_idxs:
            if idx < len(row):
                row[idx] = replace(row[idx])

    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)

    pessoas_unicas = len(set(pessoa_para_dev.values()))
    print(f"✔ {saida} ({len(rows) - 1} linhas; "
          f"{len(pessoa_para_dev)} identificadores → {pessoas_unicas} pessoas únicas)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python scripts/anonimizar_csv.py <entrada> <saida>")
        sys.exit(1)
    anonimizar(Path(sys.argv[1]), Path(sys.argv[2]))
