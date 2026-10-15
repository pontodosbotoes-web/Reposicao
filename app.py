import streamlit as st
import pandas as pd
import hashlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from manual.render_streamlit import render_manual

from src.db import (
    carregar_filiais, carregar_fabricantes,
    carregar_departamentos, carregar_grupos, carregar_subgrupos,
)
from src.base import carregar_base, carregar_transf_em_transito, carregar_transf_recebidas_recentes
from src.transferencia import gerar_sugestoes


st.set_page_config(page_title="Reposição de Produtos", layout="wide", page_icon="📊")


st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
        }
        .titulo-pagina {
            font-size: 1.7rem;
            font-weight: bold;
            text-align: center;
            margin: 0 0 22px 0;
            padding: 6px 0;
            color: #FAFAFA;
            line-height: 1.6;
        }
        .secao-titulo {
            font-size: 1.05rem;
            font-weight: bold;
            padding: 6px 0;
            margin-top: 10px;
            margin-bottom: 6px;
            border-bottom: 2px solid #334155;
        }

        /* Abas centralizadas */
        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.88rem;
            padding: 8px 18px;
        }

        /* Métricas centralizadas */
        [data-testid="stMetric"] {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        [data-testid="stMetricLabel"] {
            display: flex;
            justify-content: center;
            text-align: center;
            width: 100%;
        }
        [data-testid="stMetricLabel"] > div {
            text-align: center;
            width: 100%;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem;
            text-align: center;
            width: 100%;
        }

        /* Botões */
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            width: 100% !important;
            height: 40px !important;
            padding: 4px 2px !important;
            font-size: 1.1rem !important;
            border-radius: 6px !important;
        }

        /* Cabeçalhos das tabelas centralizados */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            justify-content: center !important;
            text-align: center !important;
        }
    </style>
