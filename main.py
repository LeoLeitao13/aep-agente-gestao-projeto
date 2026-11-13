"""CLI do Agente de Gestão de Projetos.

Uso:
    python main.py <caminho_do_docx> [--out <csv>] [--llm]
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from src.config.settings import settings
from src.controller import PipelineController


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agente de Gestão — pipeline Pipe-and-Filter")
    parser.add_argument("source", type=Path, help="Arquivo .docx exportado do Jira")
    parser.add_argument(
        "--out",
        type=Path,
        default=settings.output_dir / "indicadores.csv",
        help="CSV de saída (default: data/output/indicadores.csv)",
    )
    parser.add_argument("--llm", action="store_true", help="Habilita uso do LLM para desambiguação")
    parser.add_argument("--verbose", action="store_true", help="Log detalhado")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    controller = PipelineController(use_llm=args.llm)
    report = controller.run(args.source, args.out)
    print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    print(f"\nCSV gerado em: {args.out}")


if __name__ == "__main__":
    main()
