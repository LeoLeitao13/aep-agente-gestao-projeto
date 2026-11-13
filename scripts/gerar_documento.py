"""Preenche o Modelo_Entrega2.docx original, preservando logo, estilos e layout.

NÃO gera nada do zero — abre o modelo oficial e apenas:
  * substitui texto dos placeholders [ ... ] pelo conteúdo real do agente;
  * preenche as tabelas vazias do template (Identificação, Casos, Métricas, Consolidação);
  * insere os gráficos nos pontos indicados pelo próprio modelo;
  * remove os blocos dos Agentes 2 a 5 (escopo acordado com o professor: 1 agente).

Saída: entrega_2/Entrega2_AgenteGestao.docx
"""
from __future__ import annotations

import csv
import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path("/Users/leoleitao31/Documents/AEP/Modelo_Entrega2.docx")
GRAFICOS = ROOT / "entrega_2" / "graficos"
OUT = ROOT / "entrega_2" / "Entrega2_AgenteGestao.docx"
OUT.parent.mkdir(parents=True, exist_ok=True)


# =====================================================================
# Helpers de manipulação do .docx
# =====================================================================
def replace_paragraph_text(p: Paragraph, text: str) -> None:
    """Substitui o texto do parágrafo, preservando o estilo do próprio parágrafo."""
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    p.add_run(text)


def set_cell_text(cell, text: str) -> None:
    """Escreve texto na célula limpando qualquer conteúdo anterior."""
    cell.text = str(text)


def set_cell_text_keep_format(cell, text: str) -> None:
    """Como set_cell_text, mas preserva a formatação (bold/font/size/cor) do
    primeiro run da célula — necessário para substituir texto de cabeçalho
    sem quebrar a formatação visual das demais colunas."""
    runs = [r for p in cell.paragraphs for r in p.runs]
    bold = runs[0].bold if runs else None
    size = runs[0].font.size if runs else None
    font_name = runs[0].font.name if runs else None
    color = (runs[0].font.color.rgb
             if runs and runs[0].font.color and runs[0].font.color.rgb else None)
    cell.text = str(text)
    for p in cell.paragraphs:
        for r in p.runs:
            if bold is not None:
                r.bold = bold
            if size is not None:
                r.font.size = size
            if font_name:
                r.font.name = font_name
            if color is not None:
                r.font.color.rgb = color


def set_table_widths_cm(table, widths_cm: list[float]) -> None:
    """Define a largura (cm) de cada coluna em TODAS as linhas da tabela."""
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                cell.width = Cm(widths_cm[i])


def iter_body_items(doc):
    """Yields (element, Paragraph|Table) em ordem de documento."""
    body = doc.element.body
    paragraphs_by_elem = {p._element: p for p in doc.paragraphs}
    tables_by_elem = {t._element: t for t in doc.tables}
    for el in body.iterchildren():
        if el in paragraphs_by_elem:
            yield el, paragraphs_by_elem[el]
        elif el in tables_by_elem:
            yield el, tables_by_elem[el]


def find_paragraph(doc, text_fragment: str) -> Paragraph | None:
    for p in doc.paragraphs:
        if text_fragment in p.text:
            return p
    return None


def insert_paragraph_after(prev_paragraph: Paragraph, text: str = "", *, align=None, size: int | None = None, italic=False, bold=False) -> Paragraph:
    """Cria um novo parágrafo logo após `prev_paragraph` e devolve-o."""
    new_p_elem = OxmlElement("w:p")
    prev_paragraph._element.addnext(new_p_elem)
    new_para = Paragraph(new_p_elem, prev_paragraph._parent)
    if align is not None:
        new_para.alignment = align
    if text:
        run = new_para.add_run(text)
        if size:
            run.font.size = Pt(size)
        if italic:
            run.italic = True
        if bold:
            run.bold = True
    return new_para


def replace_placeholder_with_image(doc, marker: str, image_path: Path, *, caption: str, width_cm: float = 14.5) -> None:
    """Encontra o parágrafo-placeholder e substitui por imagem centralizada + legenda."""
    p = find_paragraph(doc, marker)
    if not p:
        return
    # limpa texto e insere imagem
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image_path), width=Cm(width_cm))
    # legenda ABNT abaixo
    cap = insert_paragraph_after(p, caption, align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True)
    _ = cap


def delete_elements_between(doc, start_marker: str, end_marker: str) -> int:
    """Remove todos os elementos entre o parágrafo contendo start_marker
    (incluído) e o parágrafo contendo end_marker (excluído).
    Devolve a quantidade de elementos removidos."""
    items = list(iter_body_items(doc))
    start = end = None
    for i, (_, obj) in enumerate(items):
        if isinstance(obj, Paragraph):
            if start is None and start_marker in obj.text:
                start = i
            elif start is not None and end is None and end_marker in obj.text:
                end = i
                break
    if start is None or end is None:
        raise RuntimeError(f"Marcadores não encontrados: {start_marker!r} / {end_marker!r}")
    removed = 0
    for el, _ in items[start:end]:
        el.getparent().remove(el)
        removed += 1
    return removed


