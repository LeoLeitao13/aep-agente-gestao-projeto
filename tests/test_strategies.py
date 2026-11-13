"""Testes unitários das Strategies de indicadores."""
from __future__ import annotations

from src.models import Task, TaskStatus, TaskType
from src.strategies import (
    AdjustmentTasksStrategy,
    CancelledTasksStrategy,
    CompletedTasksStrategy,
    EstimatedHoursStrategy,
    HoursPerAssigneeStrategy,
    PlannedTasksStrategy,
    RealizedHoursStrategy,
    ReworkRateStrategy,
)


def _t(key, status, type_=TaskType.NORMAL, est=0.0, real=0.0, assignee=""):
    return Task(
        key=key, summary=key, status=status, task_type=type_,
        assignee=assignee, estimated_hours=est, realized_hours=real,
    )


def test_contagens_simples():
    tasks = [
        _t("A", TaskStatus.PLANEJADA),
        _t("B", TaskStatus.CONCLUIDA),
        _t("C", TaskStatus.CONCLUIDA),
        _t("D", TaskStatus.CANCELADA),
        _t("E", TaskStatus.CONCLUIDA, type_=TaskType.AJUSTE),
    ]
    assert PlannedTasksStrategy().calculate(tasks).value == 5
    assert CompletedTasksStrategy().calculate(tasks).value == 3
    assert CancelledTasksStrategy().calculate(tasks).value == 1
    assert AdjustmentTasksStrategy().calculate(tasks).value == 1


def test_taxa_retrabalho_sem_concluidas_nao_divide_por_zero():
    tasks = [_t("A", TaskStatus.CANCELADA, type_=TaskType.AJUSTE)]
    assert ReworkRateStrategy().calculate(tasks).value == 0.0


def test_taxa_retrabalho_percentual():
    tasks = [
        _t("A", TaskStatus.CONCLUIDA),
        _t("B", TaskStatus.CONCLUIDA),
        _t("C", TaskStatus.CONCLUIDA, type_=TaskType.AJUSTE),
        _t("D", TaskStatus.CONCLUIDA, type_=TaskType.AJUSTE),
    ]
    # 2 ajustes / 4 concluídas = 50%
    assert ReworkRateStrategy().calculate(tasks).value == 50.0


def test_horas_estimadas_e_realizadas_e_por_integrante():
    tasks = [
        _t("A", TaskStatus.CONCLUIDA, est=100, real=90, assignee="Ana"),
        _t("B", TaskStatus.CONCLUIDA, est=200, real=210, assignee="Bruno"),
        _t("C", TaskStatus.CONCLUIDA, est=150, real=140, assignee="Ana"),
    ]
    assert EstimatedHoursStrategy().calculate(tasks).value == 450.0
    assert RealizedHoursStrategy().calculate(tasks).value == 440.0
    result = HoursPerAssigneeStrategy().calculate(tasks)
    assert result.value["Ana"] == {"estimadas": 250.0, "realizadas": 230.0}
    assert result.value["Bruno"] == {"estimadas": 200.0, "realizadas": 210.0}
