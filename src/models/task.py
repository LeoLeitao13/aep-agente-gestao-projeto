"""Modelo de domínio: representação canônica de uma tarefa do Jira."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    """Status canônicos normalizados a partir do Jira."""
    PLANEJADA = "planejada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"

    @classmethod
    def from_raw(cls, raw: str) -> "TaskStatus":
        """Mapeia status do Jira (pt/en) para o enum canônico.

        Casa também variantes com sufixo numérico (ex.: 'Em Revisão 1',
        'Em Revisão 2') removendo dígitos finais antes do lookup."""
        if not raw:
            return cls.PLANEJADA
        import re as _re
        normalized = _re.sub(r"\s*\d+\s*$", "", raw.strip().lower())
        mapping = {
            "to do": cls.PLANEJADA,
            "a fazer": cls.PLANEJADA,
            "backlog": cls.PLANEJADA,
            "aberto": cls.PLANEJADA,
            "open": cls.PLANEJADA,
            "planejada": cls.PLANEJADA,
            "tarefas pendentes": cls.PLANEJADA,
            "itens pendentes": cls.PLANEJADA,
            "pendente": cls.PLANEJADA,
            "in progress": cls.EM_ANDAMENTO,
            "em andamento": cls.EM_ANDAMENTO,
            "em progresso": cls.EM_ANDAMENTO,
            "doing": cls.EM_ANDAMENTO,
            "in review": cls.EM_ANDAMENTO,
            "em revisão": cls.EM_ANDAMENTO,
            "em revisao": cls.EM_ANDAMENTO,
            "em homologação": cls.EM_ANDAMENTO,
            "em homologacao": cls.EM_ANDAMENTO,
            "done": cls.CONCLUIDA,
            "concluído": cls.CONCLUIDA,
            "concluida": cls.CONCLUIDA,
            "concluída": cls.CONCLUIDA,
            "concluido": cls.CONCLUIDA,
            "finalizado": cls.CONCLUIDA,
            "finalizada": cls.CONCLUIDA,
            "resolvido": cls.CONCLUIDA,
            "resolvida": cls.CONCLUIDA,
            "closed": cls.CONCLUIDA,
            "fechado": cls.CONCLUIDA,
            "cancelado": cls.CANCELADA,
            "cancelada": cls.CANCELADA,
            "cancelled": cls.CANCELADA,
            "canceled": cls.CANCELADA,
        }
        return mapping.get(normalized, cls.PLANEJADA)


class TaskType(str, Enum):
    """Tipo canônico — necessário para separar tarefas de ajuste/retrabalho."""
    NORMAL = "normal"
    AJUSTE = "ajuste"

    @classmethod
    def from_raw(cls, raw: str, summary: str = "") -> "TaskType":
        """Infere o tipo: Jira raramente tem campo próprio, então procuramos
        em labels/summary (ex.: 'Ajuste', 'Retrabalho', 'Fix')."""
        hay = f"{raw or ''} {summary or ''}".lower()
        keywords = ("ajuste", "retrabalho", "rework", "bugfix", "hotfix", "correção", "correcao")
        return cls.AJUSTE if any(k in hay for k in keywords) else cls.NORMAL


@dataclass
class Task:
    """Representação canônica de uma tarefa, independente da origem."""
    key: str
    summary: str
    status: TaskStatus
    task_type: TaskType = TaskType.NORMAL
    assignee: str = ""
    estimated_hours: float = 0.0
    realized_hours: float = 0.0
    raw_status: str = ""
    labels: list[str] = field(default_factory=list)

    @property
    def is_concluida(self) -> bool:
        return self.status == TaskStatus.CONCLUIDA

    @property
    def is_cancelada(self) -> bool:
        return self.status == TaskStatus.CANCELADA

    @property
    def is_ajuste(self) -> bool:
        return self.task_type == TaskType.AJUSTE

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "summary": self.summary,
            "status": self.status.value,
            "task_type": self.task_type.value,
            "assignee": self.assignee,
            "estimated_hours": self.estimated_hours,
            "realized_hours": self.realized_hours,
        }