def delete_table_rows(table, keep_indices: list[int]) -> None:
    """Mantém apenas as linhas cujos índices estão em keep_indices."""
    rows = list(table.rows)
    for i, row in enumerate(rows):
        if i not in keep_indices:
            row._element.getparent().remove(row._element)


# =====================================================================
# Carga dos dados reais
# =====================================================================
def load_indicadores() -> dict:
    path = ROOT / "data" / "output" / "indicadores_tr_sprint7.csv"
    out: dict = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                val = float(row["valor"]) if row["valor"] else None
            except ValueError:
                val = row["valor"]
            detail = json.loads(row["detalhe"]) if row["detalhe"] else None
            out[row["indicador"]] = {"value": val, "unit": row["unidade"], "detail": detail}
    return out


def load_metricas() -> list[dict]:
    """Lê o CSV de métricas e devolve ordenado por nome do cenário (C1, C2, …)."""
    path = ROOT / "data" / "output" / "metricas_entrega2.csv"
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return sorted(rows, key=lambda r: r["cenario"])


CENARIOS_INFO = {
    "C1_tipico_sprint_feliz": (
        "Sprint típica sem retrabalho (4 tarefas; 3 concluídas e 1 em andamento).",
        "planejadas=4; concluídas=3; canceladas=0; ajuste=0; retrabalho=0%; est=150h; real=138h",
    ),
    "C2_sprint_com_retrabalho": (
        "Sprint com retrabalho relevante (4 concluídas, 2 marcadas como ajuste).",
        "concluídas=4; ajuste=2; taxa_retrabalho=50%; horas conservadas",
    ),
    "C3_tarefas_canceladas_e_backlog": (
        "Sprint com tarefas canceladas e itens de backlog (To Do / Backlog).",
        "planejadas=4; concluídas=1; canceladas=1; est=85h; real=39h",
    ),
    "C4_status_pt_br_misto": (
        "Borda: status em PT-BR com acentos e caixas variadas (Concluído/Concluída/em andamento/A Fazer) e detecção de ajuste via label 'hotfix'.",
        "concluídas=2; ajuste=1; taxa_retrabalho=50%; est=64h",
    ),
    "C5_borda_vazio": (
        "Borda: export vazio (zero tarefas) — valida consistência em 0/0 (indicador N/A).",
        "todos os contadores=0; taxa_retrabalho=N/A; horas=0h; sem erro",
    ),
    "C6_meta_1000h_aderente": (
        "Cenário aderente à meta de 1.000h (10 tarefas × 100h cada, concluídas, 950h realizadas).",
        "planejadas=10; concluídas=10; est=1000h (aderente); real=950h",
    ),
    "C7_jira_real_anonimizado": (
        "Execução contra o export REAL do Jira (Sprint 7 do board TR; 33 tarefas; 6 integrantes anonimizados em Dev1..Dev6).",
        "planejadas=33; concluídas=3; canceladas=0; ajuste=1; retrabalho=33,33%; est=0h; real=7,92h",
    ),
}


# =====================================================================
# Preenchimento, seção por seção
# =====================================================================
def preencher_identificacao(doc) -> None:
    """Tabela 0 do modelo — primeira tabela após 'Capa e Identificação'."""
    t = doc.tables[0]
    valores = [
        "Escola de TI — SAUF BR (Agente de Gestão de Projetos)",
        "Engenharia de Software — 8º Semestre · Turma A",
        (
            "Karen Tanaka - 23026540-2 – Teste e QA\n"
            "Leonardo Leitão Souza - 23020085-2 - Desenvolvedor\n"
            "Antonio Ferreira de Lima - 23038173-2 - PO"
        ),
        "ODS 8 — Trabalho Decente e Crescimento Econômico",
        "https://github.com/LeoLeitao13/aep-agente-gestao-projeto",
        datetime.now().strftime("%d/%m/%Y"),
    ]
    for i, v in enumerate(valores):
        set_cell_text(t.rows[i].cells[1], v)


