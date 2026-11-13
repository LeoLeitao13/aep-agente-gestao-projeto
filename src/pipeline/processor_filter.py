"""Filter de tratamento de dados.

Transforma registros brutos em objetos `Task` canônicos.
Usa LLM apenas para desambiguar casos em que o status é vazio/estranho —
mantendo o pipeline determinístico por padrão.
"""
from __future__ import annotations

import logging

from ..adapters.llm_adapter import BaseLLMAdapter, NullLLMAdapter
from ..models import Task, TaskStatus, TaskType
from .filter_base import BaseFilter, PipelineContext

logger = logging.getLogger(__name__)

_LLM_SYSTEM_PROMPT = (
    "Você é um classificador de status de tarefas do Jira. "
    "Dado um texto de status, responda apenas com um JSON no formato: "
    '{"status": "planejada|em_andamento|concluida|cancelada"}'
)


class ProcessorFilter(BaseFilter):
    def __init__(self, llm: BaseLLMAdapter | None = None) -> None:
        self.llm = llm or NullLLMAdapter()

    def process(self, context: PipelineContext) -> PipelineContext:
        tasks: list[Task] = []
        ambiguos = 0
        for rec in context.raw_records:
            status = self._resolve_status(rec.get("status", ""))
            if status is None:
                ambiguos += 1
                status = self._ask_llm(rec)
            task_type = TaskType.from_raw(
                rec.get("issue_type", "") + " " + " ".join(rec.get("labels", [])),
                rec.get("summary", ""),
            )
            tasks.append(
                Task(
                    key=rec.get("key", ""),
                    summary=rec.get("summary", ""),
                    status=status,
                    task_type=task_type,
                    assignee=rec.get("assignee", ""),
                    estimated_hours=float(rec.get("estimated_hours") or 0),
                    realized_hours=float(rec.get("realized_hours") or 0),
                    raw_status=rec.get("status", ""),
                    labels=list(rec.get("labels", [])),
                )
            )
        context.tasks = tasks
        context.metadata["tarefas_normalizadas"] = len(tasks)
        context.metadata["classificacoes_llm"] = ambiguos
        return context

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _resolve_status(raw: str) -> TaskStatus | None:
        """Retorna None quando o status é ambíguo (para disparar LLM)."""
        if not raw or not raw.strip():
            return None
        return TaskStatus.from_raw(raw)

    def _ask_llm(self, record: dict) -> TaskStatus:
        if isinstance(self.llm, NullLLMAdapter):
            return TaskStatus.PLANEJADA
        try:
            prompt = (
                f"Status bruto: '{record.get('status', '')}'. "
                f"Resumo: '{record.get('summary', '')}'."
            )
            data = self.llm.extract_json(prompt, system=_LLM_SYSTEM_PROMPT)
            return TaskStatus(data.get("status", "planejada"))
        except Exception as e:  # noqa: BLE001
            logger.warning("Falha ao classificar via LLM — fallback para PLANEJADA: %s", e)
            return TaskStatus.PLANEJADA