""", unsafe_allow_html=True)


st.markdown('<div class="titulo-pagina">Reposição de Produtos</div>', unsafe_allow_html=True)


PRIO_TXT = {1: "Crítica", 2: "Alta", 3: "Normal"}

try:
    TZ_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    from datetime import timezone, timedelta
    TZ_BR = timezone(timedelta(hours=-3))


def agora_br():
    return datetime.now(TZ_BR)
    
def calcular_janela_analise(opcao: str) -> tuple[date, int]:
    """
    Retorna (data_referencia, max_lookback).
    
    - data_referencia = HOJE (fim da análise)
    - max_lookback = dias para trás a analisar
    """
    hoje = date.today()

    mapa_dias = {
        "1 ano atrás":   365,
        "6 meses atrás": 180,
        "3 meses atrás":  90,
        "2 meses atrás":  60,
        "30 dias atrás":  30,
        "15 dias atrás":  15,
        "7 dias atrás":    7,
    }

    dias = mapa_dias.get(opcao, 365)
    return hoje, dias


# ============================================================
# CARREGAR LISTAS
# ============================================================
filiais = carregar_filiais()
fabricantes = carregar_fabricantes()
departamentos = carregar_departamentos()
grupos = carregar_grupos()
subgrupos = carregar_subgrupos()


# ============================================================
# PERFIS PRÉ-DEFINIDOS
# ============================================================
PERFIS = {
    "Padrão": {
        "opcao_data":       "1 ano atrás",
        "cobertura_opcao":  "Para 30 dias",
        "lead_time":        10,
        "piso":             0,
        "reserva":          25,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    15,
        "dias_transito":    10,
    },
    "Sazonal": {
        "opcao_data":       "30 dias atrás",
        "cobertura_opcao":  "Para 30 dias",
        "lead_time":        10,
        "piso":             3,
        "reserva":          10,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    7,
        "dias_transito":    10,
    },
    "Alto Giro": {
        "opcao_data":       "3 meses atrás",
        "cobertura_opcao":  "Para 15 dias",
        "lead_time":        7,
        "piso":             5,
        "reserva":          15,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    7,
        "dias_transito":    7,
    },
    "Baixo Giro": {
        "opcao_data":       "1 ano atrás",
        "cobertura_opcao":  "Para 30 dias",
        "lead_time":        10,
        "piso":             3,
        "reserva":          30,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    20,
        "dias_transito":    10,
    },
    "Liquidação": {
        "opcao_data":       "6 meses atrás",
        "cobertura_opcao":  "Para 7 dias",
        "lead_time":        10,
        "piso":             0,
        "reserva":          0,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    30,
        "dias_transito":    10,
    },
}


if "show_params" not in st.session_state:
    st.session_state.show_params = False
    
    
if "view" not in st.session_state:
    st.session_state["view"] = "calculadora"

# 👇 NOVO — roteamento ANTES de renderizar a calculadora
if st.session_state["view"] == "manual":
    render_manual()
    st.stop()


# ============================================================
# MAPA DE COBERTURA DE VENDAS (opções → dias)
# ============================================================
COBERTURA_MAP = {
    "Para 7 dias":   7,
    "Para 15 dias": 15,
    "Para 30 dias": 30,
    "Para 2 meses": 60,
    "Para 3 meses": 90,
    "Para 6 meses": 180,
    "Para 1 ano":   365,
}


# ============================================================
# FUNÇÃO QUE APLICA O PERFIL (chamada automaticamente ao mudar)
# ============================================================
def _aplicar_perfil_do_session():
    """Aplica os parâmetros do perfil escolhido no session_state."""
    perfil = st.session_state.get("perfil_sel", "Padrão")
    if perfil in PERFIS:
        for chave, valor in PERFIS[perfil].items():
            st.session_state[chave] = valor
        st.session_state["_ultimo_perfil_aplicado"] = perfil



# ============================================================
# FILTROS (dentro do form) + BOTÕES (fora do form)
# ============================================================
# Linha única: 6 filtros à esquerda + 4 botões-ícone à direita
f0, f1, f2, f3, f4, f5, b1, b2, b3, b4 = st.columns(
    [1.6, 1.9, 1.3, 1.3, 1.3, 1.8, 0.45, 0.45, 0.45, 0.45],
    vertical_alignment="bottom",
)

with f0:
    st.selectbox(
        "Perfil de Análise",
        list(PERFIS.keys()),
        index=0,
        key="perfil_sel",
        help="Escolha um perfil para ajustar os parâmetros automaticamente.",
        on_change=_aplicar_perfil_do_session,
    )

with f1:
    fabricante_sel = st.selectbox("Fabricante", ["(todos)"] + list(fabricantes.keys()), key="fabricante_sel")

with f2:
    depto_sel = st.selectbox("Departamento", ["(todos)"] + list(departamentos.keys()), key="depto_sel")

with f3:
    grupo_sel = st.selectbox("Grupo", ["(todos)"] + list(grupos.keys()), key="grupo_sel")

with f4:
    subgrupo_sel = st.selectbox("Subgrupo", ["(todos)"] + list(subgrupos.keys()), key="subgrupo_sel")

with f5:
    produto_busca = st.text_input(
        "Produto",
        placeholder="Código, ref, descrição ou cód. barras",
        key="produto_busca",
    )

with b1:
    btn_consultar = st.button("🔍", type="primary", use_container_width=True, help="Consultar")
with b2:
    btn_limpar = st.button("🧹", use_container_width=True, help="Limpar filtros")
with b3:
    btn_params = st.button("⚙️", use_container_width=True, help="Parâmetros")
with b4:
    btn_manual = st.button("📖", use_container_width=True, help="Manual do Gestor")

# ============================================================
# APLICA O PERFIL QUANDO MUDA (independente do painel aberto/fechado)
# ============================================================
perfil_atual = st.session_state.get("perfil_sel", "Padrão")
ultimo_perfil_aplicado = st.session_state.get("_ultimo_perfil_aplicado", None)

if perfil_atual != ultimo_perfil_aplicado:
    if perfil_atual in PERFIS:
        for chave, valor in PERFIS[perfil_atual].items():
            st.session_state[chave] = valor
        st.session_state["_ultimo_perfil_aplicado"] = perfil_atual

# ============================================================
# PARÂMETROS
# ============================================================
if btn_params:
    st.session_state.show_params = not st.session_state.show_params

if st.session_state.show_params:
    with st.container(border=True):
        # Linha 1 — JANELA DE ANÁLISE
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1:
            opcao_data = st.selectbox(
                "Período de Análise",
                ["1 ano atrás", "6 meses atrás", "3 meses atrás", "2 meses atrás",
                 "30 dias atrás", "15 dias atrás", "7 dias atrás"],
                index=0,
                key="opcao_data",
            )
        with r1c2:
            filial_sel = st.selectbox(
                "Filial",
                ["(todas)"] + list(filiais.keys()),
                index=0,
                key="filial_param",
            )
        with r1c3:
            cobertura_opcao = st.selectbox(
                "Cobertura de Vendas",
                ["Para 7 dias", "Para 15 dias", "Para 30 dias",
                 "Para 2 meses", "Para 3 meses", "Para 6 meses", "Para 1 ano"],
                index=2,   # padrão = "Para 30 dias"
                key="cobertura_opcao",
            )
        with r1c4:
            lead_time = st.number_input(
                "Tempo de Transporte (dias)",
                0, 30, 10, key="lead_time",
            )

        # Linha 2 — PROTEÇÃO DAS ORIGENS
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1:
            piso = st.number_input("Piso Exposição (un)", 0, 50, 0, key="piso")
        with r2c2:
            reserva = st.number_input("Reserva Origem (%)", 0, 100, 25, key="reserva")
        with r2c3:
            atacado_piso = st.selectbox("Atacado tem Piso?", ["Não", "Sim"], index=0, key="atacado_piso")
        with r2c4:
            atacado_reserva = st.selectbox("Atacado tem Reserva?", ["Não", "Sim"], index=0, key="atacado_reserva")

        # Linha 3 — TRAVAS DE SEGURANÇA
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            anti_gangorra = st.number_input("Reposição Recente (dias)", 0, 90, 15, key="anti_gangorra")
        with r3c2:
            dias_transito = st.number_input("Dias em Trânsito", 1, 60, 10, key="dias_transito")
else:
    # Valores padrão quando o painel está fechado
    perfil_sel = st.session_state.get("perfil_sel", "Padrão")
    opcao_data = st.session_state.get("opcao_data", "1 ano atrás")
    filial_sel = st.session_state.get("filial_param", "(todas)")
    cobertura_opcao = st.session_state.get("cobertura_opcao", "Para 30 dias")
    lead_time = st.session_state.get("lead_time", 10)
    piso = st.session_state.get("piso", 0)
    reserva = st.session_state.get("reserva", 25)
    atacado_piso = st.session_state.get("atacado_piso", "Não")
    atacado_reserva = st.session_state.get("atacado_reserva", "Não")
    anti_gangorra = st.session_state.get("anti_gangorra", 15)
    dias_transito = st.session_state.get("dias_transito", 10)


# ============================================================
# DERIVAÇÕES (com base nos parâmetros)
# ============================================================
cobertura = COBERTURA_MAP.get(cobertura_opcao, 30)
data_ref, lookback = calcular_janela_analise(opcao_data)


# ============================================================
# LIMPAR
# ============================================================
if btn_limpar:
    for k in [
        "df_base", "df_transf", "df_base_n", "produto_busca",
        "perfil_sel",
        "_ultimo_perfil_aplicado",       # ← nova
        "opcao_data", "filial_param", "cobertura_opcao",
        "lead_time", "piso", "reserva",
        "atacado_piso", "atacado_reserva",
        "anti_gangorra", "dias_transito",
        "fabricante_sel", "depto_sel", "grupo_sel", "subgrupo_sel",
    ]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ============================================================
# PDF
# ============================================================
class HeaderFooterCanvas(canvas.Canvas):
    """Desenha cabeçalho e rodapé em todas as páginas."""

    def __init__(self, *args, **kwargs):
        self.titulo = kwargs.pop("titulo", "Relatorio de Transferencias")
        self.gerado_em = kwargs.pop("gerado_em", "")
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        w, h = landscape(A4)  # largura, altura (842 x 595)

        # ---------- CABEÇALHO ----------
        self.setFont("Helvetica-Bold", 10)
        self.setFillColor(colors.HexColor("#1E293B"))
        self.drawString(15, h - 22, self.titulo)

        # Linha divisória
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(15, h - 28, w - 15, h - 28)

        # ---------- RODAPÉ ----------
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Esquerda: Gerado em
        self.drawString(15, 12, f"Gerado em {self.gerado_em}")

        # Centro: Página X de Y
        self.drawCentredString(w / 2, 12, f"Página {self._pageNumber} de {page_count}")

def gerar_pdf_filial(nome_filial, cod, df):
    """Gera PDF de UMA filial com cabeçalho/rodapé em todas as páginas."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=15, leftMargin=15,
        topMargin=35, bottomMargin=25,  # espaço p/ header/footer
    )
    elements = []
    styles = getSampleStyleSheet()

    page_w = landscape(A4)[0] - 30

    filial_style = ParagraphStyle('F', parent=styles['Heading2'], fontSize=11, leading=13,
                                  textColor=colors.HexColor('#1E293B'), spaceBefore=0, spaceAfter=6)
    cell_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=7, leading=9, alignment=0)
    cell_center = ParagraphStyle('CC', parent=styles['Normal'], fontSize=7, leading=9, alignment=1)
    cell_right = ParagraphStyle('CR', parent=styles['Normal'], fontSize=7, leading=9, alignment=2)
    header_style = ParagraphStyle('H', parent=styles['Normal'], fontSize=7, leading=9,
                                  fontName='Helvetica-Bold', textColor=colors.white, alignment=1)

    def _build(df_part, tipo):
        if df_part.empty:
            return Paragraph("<i>Nenhum item.</i>", cell_style)

        if tipo == "ENV":
            heads = ["#", "Pr.", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Reserva", "Ideal", "Motivo"]
            widths = [22, 42, 50, 240, 35, 130, 60, 40, 42, 40, 110]
            mapper = lambda r: [
                (r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"),
                (r["Produto"], "L"),
                (r["Embalagem"], "C"), (r["Fabricante"], "L"),
                (r["NomeFilialDestino"], "C"),
                (int(r["QtdTransferir"]), "R"),
                (int(r["ReservaOrigem"]), "R"),
                (int(r["Qtd Ideal"]), "R"),
                (r["Motivo"], "L"),
            ]
        else:
            heads = ["#", "Pr.", "Cod", "Produto", "Emb.", "Fabricante", "Origem", "Qtd", "Dias", "Ideal", "Motivo"]
            widths = [22, 42, 50, 240, 35, 130, 60, 40, 42, 40, 110]
            mapper = lambda r: [
                (r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"),
                (r["Produto"], "L"),
                (r["Embalagem"], "C"), (r["Fabricante"], "L"),
                (r["NomeFilialOrigem"], "C"),
                (int(r["QtdTransferir"]), "R"),
                (int(r["DiasAteZerarDestino"]) if pd.notna(r["DiasAteZerarDestino"]) else 0, "R"),
                (int(r["Qtd Ideal"]), "R"),
                (r["Motivo"], "L"),
            ]

        data = [[Paragraph(h, header_style) for h in heads]]
        for _, row in df_part.iterrows():
            vals = []
            for v, align in mapper(row):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    v = ""
                elif isinstance(v, float) and v.is_integer():
                    v = int(v)
                if align == "R":
                    stl = cell_right
                elif align == "C":
                    stl = cell_center
                else:
                    stl = cell_style
                vals.append(Paragraph(str(v), stl))
            data.append(vals)

        t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        return t

    # Filtra filial
    df_env = df[df["CodigoFilialOrigem"] == cod].copy()
    df_rec = df[df["CodigoFilialDestino"] == cod].copy()

    if df_env.empty and df_rec.empty:
        elements.append(Paragraph(f"<b>Sem movimentações para {nome_filial.title()}</b>", filial_style))
        agora = agora_br()
        titulo_cab = f"Relatorio de Reposicao - {nome_filial.title()}"
        doc.build(
            elements,
            canvasmaker=lambda *a, **kw: HeaderFooterCanvas(
                *a, titulo=titulo_cab,
                gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), **kw
            ),
        )
        buffer.seek(0)
        return buffer, agora

    # ENVIAR
    df_env = df_env.reset_index(drop=True)
    df_env.insert(0, "#", range(1, len(df_env) + 1))
    # Regra: Atacado mostra IdealDestino; Lojas mostram IdealOrigem
    df_env["Qtd Ideal"] = df_env["IdealDestino"] if cod == 5 else df_env["IdealOrigem"]
    df_env["Prioridade"] = df_env["Prioridade"].map(PRIO_TXT).fillna("-")
    elements.append(Paragraph("<b>ENVIAR</b>", filial_style))
    elements.append(_build(df_env, "ENV"))
    elements.append(Spacer(1, 14))

    # RECEBER
    df_rec = df_rec.reset_index(drop=True)
    df_rec.insert(0, "#", range(1, len(df_rec) + 1))
    # Sempre IdealDestino (a loja é o destino)
    df_rec["Qtd Ideal"] = df_rec["IdealDestino"]
    df_rec["Prioridade"] = df_rec["Prioridade"].map(PRIO_TXT).fillna("-")
    elements.append(Paragraph("<b>RECEBER</b>", filial_style))
    elements.append(_build(df_rec, "REC"))

    # Gera
    agora = agora_br()
    titulo_cab = f"Relatorio de Reposicao - {nome_filial.title()}"
    doc.build(
        elements,
        canvasmaker=lambda *a, **kw: HeaderFooterCanvas(
            *a, titulo=titulo_cab,
            gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), **kw
        ),
    )
    buffer.seek(0)
    return buffer, agora

# ============================================================
# CONSULTAR
# ============================================================
if btn_consultar:
    # Regra: se o campo Produto estiver preenchido, ele é EXCLUSIVO.
    # Todos os filtros (Fabricante, Departamento, Grupo, Subgrupo e Filial)
    # são ignorados. Apenas o Perfil de Análise continua sendo aplicado.
    produto_preenchido = bool(produto_busca and produto_busca.strip())

    if produto_preenchido:
        fabricante_filtro   = ""
        departamento_filtro = ""
        grupo_filtro        = ""
        subgrupo_filtro     = ""
        filial_filtro       = ""
    else:
        fabricante_filtro   = "" if fabricante_sel == "(todos)" else fabricantes[fabricante_sel]
        departamento_filtro = "" if depto_sel == "(todos)" else departamentos[depto_sel]
        grupo_filtro        = "" if grupo_sel == "(todos)" else grupos[grupo_sel]
        subgrupo_filtro     = "" if subgrupo_sel == "(todos)" else subgrupos[subgrupo_sel]
        filial_filtro       = "" if filial_sel == "(todas)" else filiais[filial_sel]

    # Validação: precisa ter produto digitado OU pelo menos 1 filtro
    if (not produto_preenchido and not fabricante_filtro
        and not departamento_filtro and not grupo_filtro
        and not subgrupo_filtro and not filial_filtro):
        st.warning("⚠️ Digite um produto ou escolha pelo menos 1 filtro.")
    else:
        try:
            with st.spinner("⏳ Construindo Base..."):
                df_base = carregar_base(
                    data_referencia=data_ref.strftime("%Y-%m-%d"),
                    max_lookback=lookback,
                    fabricante=fabricante_filtro,
                    departamento=departamento_filtro,
                    grupo=grupo_filtro,
                    subgrupo=subgrupo_filtro,
                    filial=filial_filtro,
                    produto=produto_busca,
                )
                st.session_state["df_base"] = df_base


# ============================================================
# RESULTADO
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]

    if df.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        nomes = ["ATACADO", "ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE"]
        codigos = {"ATACADO": 5, "ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4}

        tabs = st.tabs(nomes)
        for tab, nome in zip(tabs, nomes):
            cod = codigos[nome]
            with tab:
                df_env = df[df["CodigoFilialOrigem"] == cod].copy().reset_index(drop=True)
                df_rec = df[df["CodigoFilialDestino"] == cod].copy().reset_index(drop=True)

                # ---- MÉTRICAS + BOTÃO PDF NA MESMA LINHA ----
                m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1, 1.2])
                m1.metric("📤 Enviar (itens)", len(df_env))
                m2.metric("📤 Enviar (un)", int(df_env["QtdTransferir"].sum()) if not df_env.empty else 0)
                m3.metric("📥 Receber (itens)", len(df_rec))
                m4.metric("📥 Receber (un)", int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0)

                with m5:
                    st.write("")
                    # Chave estável: filial + impressão digital do conteúdo real
                    _h = hashlib.md5(
                        pd.util.hash_pandas_object(df, index=True).values.tobytes()
                    ).hexdigest()[:10]
                    cache_key = f"pdf_cache_{cod}_{_h}"

                    if cache_key not in st.session_state:
                        try:
                            pdf_bytes, agora = gerar_pdf_filial(nome, cod, df)
                            st.session_state[cache_key] = (pdf_bytes, agora)
                        except Exception:
                            st.session_state[cache_key] = (None, None)
                    
                    pdf_bytes, agora = st.session_state[cache_key]
                    
                    if pdf_bytes is not None:
                        nome_file = nome.title().replace(" ", "")
                        file_name = f"Reposicao {nome_file} {agora.strftime('%Y%m%d %H%M%S')}.pdf"
                        st.download_button(
                            "📄 Gerar PDF",
                            data=pdf_bytes,
                            file_name=file_name,
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"pdf_{cod}",
                        )
                    else:
                        st.button("📄 Gerar PDF", disabled=True, use_container_width=True)

                # ---- ENVIAR ----
                st.markdown('<div class="secao-titulo">📤 ENVIAR</div>', unsafe_allow_html=True)
                if df_env.empty:
                    st.caption("Nada a enviar")
                else:
                    dfe = df_env.copy()
                    dfe.insert(0, "#", range(1, len(dfe) + 1))
                    dfe["Qtd Ideal"] = dfe["IdealDestino"] if cod == 5 else dfe["IdealOrigem"]
                    dfe["Prioridade"] = dfe["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfe = dfe[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante",
                               "NomeFilialDestino", "QtdTransferir",
                               "ReservaOrigem", "Qtd Ideal", "Motivo"]]
                    dfe.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante",
                                   "Destino", "Qtd Transf.", "Reserva", "Qtd Ideal", "Motivo"]

                    styler_e = dfe.style.set_properties(
                        subset=["Qtd Transf.", "Reserva", "Qtd Ideal"],
                        **{"text-align": "right"}
                    )

                    h = min(420, max(120, len(dfe) * 36 + 42))
                    st.dataframe(styler_e, use_container_width=True, hide_index=True, height=h)

                # ---- RECEBER ----
                st.markdown('<div class="secao-titulo">📥 RECEBER</div>', unsafe_allow_html=True)
                if df_rec.empty:
                    st.caption("Nada a receber")
                else:
                    dfr = df_rec.copy()
                    dfr.insert(0, "#", range(1, len(dfr) + 1))
                    dfr["Qtd Ideal"] = dfr["IdealDestino"]
                    dfr["Prioridade"] = dfr["Prioridade"].map(PRIO_TXT).fillna("-")
                    # Trata None → "-" e converte para inteiro quando houver valor
                    dfr["Dias p/ Zerar"] = dfr["DiasAteZerarDestino"].apply(
                        lambda x: 0 if pd.isna(x) or x is None else int(x)
                    ).astype(int)

                    dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante",
                               "NomeFilialOrigem", "QtdTransferir",
                               "Dias p/ Zerar", "Qtd Ideal", "Motivo"]]
                    dfr.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante",
                                   "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]

                    h = min(420, max(120, len(dfr) * 36 + 42))
                    st.dataframe(dfr, use_container_width=True, hide_index=True, height=h)
                    


if btn_manual:
    st.session_state["view"] = "manual"
    st.rerun()