def preencher_resumo_executivo(doc) -> None:
    p = find_paragraph(doc, "Em até 10 linhas")
    replace_paragraph_text(p, (
        "Esta entrega apresenta os resultados dos testes e evidências do Agente de "
        "Gestão de Projetos, implementado em Python sob o estilo arquitetural "
        "Pipe-and-Filter e combinando os padrões Controller (GRASP), Factory Method, "
        "Adapter e Strategy (GoF). O agente consome exports do Jira (.csv/.docx), "
        "normaliza as tarefas e produz um CSV padronizado com 8 indicadores de "
        "gestão. Foram executados 7 cenários automatizados — 2 típicos, 4 de borda e 1 contra o export real do Jira (Sprint 7 do board TR, 33 tarefas, 6 integrantes anonimizados em Dev1..Dev6) — com "
        "100% de taxa de acerto e tempo médio inferior a 4 ms por execução. "
        "A execução contra o dado produtivo tem todos os indicadores batendo "
        "com a contagem visual do board (13 pendentes + 14 em andamento + 3 em "
        "revisão + 3 finalizados = 33). A principal conclusão é que a arquitetura modular adotada "
        "atendeu plenamente aos requisitos funcionais e expôs, no dado real, uma "
        "lacuna de processo (ausência de estimativa de horas pelo time) — "
        "ilustrando que o próprio agente passa a atuar como instrumento de "
        "melhoria contínua."
    ))


def preencher_ambiente(doc) -> None:
    p = find_paragraph(doc, "Descreva como os testes foram conduzidos")
    replace_paragraph_text(p, (
        "Ambiente de execução: Python 3.14 em macOS (Darwin 25.6.0), dependências "
        "gerenciadas via venv (python-docx, pandas, matplotlib, pytest). Testes "
        "orquestrados com pytest; medições de tempo via time.perf_counter. "
        "Dados de entrada: (i) 6 arquivos .docx sintéticos gerados programaticamente "
        "nos próprios testes (cada cenário produz um .docx reproduzindo o layout do "
        "export do Jira); (ii) 1 export CSV real do projeto TR (Escola de TI — SAUF "
        "BR), Sprint 7, com 33 tarefas e 6 integrantes, utilizado como fixture "
        "anonimizada (nomes substituídos por Dev1..Dev6; o rótulo 'Não atribuído' "
        "que aparece nos gráficos é uma categoria de agregação para tarefas sem "
        "responsável, não uma 7ª pessoa). Critérios gerais de "
        "avaliação: (a) taxa de acerto por cenário (indicadores obtidos vs. "
        "esperados); (b) tempo de execução total do pipeline; (c) teste de "
        "regressão travando os valores do board real, detectando automaticamente "
        "qualquer alteração futura."
    ))


