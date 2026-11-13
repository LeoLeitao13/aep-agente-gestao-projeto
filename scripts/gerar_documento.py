"""Gera o documento final da Entrega 2 (.docx) — AEP 8S.

Segue a estrutura do `Modelo_Entrega2.docx`, com a seção 3 focada em 1 agente
(Agente de Gestão de Projetos), já pré-preenchida com os dados reais coletados
do board TR / Sprint 7 e dos 6 cenários de teste automatizados.

Campos ainda dependentes da equipe (nomes, ODS, repo) estão marcados com
colchetes `[ ... ]` para edição rápida.

Saída: `entrega_2/Entrega2_AgenteGestao.docx`
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
GRAFICOS = ROOT / "entrega_2" / "graficos"
OUT = ROOT / "entrega_2" / "Entrega2_AgenteGestao.docx"
OUT.parent.mkdir(parents=True, exist_ok=True)


# =====================================================================
# Utilitários de formatação
# =====================================================================
def set_cell_shading(cell, color_hex: str) -> None:
    from docx.oxml.ns import nsdecls
    from docx.oxml import parse_xml
    cell._tc.get_or_add_tcPr().append(
        parse_xml(rf'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    )


def add_heading_pt(doc: Document, text: str, level: int) -> None:
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)


def add_bullet(doc: Document, text: str) -> None:
    doc.add_paragraph(text, style="List Bullet")


def add_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
        set_cell_shading(hdr_cells[i], "1F2A44")
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            cells[i].vertical_alignment = WD_ALIGN_VERTICAL.TOP


def add_image(doc: Document, path: Path, width_cm: float = 15.0, caption: str = "") -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.italic = True
            r.font.size = Pt(9)


# =====================================================================
# Carga de dados reais
# =====================================================================
def load_indicadores() -> dict:
    path = ROOT / "data" / "output" / "indicadores_tr_sprint7.csv"
    out: dict = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            val = row["valor"]
            try:
                val = float(val) if val else None
            except ValueError:
                pass
            detail = json.loads(row["detalhe"]) if row["detalhe"] else None
            out[row["indicador"]] = {"value": val, "unit": row["unidade"], "detail": detail}
    return out


def load_metricas() -> list[dict]:
    path = ROOT / "data" / "output" / "metricas_entrega2.csv"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


CENARIO_DESC = {
    "C1_tipico_sprint_feliz": (
        "Sprint típica sem retrabalho: 4 tarefas, 3 concluídas e 1 em andamento.",
        "planejadas=4, concluídas=3, canceladas=0, ajuste=0, retrabalho=0%, est=150h, real=138h",
    ),
    "C2_sprint_com_retrabalho": (
        "Sprint com retrabalho relevante: 4 tarefas concluídas, 2 marcadas como ajuste.",
        "concluídas=4, ajuste=2, taxa_retrabalho=50%, horas conservadas",
    ),
    "C3_tarefas_canceladas_e_backlog": (
        "Sprint com tarefas canceladas e itens de backlog (To Do/Backlog).",
        "planejadas=4, concluídas=1, canceladas=1, horas estimadas=85h, realizadas=39h",
    ),
    "C4_status_pt_br_misto": (
        "Teste de borda: status em PT-BR com acentos, variações de caixa (Concluído / Concluída / em andamento / A Fazer) e detecção de ajuste via label 'hotfix'.",
        "concluídas=2, ajuste=1, taxa_retrabalho=50%, horas=64h",
    ),
    "C5_borda_vazio": (
        "Teste de borda: export vazio (zero tarefas) — valida divisão por zero e saída consistente.",
        "todos os contadores=0, taxa_retrabalho=0%, horas=0h, nenhum erro",
    ),
    "C6_meta_1000h_aderente": (
        "Cenário aderente à meta de 1.000h: 10 tarefas de 100h cada, concluídas, 950h realizadas.",
        "planejadas=10, concluídas=10, horas_estimadas=1000h (aderente), realizadas=950h",
    ),
}


# =====================================================================
# Montagem do documento
# =====================================================================
def build_document() -> Path:
    doc = Document()

    # --------- estilo base
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # --------- Capa e Identificação
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("Entrega 2 — Testes, Estatísticas e Demonstração do Agente")
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Arquitetura de Software · Gestão de Projetos · Tecnologias Emergentes")
    r.italic = True
    r.font.size = Pt(12)

    doc.add_paragraph()

    add_heading_pt(doc, "Capa e Identificação", level=1)
    identificacao = [
        ("Título do projeto/ecossistema de agentes", "Escola de TI — SAUF BR (Agente de Gestão de Projetos)"),
        ("Curso/Disciplina/Turma", "Engenharia de Software — 8º Semestre · AEP 8S-1B-1"),
        ("Integrantes da equipe (3) e papéis", "[ Integrante 1 — papel ] · [ Integrante 2 — papel ] · [ Integrante 3 — papel ]"),
        ("ODS escolhida", "[ Ex.: ODS 4 — Educação de Qualidade ]"),
        ("Link/repositório da implementação", "[ URL do repositório Git ]"),
        ("Data", datetime.now().strftime("%d/%m/%Y")),
    ]
    add_table(doc, ["Campo", "Valor"], identificacao)
    doc.add_paragraph()

    nota = doc.add_paragraph()
    nr = nota.add_run(
        "Observação sobre o escopo: na Entrega 1 havia previsão de um ecossistema "
        "de 5 agentes; após replanejamento com o professor e a equipe, o escopo foi "
        "concentrado em 1 (um) agente — o Agente de Gestão de Projetos — com "
        "profundidade reforçada em arquitetura, testes e análise crítica. Esta "
        "entrega apresenta esse agente de forma completa."
    )
    nr.italic = True
    nr.font.size = Pt(10)

    doc.add_page_break()

    # --------- 1. Resumo Executivo
    add_heading_pt(doc, "1. Resumo Executivo", level=1)
    doc.add_paragraph(
        "Esta entrega apresenta os resultados dos testes e evidências do Agente de "
        "Gestão de Projetos, implementado em Python sob o estilo arquitetural "
        "Pipe-and-Filter e combinando os padrões Controller (GRASP), Factory Method, "
        "Adapter e Strategy (GoF). O agente consome exports do Jira (.csv ou .docx), "
        "normaliza as tarefas e produz um CSV padronizado com 8 indicadores de "
        "gestão (tarefas planejadas/concluídas/canceladas/ajuste, taxa de "
        "retrabalho, horas estimadas/realizadas, horas por integrante). "
        "Foram executados 6 cenários automatizados (casos típicos + bordas) "
        "obtendo 100% de taxa de acerto e tempo médio inferior a 4 ms por execução. "
        "Além dos cenários sintéticos, o pipeline foi validado contra o dado real "
        "do board TR (Sprint 7, 33 tarefas, 7 integrantes) com todos os indicadores "
        "batendo com a contagem visual do board. A principal conclusão é que a "
        "arquitetura modular adotada atendeu plenamente aos requisitos funcionais "
        "e evidenciou, no dado real, uma lacuna de processo (ausência de "
        "estimativa de horas pelo time) — ilustrando que o próprio agente passa a "
        "funcionar como instrumento de melhoria contínua."
    )

    # --------- 2. Ambiente e Metodologia de Teste
    add_heading_pt(doc, "2. Ambiente e Metodologia de Teste", level=1)
    doc.add_paragraph(
        "Ambiente de execução: Python 3.14 em macOS Darwin 25.6.0; "
        "dependências gerenciadas via venv (python-docx, pandas, matplotlib, pytest). "
        "Testes orquestrados com pytest; medições de tempo via time.perf_counter."
    )
    doc.add_paragraph(
        "Dados de entrada: (i) 6 arquivos .docx sintéticos gerados programaticamente "
        "nos próprios testes (cada cenário produz um .docx reproduzindo o layout "
        "de export do Jira); (ii) 1 export CSV real do projeto TR (Escola de TI — "
        "SAUF BR) extraído da Sprint 7, com 33 tarefas e 7 integrantes."
    )
    doc.add_paragraph(
        "Critérios gerais de avaliação: (a) taxa de acerto por cenário "
        "(indicadores obtidos vs esperados); (b) tempo de execução total do "
        "pipeline; (c) teste de regressão travando os valores do board real "
        "(qualquer alteração futura que mude os números é detectada)."
    )

    # --------- 3. Testes por Agente
    add_heading_pt(doc, "3. Testes, Estatísticas e Demonstração do Agente", level=1)
    add_heading_pt(doc, "Agente 1 — Agente de Gestão de Projetos", level=2)

    # 3.1 Confirmação Entrega 1
    add_heading_pt(doc, "Confirmação da base tecnológica e do modelo de interação (Entrega 1)", level=3)
    doc.add_paragraph(
        "Base tecnológica mantida conforme a Entrega 1: arquitetura própria em "
        "Python aplicando Pipe-and-Filter, com os quatro padrões de projeto "
        "exigidos (Controller, Factory Method, Adapter e Strategy). A integração "
        "com LLM (OpenAI) foi mantida como componente opcional e desacoplado — "
        "via LLMAdapter / NullLLMAdapter — garantindo que o pipeline rode em "
        "modo totalmente determinístico (sem chamada externa) quando a chave "
        "não está configurada, o que foi fundamental para a reprodutibilidade "
        "dos testes."
    )
    doc.add_paragraph(
        "Modelo de interação mantido: operação independente a partir de um "
        "artefato de entrada (export Jira), sem acoplamento síncrono com outros "
        "agentes. Única alteração em relação à Entrega 1: além do formato .docx, "
        "foi adicionado suporte a export .csv do Jira, pois a interface atual do "
        "Jira Cloud descontinuou o export direto para Word — a decisão foi "
        "absorvida no pipeline via um segundo Adapter concreto (CsvJiraAdapter), "
        "preservando todo o restante da arquitetura."
    )

    # 3.2 Casos de teste
    add_heading_pt(doc, "Casos de teste executados (mínimo de 5)", level=3)
    metricas = load_metricas()
    linhas_casos: list[list[str]] = []
    for i, m in enumerate(metricas, 1):
        nome = m["cenario"]
        desc, esperado = CENARIO_DESC.get(nome, ("—", "—"))
        inds = json.loads(m["indicadores_json"])
        resumo_obtido = "; ".join(
            f"{x['name']}={x['value']}" for x in inds
            if not isinstance(x["value"], dict)
        )
        linhas_casos.append([str(i), f"{nome} — {desc}", esperado, resumo_obtido])
    add_table(doc, ["Nº", "Cenário testado", "Resultado esperado", "Resultado obtido"], linhas_casos)

    # 3.3 Métricas e estatísticas
    add_heading_pt(doc, "Métricas e estatísticas coletadas", level=3)
    taxas = [float(m["taxa_acerto_%"]) for m in metricas]
    tempos = [float(m["duracao_seg"]) for m in metricas]
    taxa_media = sum(taxas) / len(taxas)
    tempo_medio_ms = sum(tempos) / len(tempos) * 1000
    tempo_max_ms = max(tempos) * 1000
    linhas_met = [
        ["Taxa de acerto/precisão", f"{taxa_media:.2f}%", "≥ 95% (meta Entrega 1)"],
        ["Tempo médio de resposta", f"{tempo_medio_ms:.2f} ms", "≤ 5000 ms por execução"],
        ["Tempo máximo observado", f"{tempo_max_ms:.2f} ms", "≤ 5000 ms (limite assert nos testes)"],
        ["Nº de cenários executados", f"{len(metricas)}", "≥ 5 cenários (rubrica)"],
        ["Cobertura de categorias de indicador", "8/8", "100% dos indicadores do agente"],
    ]
    add_table(doc, ["Métrica", "Valor obtido", "Meta/critério de aceitação (Entrega 1)"], linhas_met)

    # 3.4 Gráficos
    add_heading_pt(doc, "Gráfico(s) e visualização dos resultados", level=3)
    add_image(doc, GRAFICOS / "04_taxa_acerto.png", width_cm=15,
              caption="Figura 1 — Taxa de acerto por cenário (100% em todos os 6 testes).")
    add_image(doc, GRAFICOS / "03_tempo_execucao.png", width_cm=15,
              caption="Figura 2 — Tempo de execução do pipeline por cenário (ms).")
    add_image(doc, GRAFICOS / "01_status_tarefas.png", width_cm=15,
              caption="Figura 3 — Distribuição de tarefas por categoria, calculada contra o board real (Sprint 7 / TR).")
    add_image(doc, GRAFICOS / "02_horas_por_integrante.png", width_cm=15,
              caption="Figura 4 — Horas realizadas por integrante extraídas do export real do Jira.")

    # 3.5 Evidência antes/depois
    add_heading_pt(doc, "Evidência antes/depois", level=3)
    doc.add_paragraph("Antes (entrada bruta — export do Jira): 33 linhas no CSV com 86 colunas, "
                      "mescla de status em PT-BR (Em andamento, Tarefas pendentes, Em Revisão 1, Concluído), "
                      "tempos gastos armazenados em SEGUNDOS, 1 issue do tipo 'Ajuste' misturada "
                      "no backlog, sem qualquer agregação ou cálculo de taxa de retrabalho.")

    doc.add_paragraph("Depois (saída do agente — data/output/indicadores_tr_sprint7.csv):")
    ind = load_indicadores()
    linhas_depois = []
    for nome, info in ind.items():
        if isinstance(info["value"], dict) or nome == "horas_por_integrante":
            continue
        linhas_depois.append([nome, f"{info['value']}", info["unit"] or "—"])
    add_table(doc, ["Indicador", "Valor calculado", "Unidade"], linhas_depois)

    doc.add_paragraph("Detalhamento de horas por integrante (saída estruturada do agente):")
    detalhe_int = ind["horas_por_integrante"]["detail"] or {}
    linhas_int = [[nome, f"{v['estimadas']:.2f}", f"{v['realizadas']:.2f}"]
                  for nome, v in detalhe_int.items()]
    add_table(doc, ["Integrante", "Horas estimadas", "Horas realizadas"], linhas_int)

    doc.add_paragraph(
        "Validação cruzada com o board: o agente reporta 33 tarefas, exatamente "
        "o mesmo total visível no Jira (13 Itens Pendentes + 14 Em Andamento + "
        "3 Em Revisão + 0 Em Homologação + 3 Finalizados = 33). Os 3 "
        "finalizados correspondem aos 3 reportados como 'tarefas_concluidas' "
        "pelo agente. A única issue marcada como 'Ajuste' no Jira foi "
        "corretamente detectada pela Strategy correspondente."
    )

    # 3.6 Análise crítica
    add_heading_pt(doc, "Análise crítica do agente", level=3)
    doc.add_paragraph(
        "Os resultados confirmam plenamente a especificação da Entrega 1 em "
        "termos funcionais (todos os 8 indicadores exigidos são produzidos) e de "
        "arquitetura (os quatro padrões de projeto foram aplicados sem "
        "ajustes estruturais ao longo da implementação). O custo marginal de "
        "adicionar um novo formato de entrada (de .docx para .csv quando a UI do "
        "Jira removeu o export Word) foi de uma única classe nova "
        "(CsvJiraAdapter) sem tocar em Controller, Strategies ou Factory — "
        "evidência prática de que a aplicação do padrão Adapter se pagou "
        "imediatamente na primeira mudança de requisito."
    )
    doc.add_paragraph(
        "A principal descoberta não funcional veio do dado real: a soma de "
        "'horas estimadas' no board da Sprint 7 ficou em 0 h, pois o time não "
        "preenche o campo 'Estimativa original' no Jira. Esse é um achado "
        "operacional valioso — o indicador 'horas_estimadas' não só mede, como "
        "expõe uma lacuna de processo que impede, hoje, qualquer análise de "
        "aderência à meta de 1.000 h. Como contraprova, o cenário C6 "
        "(sintético) demonstra que o indicador funciona corretamente quando os "
        "dados existem (10 tarefas × 100 h = 1.000 h, aderente à meta com "
        "desvio 0)."
    )
    doc.add_paragraph(
        "Ajustes implementados em relação ao plano inicial: (i) adoção do "
        "Adapter também para o LLM, criando um NullLLMAdapter que mantém o "
        "pipeline 100% determinístico nos testes; (ii) normalização defensiva "
        "de status do Jira, aceitando variações com acento, caixa e sufixos "
        "numéricos (ex.: 'Em Revisão 1', 'Em Revisão 2'); (iii) conversão "
        "automática de tempo em segundos (formato do export CSV do Jira) para "
        "horas decimais, encapsulada no adapter."
    )

    # --------- 4. Consolidação
    add_heading_pt(doc, "4. Consolidação Estatística Geral do Ecossistema", level=1)
    doc.add_paragraph(
        "Dado que esta entrega concentrou o escopo em 1 agente (Agente de Gestão "
        "de Projetos — conforme nota de escopo na Identificação), a consolidação "
        "reúne os números agregados dos 6 cenários executados e da execução "
        "contra o dado real do Jira."
    )
    add_table(doc, ["Agente", "Nº de testes", "Taxa de sucesso", "Tempo médio (ms)"], [
        ["Agente de Gestão de Projetos", str(len(metricas)),
         f"{taxa_media:.2f}%", f"{tempo_medio_ms:.2f}"],
    ])
    add_image(doc, GRAFICOS / "05_consolidacao.png", width_cm=14,
              caption="Figura 5 — Consolidação dos indicadores da suíte de testes.")

    # --------- 5. Demonstração
    add_heading_pt(doc, "5. Demonstração dos Resultados", level=1)
    doc.add_paragraph(
        "A demonstração pode ser reproduzida localmente com os comandos:"
    )
    cmd = doc.add_paragraph()
    cr = cmd.add_run(
        "    cd projeto_gestao\n"
        "    python -m venv .venv && source .venv/bin/activate\n"
        "    pip install -r requirements.txt\n"
        "    python main.py tests/fixtures/jira_real_tr_sprint7.csv \\\n"
        "        --out data/output/indicadores_tr_sprint7.csv --verbose\n"
        "    pytest -v"
    )
    cr.font.name = "Consolas"
    cr.font.size = Pt(10)

    doc.add_paragraph(
        "Durante a defesa serão apresentados: (i) print do board Jira original "
        "(evidência 'antes'); (ii) execução ao vivo do pipeline; (iii) "
        "abertura do CSV gerado (evidência 'depois'); (iv) execução do "
        "pytest com os 21 testes passando (unitários + integração + regressão "
        "contra Jira real)."
    )

    # --------- 6. Retrospectiva
    add_heading_pt(doc, "6. Retrospectiva de Gestão do Projeto", level=1)
    add_heading_pt(doc, "Aderência à metodologia planejada", level=3)
    doc.add_paragraph(
        "A metodologia ágil baseada em sprints curtas no Jira foi seguida. "
        "Houve uma adaptação relevante: o escopo foi reduzido de 5 para 1 "
        "agente, com acordo prévio, priorizando profundidade (arquitetura "
        "correta + testes automatizados + regressão contra dado real) em "
        "lugar de amplitude (5 agentes implementados de forma rasa)."
    )
    add_heading_pt(doc, "O que funcionou bem", level=3)
    for item in [
        "Uso disciplinado de padrões de projeto desde o primeiro commit — "
        "cada novo indicador vira uma Strategy sem tocar em nada mais.",
        "Decoupling do LLM atrás de um Adapter — permitiu rodar todos os "
        "testes em modo determinístico, sem depender de rede ou chave.",
        "Teste de regressão contra o CSV real do Jira — qualquer mudança "
        "futura que altere os números do board é imediatamente detectada.",
        "Geração automatizada de .docx sintéticos nos próprios testes, "
        "evitando fixtures binárias comitadas desnecessariamente.",
    ]:
        add_bullet(doc, item)

    add_heading_pt(doc, "O que não funcionou / dificuldades enfrentadas", level=3)
    for item in [
        "A interface atual do Jira Cloud não oferece export .docx — "
        "exigiu criar um segundo Adapter (CsvJiraAdapter) em cima do CSV.",
        "O time não preenche 'Estimativa original' no board, o que zera o "
        "indicador de horas estimadas no dado real — virou uma oportunidade "
        "de melhoria de processo exposta pelo próprio agente.",
        "Formatos de hora heterogêneos no Jira (segundos no CSV, '3h 30m' "
        "no .docx) exigiram parsing defensivo.",
    ]:
        add_bullet(doc, item)

    add_heading_pt(doc, "Lições aprendidas", level=3)
    for item in [
        "Adapter é o padrão com maior retorno sobre investimento em "
        "projetos que leem dados de sistemas externos — a primeira mudança "
        "de formato já quita o custo inicial.",
        "Separar regras de negócio (Strategies) de orquestração "
        "(Controller) acelera brutalmente a criação de novos indicadores.",
        "Começar por uma suíte de testes com cenários sintéticos e só "
        "depois conectar ao dado real reduz o risco de retrabalho.",
        "Reduzir escopo proativamente (5 → 1 agente) e documentar a "
        "decisão é melhor do que entregar 5 agentes rasos.",
    ]:
        add_bullet(doc, item)

    # --------- 7. Conclusão
    add_heading_pt(doc, "7. Conclusão", level=1)
    doc.add_paragraph(
        "Os objetivos de aprendizagem da AEP foram atingidos: a equipe aplicou "
        "na prática um estilo arquitetural (Pipe-and-Filter) combinado com "
        "quatro padrões de projeto clássicos (Controller, Factory Method, "
        "Adapter, Strategy), mediu a solução quantitativamente com uma suíte "
        "automatizada e validou-a contra dados reais de uso do Jira. A "
        "escolha pelo aprofundamento em um único agente permitiu demonstrar "
        "não apenas que o código funciona, mas por quê funciona — explicitando "
        "o papel de cada padrão na resposta a uma mudança real de requisito."
    )
    doc.add_paragraph(
        "A conexão com a ODS escolhida [ ex.: ODS 4 — Educação de Qualidade, "
        "aderente ao projeto 'Escola de TI — SAUF BR' ] se dá pelo papel de "
        "instrumentação de processos educacionais/gestão: o agente transforma "
        "um artefato bruto (export do board) em indicadores acionáveis, "
        "apoiando decisões de gestão e expondo lacunas de processo — "
        "aplicável tanto ao projeto da disciplina quanto a cenários "
        "educacionais reais de coordenação de projetos acadêmicos."
    )

    # --------- 8. Referências
    add_heading_pt(doc, "8. Referências Utilizadas", level=1)
    for ref in [
        "GAMMA, E.; HELM, R.; JOHNSON, R.; VLISSIDES, J. Padrões de projeto: "
        "soluções reutilizáveis de software orientado a objetos. Porto "
        "Alegre: Bookman, 2000.",
        "LARMAN, C. Utilizando UML e padrões: uma introdução à análise e ao "
        "projeto orientados a objetos e ao desenvolvimento iterativo. 3. ed. "
        "Porto Alegre: Bookman, 2007.",
        "SHAW, M.; GARLAN, D. Software Architecture: Perspectives on an "
        "Emerging Discipline. Upper Saddle River: Prentice-Hall, 1996.",
        "ATLASSIAN. Jira Software — Documentation. Disponível em: "
        "<https://support.atlassian.com/jira-software-cloud/>. Acesso em: "
        f"{datetime.now().strftime('%d/%m/%Y')}.",
        "PYTEST DEVELOPERS. pytest documentation. Disponível em: "
        "<https://docs.pytest.org/>. Acesso em: "
        f"{datetime.now().strftime('%d/%m/%Y')}.",
        "PYTHON-DOCX. python-docx documentation. Disponível em: "
        "<https://python-docx.readthedocs.io/>. Acesso em: "
        f"{datetime.now().strftime('%d/%m/%Y')}.",
    ]:
        add_bullet(doc, ref)

    doc.save(str(OUT))
    return OUT


if __name__ == "__main__":
    out = build_document()
    print(f"✔ Documento gerado em: {out.relative_to(ROOT)}")
