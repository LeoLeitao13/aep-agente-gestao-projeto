"""Factory Method para os Filters do pipeline Pipe-and-Filter."""
from __future__ import annotations

from pathlib import Path

from ..pipeline.csv_writer_filter import CsvWriterFilter
from ..pipeline.filter_base import BaseFilter
from ..pipeline.indicator_filter import IndicatorFilter
from ..pipeline.processor_filter import ProcessorFilter
from ..pipeline.reader_filter import ReaderFilter
from .adapter_factory import AdapterFactory
from .strategy_factory import StrategyFactory


class FilterFactory:
    """Constrói a sequência canônica de filtros do pipeline."""

    @staticmethod
    def build_pipeline(
        source: Path | str,
        output_path: Path | str,
        *,
        use_llm: bool = False,
    ) -> list[BaseFilter]:
        return [
            ReaderFilter(adapter=AdapterFactory.for_source(source), source=source),
            ProcessorFilter(llm=AdapterFactory.llm(force_null=not use_llm)),
            IndicatorFilter(strategies=StrategyFactory.default_set()),
            CsvWriterFilter(output_path=output_path),
        ]