def preencher_agente_1(doc, metricas: list[dict], ind: dict) -> None:
    # Troca o título do Agente 1 (que era 'Agente de Documentação')
    for p in doc.paragraphs:
        if "Agente 1 —" in p.text and "Agente de Documentação" in p.text:
            replace_paragraph_text(p, "Agente de Gestão de Projetos")
            break

    # 3.1 Confirmação Entrega 1
    p_conf = find_paragraph(doc, "Confirme se a base tecnológica")
    replace_paragraph_text(p_conf, (
        "Base tecnológica mantida conforme a Entrega 1: arquitetura própria em "
        "Python aplicando o estilo arquitetural Pipe-and-Filter, com os quatro "
        "padrões de projeto exigidos (Controller — GRASP; Factory Method, Adapter "
        "e Strategy — GoF). A integração com LLM (OpenAI) foi mantida como "
        "componente opcional e desacoplado via LLMAdapter / NullLLMAdapter, "
        "garantindo que o pipeline rode em modo totalmente determinístico (sem "
        "chamada externa) quando a chave não estiver configurada — essencial para "
        "a reprodutibilidade dos testes. Modelo de interação mantido: operação "
        "independente a partir de um artefato de entrada (export do Jira), sem "
        "acoplamento síncrono com outros agentes. Única alteração em relação à "
        "Entrega 1: além do formato .docx, foi adicionado suporte a export .csv, "
        "pois a interface atual do Jira Cloud descontinuou o export direto para "
        "Word; a mudança foi absorvida com a criação de um segundo Adapter "
        "concreto (CsvJiraAdapter), preservando todo o restante da arquitetura."
    ))

    # 3.2 Casos de teste — Tabela 1 (modelo tem 5 linhas; acrescentamos as extras)
    def _fmt_obtido(indicadores: list[dict]) -> str:
        """Formata a coluna 'Resultado obtido' tratando None como 'N/A'."""
        parts = []
        for x in indicadores:
            if isinstance(x["value"], dict):
                continue
            val = "N/A" if x["value"] is None else x["value"]
            parts.append(f"{x['name']}={val}")
        return "; ".join(parts)

    t_casos = doc.tables[1]
    for i, m in enumerate(metricas[:5]):
        nome = m["cenario"]
        desc, esperado = CENARIOS_INFO.get(nome, ("—", "—"))
        inds = json.loads(m["indicadores_json"])
        set_cell_text(t_casos.rows[i + 1].cells[1], f"{nome} — {desc}")
        set_cell_text(t_casos.rows[i + 1].cells[2], esperado)
        set_cell_text(t_casos.rows[i + 1].cells[3], _fmt_obtido(inds))

    # Cenários adicionais (C6, C7) — adiciona novas linhas no fim da tabela
    for idx, m in enumerate(metricas[5:], start=6):
        desc, esperado = CENARIOS_INFO.get(m["cenario"], ("—", "—"))
        inds = json.loads(m["indicadores_json"])
        new_row = t_casos.add_row().cells
        set_cell_text(new_row[0], str(idx))
        set_cell_text(new_row[1], f"{m['cenario']} — {desc}")
        set_cell_text(new_row[2], esperado)
        set_cell_text(new_row[3], _fmt_obtido(inds))

    # 3.3 Métricas — Tabela 2
    taxas = [float(m["taxa_acerto_%"]) for m in metricas]
    tempos = [float(m["duracao_seg"]) for m in metricas]
    taxa_media = sum(taxas) / len(taxas)
    tempo_medio_ms = sum(tempos) / len(tempos) * 1000
    tempo_max_ms = max(tempos) * 1000

    t_met = doc.tables[2]
    set_cell_text(t_met.rows[1].cells[1], f"{taxa_media:.2f}%")
    set_cell_text(t_met.rows[1].cells[2], "≥ 95% (meta Entrega 1)")
    set_cell_text(t_met.rows[2].cells[1], f"{tempo_medio_ms:.2f} ms")
    set_cell_text(t_met.rows[2].cells[2], "≤ 5000 ms por execução")
    # Linha "[outra métrica]" — troca por cobertura de indicadores
    set_cell_text(t_met.rows[3].cells[0], "Cobertura de indicadores exigidos (8 ao todo)")
    set_cell_text(t_met.rows[3].cells[1], "8/8 (100%)")
    set_cell_text(t_met.rows[3].cells[2], "100% dos indicadores exigidos pela Entrega 1")

    # Linha extra: tempo máximo
    extra = t_met.add_row().cells
    set_cell_text(extra[0], "Tempo máximo observado em um cenário")
    set_cell_text(extra[1], f"{tempo_max_ms:.2f} ms")
    set_cell_text(extra[2], "≤ 5000 ms (limite do assert)")

    # Linha extra: número de cenários
    extra2 = t_met.add_row().cells
    set_cell_text(extra2[0], "Nº de cenários de teste executados")
    set_cell_text(extra2[1], f"{len(metricas)} (6 sintéticos + 1 com dado real do Jira)")
    set_cell_text(extra2[2], "≥ 5 cenários (rubrica)")

    # 3.4 Gráficos — substituir o placeholder por gráfico principal + anexos
    p_graf = find_paragraph(doc, "Insira aqui gráfico(s)")
    for r in list(p_graf.runs):
        r._element.getparent().remove(r._element)
    p_graf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_graf.add_run().add_picture(str(GRAFICOS / "04_taxa_acerto.png"), width=Cm(14.5))
    insert_paragraph_after(
        p_graf,
        "Figura 1 — Taxa de acerto por cenário (100% nos 7 testes).",
        align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True,
    )

    # Figuras adicionais (empilhadas logo abaixo, antes do próximo heading)
    anchor = find_paragraph(doc, "Figura 1 — Taxa de acerto")
    for img, cap in [
        ("03_tempo_execucao.png", "Figura 2 — Tempo de execução do pipeline por cenário (ms)."),
        ("01_status_tarefas.png", "Figura 3 — Distribuição de tarefas por categoria (Sprint 7 / TR)."),
        ("02_horas_por_integrante.png", "Figura 4 — Horas realizadas por integrante (export real anonimizado)."),
    ]:
        img_p = insert_paragraph_after(anchor, align=WD_ALIGN_PARAGRAPH.CENTER)
        img_p.add_run().add_picture(str(GRAFICOS / img), width=Cm(14.5))
        cap_p = insert_paragraph_after(img_p, cap, align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True)
        anchor = cap_p

    # 3.5 Evidência antes/depois (texto + 3 prints reais)
    p_evid = find_paragraph(doc, "Insira prints, trechos de código ou saídas reais")
    replace_paragraph_text(p_evid, (
        "Esta seção apresenta três evidências reais da atuação do agente sobre o "
        "dado produtivo (Sprint 7 do board TR, 33 tarefas). O conteúdo dos três "
        "prints a seguir é extraído diretamente dos arquivos do repositório e da "
        "execução dos testes automatizados."
    ))

    # Figura 5 — print do CSV de entrada
    anchor = p_evid
    img_p = insert_paragraph_after(anchor, align=WD_ALIGN_PARAGRAPH.CENTER)
    img_p.add_run().add_picture(str(GRAFICOS / "06_evidencia_csv_entrada.png"), width=Cm(15.5))
    cap_p = insert_paragraph_after(
        img_p,
        "Figura 5 (antes) — trecho do CSV bruto exportado do Jira "
        "(tests/fixtures/jira_sprint7_anon.csv): 86 colunas, status em PT-BR "
        "misturados, tempos em segundos.",
        align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True,
    )

    # Figura 6 — print do CSV de saída
    img_p = insert_paragraph_after(cap_p, align=WD_ALIGN_PARAGRAPH.CENTER)
    img_p.add_run().add_picture(str(GRAFICOS / "07_evidencia_csv_saida.png"), width=Cm(15.5))
    cap_p = insert_paragraph_after(
        img_p,
        "Figura 6 (depois) — CSV padronizado gerado pelo agente "
        "(data/output/indicadores_tr_sprint7.csv): 8 indicadores de gestão em 4 "
        "colunas semânticas.",
        align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True,
    )

    # Texto de ponte explicando a validação cruzada
    cap_p = insert_paragraph_after(
        cap_p,
        "Validação cruzada com o board (visual): 13 Itens Pendentes + 14 Em "
        "Andamento + 3 Em Revisão + 0 Em Homologação + 3 Finalizados = 33 — "
        "exatamente o total reportado pelo agente. Os 3 finalizados correspondem "
        "aos 3 'tarefas_concluidas'; a única issue do tipo 'Ajuste' no Jira foi "
        "corretamente detectada pela Strategy correspondente. Todos esses valores "
        "estão travados em um teste de regressão automatizado "
        "(test_regression_real_jira.py).",
    )

    # Figura 7 — pytest passando
    img_p = insert_paragraph_after(cap_p, align=WD_ALIGN_PARAGRAPH.CENTER)
    img_p.add_run().add_picture(str(GRAFICOS / "08_evidencia_pytest.png"), width=Cm(15.5))
    insert_paragraph_after(
        img_p,
        "Figura 7 — saída real do 'pytest -v': 21 testes passando — 2 do "
        "adapter, 6 cenários de integração (C1–C6) + relatório consolidado, "
        "8 de regressão contra o export real (C7) e 4 das strategies.",
        align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True,
    )

    # 3.6 Análise crítica
    p_an = find_paragraph(doc, "Os resultados confirmam a especificação")
    replace_paragraph_text(p_an, (
        "Os resultados confirmam plenamente a especificação da Entrega 1 em "
        "termos funcionais (todos os 8 indicadores são produzidos) e de "
        "arquitetura (os quatro padrões foram aplicados sem ajustes estruturais). "
        "O custo marginal de adicionar um novo formato de entrada — de .docx para "
        ".csv, quando a UI do Jira descontinuou o export Word — foi de uma única "
        "classe nova (CsvJiraAdapter) sem tocar em Controller, Strategies ou "
        "Factory: evidência prática de que a aplicação do padrão Adapter se pagou "
        "imediatamente na primeira mudança de requisito. A principal descoberta "
        "não funcional veio do dado real: a soma de 'horas estimadas' no board da "
        "Sprint 7 ficou em 0 h, pois o time não preenche o campo 'Estimativa "
        "original' no Jira — o indicador 'horas_estimadas' não só mede como expõe "
        "uma lacuna de processo que impede, hoje, qualquer análise de aderência à "
        "meta de 1.000 h. Como contraprova, o cenário C6 (sintético) demonstra "
        "que o indicador funciona corretamente quando os dados existem (10 × 100 "
        "h = 1.000 h, aderente à meta com desvio 0). Ajustes implementados em "
        "relação ao plano inicial: (i) adoção do Adapter também para o LLM, "
        "criando um NullLLMAdapter que mantém o pipeline determinístico; (ii) "
        "normalização defensiva de status do Jira, aceitando variações com "
        "acento, caixa e sufixos numéricos (ex.: 'Em Revisão 1', 'Em Revisão 2'); "
        "(iii) conversão automática de tempo em segundos (formato do CSV) para "
        "horas decimais, encapsulada no adapter; (iv) convenção explícita no "
        "indicador 'taxa_retrabalho' para o caso de denominador zero (sem "
        "tarefas concluídas no período): a Strategy devolve None e o CSV grava "
        "'N/A' — nunca 0%, que seria enganoso. Esse comportamento é coberto "
        "pelo cenário de borda C5."
    ))


