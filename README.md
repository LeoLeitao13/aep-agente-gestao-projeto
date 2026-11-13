# Agente de Gestão de Projetos — AEP

Pipeline **Pipe-and-Filter** em Python que lê um export do Jira (.docx),
normaliza as tarefas e gera um CSV padronizado com os indicadores exigidos
pela Entrega 2:

| Indicador              | Fonte                                   |
|------------------------|-----------------------------------------|
| tarefas_planejadas     | total no sprint                         |
| tarefas_concluidas     | status mapeado para `concluida`         |
| tarefas_canceladas     | status mapeado para `cancelada`         |
| tarefas_ajuste         | labels/summary (ajuste, retrabalho...)  |
| taxa_retrabalho (%)    | `ajuste / concluidas`                   |
| horas_estimadas        | soma + comparação com meta de 1.000h    |
| horas_realizadas       | soma de time-spent                      |
| horas_por_integrante   | agregado por assignee                   |

## Padrões aplicados

| Padrão            | Onde                                                       |
|-------------------|------------------------------------------------------------|
| Controller (GRASP)| `src/controller/pipeline_controller.py`                    |
| Factory Method    | `src/factories/` (Adapter/Strategy/Filter)                 |
| Adapter (GoF)     | `src/adapters/docx_jira_adapter.py`, `llm_adapter.py`      |
| Strategy (GoF)    | `src/strategies/*`                                         |
| Pipe-and-Filter   | `src/pipeline/` (Reader → Processor → Indicator → Writer)  |

## Instalação

```bash
cd projeto_gestao
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # (opcional, para habilitar LLM)
```

## Execução

```bash
python main.py caminho/para/export_jira.docx --out data/output/indicadores.csv
# --llm para habilitar desambiguação via OpenAI
# --verbose para logs do pipeline
```

## Testes (Entrega 2)

```bash
pytest -v
```

Resulta em `data/output/metricas_entrega2.csv` com:
`cenario, duracao_seg, taxa_acerto_%, indicadores_json` — pronto para colar no
relatório da Entrega 2.
