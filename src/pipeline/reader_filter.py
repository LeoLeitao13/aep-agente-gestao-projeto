"""Filter de leitura — delega ao Adapter correto."""
from __future__ import annotations

from pathlib import Path

from ..adapters import BaseInputAdapter
from .filter_base import BaseFilter, PipelineContext


class ReaderFilter(BaseFilter):
    def __init__(self, adapter: BaseInputAdapter, source: Path | str) -> None:
        self.adapter = adapter
        self.source = Path(source)

    def process(self, context: PipelineContext) -> PipelineContext:
        context.raw_records = self.adapter.adapt(self.source)
        context.metadata["source_file"] = str(self.source)
        context.metadata["total_registros_lidos"] = len(context.raw_records)
        return context