def remover_agentes_2_a_5(doc) -> None:
    """Apaga tudo do Heading 'Agente 2 — ' até (exclusive) '4. Consolidação'."""
    removidos = delete_elements_between(doc, "Agente 2 —", "4. Consolidação")
    print(f"  Removidos {removidos} elementos (agentes 2–5)")


def preencher_consolidacao(doc, metricas: list[dict]) -> None:
    taxa_media = sum(float(m["taxa_acerto_%"]) for m in metricas) / len(metricas)
    tempo_medio_ms = sum(float(m["duracao_seg"]) for m in metricas) / len(metricas) * 1000

    t_cons = doc.tables[-1]
    # Troca "Tempo médio (s)" por "(ms)" PRESERVANDO bold/fonte do cabeçalho
    set_cell_text_keep_format(t_cons.rows[0].cells[3], "Tempo médio (ms)")
    # Preenche a linha 1 com os dados do único agente (valores em ms, consistentes com Tabela 2 e Figura 5)
    set_cell_text(t_cons.rows[1].cells[0], "Agente de Gestão de Projetos")
    set_cell_text(t_cons.rows[1].cells[1], str(len(metricas)))
    set_cell_text(t_cons.rows[1].cells[2], f"{taxa_media:.2f}%")
    set_cell_text(t_cons.rows[1].cells[3], f"{tempo_medio_ms:.2f}")
    # Remove as linhas vazias dos agentes 2–5
    delete_table_rows(t_cons, keep_indices=[0, 1])
    # Ajusta larguras p/ caber na área útil (A4 21cm − margens 3+2 = 16cm)
    set_table_widths_cm(t_cons, [6.5, 2.5, 3.5, 3.5])

    # Substitui o placeholder de gráfico por imagem de consolidação
    replace_placeholder_with_image(
        doc,
        "Insira aqui um gráfico comparativo consolidado",
        GRAFICOS / "05_consolidacao.png",
        caption="Figura 8 — Taxa de sucesso por tipo de cenário (típico, borda, real). Unidade única (%).",
        width_cm=13,
    )


