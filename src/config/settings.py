"""Configurações globais carregadas via variáveis de ambiente."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    input_dir: Path = BASE_DIR / os.getenv("INPUT_DIR", "data/input").lstrip("./")
    output_dir: Path = BASE_DIR / os.getenv("OUTPUT_DIR", "data/output").lstrip("./")
    horas_estimadas_totais: float = float(os.getenv("HORAS_ESTIMADAS_TOTAIS", "1000"))

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