def preencher_demonstracao(doc) -> None:
    p = find_paragraph(doc, "Anexe ou referencie prints de tela")
    replace_paragraph_text(p, (
        "A demonstração pode ser reproduzida localmente a partir do repositório "
        "público do projeto. Comandos:"
    ))
    cmd_p = insert_paragraph_after(p, (
        "git clone https://github.com/LeoLeitao13/aep-agente-gestao-projeto.git\n"
        "cd aep-agente-gestao-projeto\n"
        "python -m venv .venv && source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python main.py tests/fixtures/jira_sprint7_anon.csv --out data/output/indicadores.csv --verbose\n"
        "pytest -v"
    ), size=10)
    cmd_p.paragraph_format.left_indent = Cm(1.0)
    for r in cmd_p.runs:
        r.font.name = "Courier New"

    insert_paragraph_after(cmd_p, (
        "As evidências 'antes' (CSV bruto do Jira) e 'depois' (CSV gerado pelo "
        "agente) estão apresentadas nas Figuras 5 e 6 da seção 3. A Figura 7 "
        "traz a saída real do pytest com os 21 testes passando (2 do adapter, "
        "6 cenários de integração C1–C6 + relatório consolidado, 8 de "
        "regressão contra o export real C7 e 4 das strategies). Qualquer "
        "avaliador pode reproduzir integralmente a demonstração clonando o "
        "repositório público, instalando as dependências e executando os dois "
        "comandos listados acima."
    ))


def preencher_retrospectiva(doc) -> None:
    replace_paragraph_text(
        find_paragraph(doc, "A metodologia definida na Entrega 1"),
        (
            "A metodologia ágil baseada em sprints curtas no Jira foi seguida. "
            "Houve uma adaptação relevante acordada com o professor e a equipe: "
            "o escopo foi reduzido de 5 para 1 agente, priorizando profundidade "
            "(arquitetura correta, testes automatizados e regressão contra dado "
            "real) em lugar de amplitude (5 agentes implementados de forma rasa)."
        ),
    )
    replace_paragraph_text(
        find_paragraph(doc, "Liste práticas que contribuíram"),
        (
            "Uso disciplinado de padrões de projeto desde o primeiro commit (cada "
            "novo indicador é uma Strategy nova, sem tocar em nada mais); "
            "desacoplamento do LLM atrás de um Adapter (permitiu rodar todos os "
            "testes em modo determinístico, sem depender de rede ou chave); "
            "teste de regressão contra o CSV real do Jira (qualquer mudança "
            "futura que altere os números do board é detectada automaticamente); "
            "geração automatizada de .docx sintéticos nos próprios testes, "
            "evitando fixtures binárias desnecessárias."
        ),
    )
    replace_paragraph_text(
        find_paragraph(doc, "Liste rotinas/decisões que geraram atrasos"),
        (
            "No plano da gestão: os integrantes tiveram dificuldade em registrar "
            "as horas trabalhadas de forma consistente no Clockify, o que "
            "limita a precisão do indicador 'horas por integrante' calculado "
            "pelo agente e, no board do Jira, resultou em ausência de "
            "estimativas e apontamentos incompletos. Além disso, o "
            "replanejamento do escopo (redução de 5 para 1 agente) ocorreu "
            "tardiamente, encurtando o tempo disponível para testes e para a "
            "redação do documento final. "
            "No plano técnico: a interface atual do Jira Cloud não oferece "
            "export .docx — exigiu criar um segundo Adapter (CsvJiraAdapter) em "
            "cima do CSV; formatos de hora heterogêneos no Jira (segundos no "
            "CSV, '3h 30m' no .docx) exigiram parsing defensivo; a ausência de "
            "'Estimativa original' preenchida no board zerou o indicador de "
            "horas estimadas no dado real — virou uma oportunidade de melhoria "
            "de processo exposta pelo próprio agente."
        ),
    )
    replace_paragraph_text(
        find_paragraph(doc, "O que a equipe faria diferente"),
        (
            "Em um próximo projeto a equipe (i) acordaria no sprint-zero uma "
            "rotina obrigatória de apontamento diário no Clockify + preenchimento "
            "de estimativas no Jira, com responsável por cobrar — essa "
            "disciplina de gestão é pré-requisito para qualquer indicador de "
            "esforço ter valor; (ii) faria revisão de escopo logo após a "
            "Entrega 1, para evitar replanejamento tardio; (iii) manteria o uso "
            "disciplinado de padrões (Adapter é o de maior retorno em "
            "integrações com sistemas externos — a primeira mudança de formato "
            "já quita o custo inicial); (iv) continuaria separando regras de "
            "negócio (Strategies) de orquestração (Controller), que acelera "
            "muito a criação de novos indicadores; e (v) manteria a prática de "
            "começar por cenários de teste sintéticos e só depois conectar ao "
            "dado real, reduzindo risco de retrabalho."
        ),
    )


def preencher_conclusao(doc) -> None:
    replace_paragraph_text(
        find_paragraph(doc, "Conclua relacionando os resultados"),
        (
            "Os objetivos de aprendizagem da AEP foram atingidos: a equipe aplicou "
            "na prática um estilo arquitetural (Pipe-and-Filter) combinado com "
            "quatro padrões de projeto clássicos (Controller, Factory Method, "
            "Adapter, Strategy), mediu a solução quantitativamente com uma suíte "
            "automatizada e validou-a contra dados reais de uso do Jira. A "
            "escolha pelo aprofundamento em um único agente permitiu demonstrar "
            "não só que o código funciona, mas por quê funciona — explicitando o "
            "papel de cada padrão na resposta a uma mudança real de requisito. "
            "A conexão com a ODS 8 (Trabalho Decente e Crescimento Econômico) "
            "se dá pelo contexto do próprio projeto — 'Escola de TI — SAUF BR' —, "
            "cuja missão é preparar jovens para o mercado de tecnologia, "
            "ampliando o acesso ao trabalho decente e fortalecendo a indústria de "
            "TI nacional. O agente contribui diretamente com essa missão ao "
            "instrumentar a gestão dos projetos formativos: transforma um "
            "artefato bruto (export do board do Jira) em indicadores acionáveis "
            "de produtividade e retrabalho, apoia decisões de coordenação e "
            "expõe lacunas de processo — habilidades diretamente transferíveis a "
            "qualquer ambiente profissional de desenvolvimento de software, "
            "aproximando a formação dos alunos das práticas reais do mercado."
        ),
    )


def preencher_referencias(doc) -> None:
    """Substitui o placeholder por 10 referências ABNT NBR 6023.

    Inserimos TODAS as referências como parágrafos novos (limpos) após o
    placeholder, depois removemos o placeholder — isso evita que a primeira
    referência herde a formatação (p.ex. caixa cinza) do placeholder original
    e deixa todas as entradas visualmente iguais."""
    p = find_paragraph(doc, "Liste as fontes consultadas")
    refs = [
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 6023: informação e documentação: referências: elaboração. Rio de Janeiro: ABNT, 2018.",
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 14724: informação e documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.",
        "GAMMA, Erich; HELM, Richard; JOHNSON, Ralph; VLISSIDES, John. Padrões de projeto: soluções reutilizáveis de software orientado a objetos. Porto Alegre: Bookman, 2000.",
        "LARMAN, Craig. Utilizando UML e padrões: uma introdução à análise e ao projeto orientados a objetos e ao desenvolvimento iterativo. 3. ed. Porto Alegre: Bookman, 2007.",
        "SHAW, Mary; GARLAN, David. Software architecture: perspectives on an emerging discipline. Upper Saddle River: Prentice-Hall, 1996.",
        "SOMMERVILLE, Ian. Engenharia de software. 10. ed. São Paulo: Pearson, 2019.",
        f"ATLASSIAN. Jira Software Cloud: documentation. [S. l.], c2024. Disponível em: https://support.atlassian.com/jira-software-cloud/. Acesso em: {datetime.now().strftime('%d %b. %Y').lower()}.",
        f"PYTEST DEVELOPERS. pytest: helps you write better programs. [S. l.], c2024. Disponível em: https://docs.pytest.org/. Acesso em: {datetime.now().strftime('%d %b. %Y').lower()}.",
        f"PYTHON-DOCX. python-docx documentation. [S. l.], c2024. Disponível em: https://python-docx.readthedocs.io/. Acesso em: {datetime.now().strftime('%d %b. %Y').lower()}.",
        "ORGANIZAÇÃO DAS NAÇÕES UNIDAS. Transformando nosso mundo: a Agenda 2030 para o desenvolvimento sustentável. Nova York: ONU, 2015.",
    ]
    anchor = p
    for ref in refs:
        anchor = insert_paragraph_after(anchor, ref)
    # Remove o placeholder herdado (que trazia caixa cinza / sombreamento)
    p._element.getparent().remove(p._element)


# =====================================================================
# Orquestração
# =====================================================================
def remover_instrucao_5_agentes(doc) -> None:
    """Remove o parágrafo 'Preencha uma seção completa para cada um dos 5 agentes...'
    e o substitui por uma nota de escopo."""
    p = find_paragraph(doc, "Preencha uma seção completa para cada um dos 5 agentes")
    if p:
        replace_paragraph_text(p, (
            "Nota sobre o escopo: na Entrega 1 havia previsão de um ecossistema de "
            "5 agentes; após replanejamento com o professor e a equipe, o escopo "
            "foi concentrado em 1 (um) agente — o Agente de Gestão de Projetos — "
            "com profundidade reforçada em arquitetura, testes e análise crítica. "
            "Esta seção apresenta esse agente de forma completa."
        ))


def aplicar_abnt(doc) -> None:
    """Ajusta papel (A4), margens (3-3-2-2) e fonte padrão (Times New Roman 12pt)
    SEM alterar a estrutura (seções, tabelas, imagens) do modelo original."""
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(3)
        section.left_margin = Cm(3)
        section.bottom_margin = Cm(2)
        section.right_margin = Cm(2)

    # Define font padrão (rPrDefault no styles.xml) para Times New Roman 12pt preto
    styles_el = doc.styles.element
    rpr_default = styles_el.find(qn("w:docDefaults") + "/" + qn("w:rPrDefault"))
    if rpr_default is None:
        docdef = OxmlElement("w:docDefaults")
        styles_el.insert(0, docdef)
        rpr_default = OxmlElement("w:rPrDefault")
        docdef.append(rpr_default)
    rpr = rpr_default.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        rpr_default.append(rpr)
    # fonte
    for tag in ("w:rFonts", "w:sz", "w:szCs", "w:color"):
        for child in rpr.findall(qn(tag)):
            rpr.remove(child)
    rfonts = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), "Times New Roman")
    rpr.append(rfonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "24")   # meio-pontos: 24 = 12pt
    rpr.append(sz)
    szcs = OxmlElement("w:szCs")
    szcs.set(qn("w:val"), "24")
    rpr.append(szcs)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    rpr.append(color)


def build_document() -> Path:
    # Copia o template para a saída e trabalha na cópia (preserva logo, header, etc.)
    shutil.copy(TEMPLATE, OUT)
    doc = Document(str(OUT))

    print("• Aplicando ABNT (A4 + margens 3-3-2-2 + Times New Roman 12pt preto)…")
    aplicar_abnt(doc)

    metricas = load_metricas()
    ind = load_indicadores()

    print("• Preenchendo Identificação…")
    preencher_identificacao(doc)
    print("• Substituindo instrução dos 5 agentes por nota de escopo…")
    remover_instrucao_5_agentes(doc)
    print("• Preenchendo Resumo Executivo…")
    preencher_resumo_executivo(doc)
    print("• Preenchendo Ambiente e Metodologia…")
    preencher_ambiente(doc)
    print("• Preenchendo bloco do Agente 1…")
    preencher_agente_1(doc, metricas, ind)
    print("• Removendo blocos dos Agentes 2 a 5…")
    remover_agentes_2_a_5(doc)
    print("• Preenchendo Consolidação…")
    preencher_consolidacao(doc, metricas)
    print("• Preenchendo Demonstração…")
    preencher_demonstracao(doc)
    print("• Preenchendo Retrospectiva…")
    preencher_retrospectiva(doc)
    print("• Preenchendo Conclusão…")
    preencher_conclusao(doc)
    print("• Preenchendo Referências (ABNT NBR 6023)…")
    preencher_referencias(doc)

    doc.save(str(OUT))
    return OUT


if __name__ == "__main__":
    out = build_document()
    print(f"\n✔ Documento gerado em: {out.relative_to(ROOT)}")
