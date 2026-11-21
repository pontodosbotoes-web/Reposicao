import streamlit as st
import pandas as pd
import hashlib
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from manual.render_streamlit import render_manual
import streamlit.components.v1 as components

from src.db import (
    carregar_filiais, carregar_fabricantes,
    carregar_departamentos, carregar_grupos, carregar_subgrupos,
)
from src.base import carregar_base, carregar_transf_em_transito, carregar_transf_recebidas_recentes, carregar_compras_recentes
from src.transferencia import gerar_sugestoes


st.set_page_config(page_title="Reposição de Produtos", layout="wide", page_icon="📊")


st.markdown("""
<style>
    :root {
        --ops-bg: #0b1220;
        --ops-panel: #111c2e;
        --ops-panel-2: #162338;
        --ops-border: rgba(148, 163, 184, .18);
        --ops-text: #e5edf7;
        --ops-muted: #91a2b8;
        --ops-accent: #38bdf8;
        --ops-success: #34d399;
        --ops-warning: #fbbf24;
        --ops-danger: #fb7185;
    }
    #MainMenu, footer, .stAppDeployButton { visibility: hidden; }
    header { height: 0; }
    .stApp { background: var(--ops-bg); }
    .block-container {
        max-width: 1680px !important;
        padding: 1.25rem 2rem 3rem !important;
    }
    .ops-header {
        display:flex; align-items:center; justify-content:space-between; gap:1rem;
        padding: 1.1rem 1.35rem; margin: 0 0 1.1rem 0;
        border:1px solid var(--ops-border); border-radius:14px;
        background:linear-gradient(115deg, #14243a 0%, #101a2b 70%, #102b40 100%);
    }
    .ops-kicker { color:var(--ops-accent); font-size:.72rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
    .ops-title { color:var(--ops-text); font-size:1.65rem; line-height:1.2; font-weight:800; margin:.15rem 0 .25rem; }
    .ops-subtitle { color:var(--ops-muted); font-size:.86rem; }
    .ops-header-mark { font-size:2rem; opacity:.9; padding: .3rem .65rem; }
    .section-heading {
        display:flex; align-items:center; gap:.55rem; margin:.6rem 0 .7rem;
        color:var(--ops-text); font-size:1rem; font-weight:750;
    }
    .section-note { color:var(--ops-muted); font-size:.78rem; margin-top:-.35rem; margin-bottom:.8rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--ops-border); border-radius:12px; }
    div[data-testid="stMetric"] {
        background:var(--ops-panel); border:1px solid var(--ops-border);
        border-radius:11px; padding:.75rem .9rem;
    }
    div[data-testid="stMetricLabel"] { color:var(--ops-muted); font-size:.78rem; }
    div[data-testid="stMetricValue"] { color:var(--ops-text); font-weight:800; }
    .metric-grid {
        display:grid; grid-template-columns:repeat(auto-fit, minmax(145px, 1fr));
        gap:.65rem; margin:.8rem 0 1.1rem;
    }
    .metric-card {
        background:linear-gradient(145deg, var(--ops-panel), var(--ops-panel-2));
        border:1px solid var(--ops-border); border-radius:11px; padding:.8rem .7rem;
        min-width:0;
    }
    .metric-card-title { color:var(--ops-text); font-size:.8rem; font-weight:800; text-align:center; padding-bottom:.45rem; border-bottom:1px solid var(--ops-border); }
    .metric-card-row, .metric-card-values { display:flex; justify-content:space-around; gap:.5rem; }
    .metric-card-row { color:var(--ops-muted); font-size:.7rem; margin-top:.55rem; }
    .metric-card-values { color:var(--ops-text); font-size:1.2rem; font-weight:850; margin-top:.12rem; }
    .stTabs [data-baseweb="tab-list"] { gap:.35rem; border-bottom:1px solid var(--ops-border); }
    .stTabs [data-baseweb="tab"] { padding:.65rem 1rem; font-weight:650; }
    .stTabs [aria-selected="true"] { color:var(--ops-accent) !important; }
    div[data-testid="stDataFrame"] { border:1px solid var(--ops-border); border-radius:10px; overflow:hidden; }
    div[data-testid="stDataFrame"] div[role="columnheader"] { justify-content:center !important; text-align:center !important; }
    div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
        min-height:2.55rem; border-radius:9px; font-weight:700; transition:all .15s ease;
    }
    .st-key-btn_consultar button { background:#0284c7 !important; color:white !important; border:1px solid #0ea5e9 !important; }
    .st-key-btn_consultar button:hover { background:#0369a1 !important; }
    .st-key-btn_limpar button { background:transparent !important; color:#fda4af !important; border:1px solid #9f1239 !important; }
    .st-key-btn_parametros button { background:#1e293b !important; color:#dbeafe !important; border:1px solid #475569 !important; }
    .st-key-btn_manual button { background:#123b38 !important; color:#a7f3d0 !important; border:1px solid #047857 !important; }
    .st-key-btn_pdf button { background:#713f12 !important; color:#fde68a !important; border:1px solid #a16207 !important; }
    .st-key_btn_download_pdf button { background:#155e75 !important; color:white !important; }
    .rodape { position:fixed; bottom:8px; right:14px; font-size:.7rem; color:#64748b; z-index:1000; }
    @media (max-width: 900px) {
        .block-container { padding: .8rem .8rem 3rem !important; }
        .ops-title { font-size:1.35rem; }
        .ops-header { padding:.9rem; }
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="ops-header">
  <div>
    <div class="ops-kicker">Painel operacional · Abastecimento</div>
    <div class="ops-title">Reposição de Produtos</div>
    <div class="ops-subtitle">Central de análise, transferência entre filiais e planejamento de compras</div>
  </div>
  <div class="ops-header-mark">📦</div>
</div>
""", unsafe_allow_html=True)


PRIO_TXT = {1: "CRÍTICA", 2: "ALTA", 3: "NORMAL"}
codigos_filial = {"ATACADO": 5, "ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4}
icones_filial = {"ATACADO": "🏢", "ALECRIM": "🌿", "VIA DIRETA": "🚗", "ZONA SUL": "🏖️", "ZONA NORTE": "🏔️"}

try:
    TZ_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    from datetime import timezone, timedelta
    TZ_BR = timezone(timedelta(hours=-3))


def agora_br():
    return datetime.now(TZ_BR)
    
def calcular_janela_analise(opcao: str) -> tuple[date, int]:
    hoje = date.today()
    mapa_dias = {
        "1 ano atrás": 365, "6 meses atrás": 180, "3 meses atrás": 90,
        "2 meses atrás": 60, "30 dias atrás": 30, "15 dias atrás": 15, "7 dias atrás": 7,
    }
    return hoje, mapa_dias.get(opcao, 365)


# ============================================================
# CARREGAR LISTAS E PERFIS
# ============================================================
filiais = carregar_filiais()
fabricantes = carregar_fabricantes()
departamentos = carregar_departamentos()
grupos = carregar_grupos()
subgrupos = carregar_subgrupos()

# Valores padrão (antigo Perfil Padrão)
DEFAULTS = {
    "opcao_data": "1 ano atrás",
    "cobertura_opcao": "Para 30 dias",
    "lead_time": 10,
    "piso": 0,
    "reserva": 25,
    "atacado_piso": "Não",
    "atacado_reserva": "Não",
    "atacado_min_compra": "Não",
    "anti_gangorra": 15,
    "dias_transito": 10,
    "dias_compra": 30,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

compras_recentes = carregar_compras_recentes(st.session_state.get("dias_compra", 30))

if "show_params" not in st.session_state: st.session_state.show_params = False
if "view" not in st.session_state: st.session_state["view"] = "calculadora"

if st.session_state["view"] == "manual":
    render_manual()
    st.stop()

# ============================================================
# INICIALIZAÇÃO E SINCRONIA DE ESTADO
# ============================================================
if "fabricante_sel" not in st.session_state: st.session_state["fabricante_sel"] = "(todos)"
if "depto_sel" not in st.session_state: st.session_state["depto_sel"] = "(todos)"
if "grupo_sel" not in st.session_state: st.session_state["grupo_sel"] = "(todos)"
if "subgrupo_sel" not in st.session_state: st.session_state["subgrupo_sel"] = "(todos)"
if "produto_busca" not in st.session_state: st.session_state["produto_busca"] = ""
if "filial_param" not in st.session_state: st.session_state["filial_param"] = "(todas)"
if "nf_sel" not in st.session_state: st.session_state["nf_sel"] = "Nenhuma"

# ============================================================
# CALLBACKS
# ============================================================
def _limpar_filtros():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    
    st.session_state["fabricante_sel"] = "(todos)"
    st.session_state["depto_sel"] = "(todos)"
    st.session_state["grupo_sel"] = "(todos)"
    st.session_state["subgrupo_sel"] = "(todos)"
    st.session_state["produto_busca"] = ""
    st.session_state["filial_param"] = "(todas)"
    st.session_state["nf_num"] = None
    if "busca_compra" in st.session_state: st.session_state["busca_compra"] = ""
    
    for _k in ("df_base", "df_transf", "df_compras", "df_demonstracao", "df_base_n", "pdf_bytes_global", "filial_pdf_sel"):
        if _k in st.session_state: del st.session_state[_k]

if "nf_num" not in st.session_state: st.session_state["nf_num"] = None
bloqueado = st.session_state.get("nf_num") is not None

# ============================================================
# FILTROS OPERACIONAIS
# ============================================================
lista_periodo = ["1 ano atrás", "6 meses atrás", "3 meses atrás", "2 meses atrás", "30 dias atrás", "15 dias atrás", "7 dias atrás"]
idx_p = lista_periodo.index(st.session_state.get("opcao_data", "1 ano atrás")) if st.session_state.get("opcao_data") in lista_periodo else 0

with st.container(border=True):
    st.markdown('<div class="section-heading">⌕ Critérios da consulta</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Use os filtros para delimitar a análise. A busca por produto tem precedência sobre os demais filtros.</div>', unsafe_allow_html=True)
    f_periodo, f_fab, f_depto, f_grupo, f_sub, f_prod = st.columns([1.25, 1.45, 1.05, 1.05, 1.05, 1.55], vertical_alignment="bottom")
    with f_periodo:
        st.selectbox("Período de análise", lista_periodo, index=idx_p, key="opcao_data", disabled=bloqueado)
    with f_fab:
        fabricante_sel = st.selectbox("Fabricante", ["(todos)"] + list(fabricantes.keys()), key="fabricante_sel", disabled=bloqueado)
    with f_depto:
        depto_sel = st.selectbox("Departamento", ["(todos)"] + list(departamentos.keys()), key="depto_sel", disabled=bloqueado)
    with f_grupo:
        grupo_sel = st.selectbox("Grupo", ["(todos)"] + list(grupos.keys()), key="grupo_sel", disabled=bloqueado)
    with f_sub:
        subgrupo_sel = st.selectbox("Subgrupo", ["(todos)"] + list(subgrupos.keys()), key="subgrupo_sel", disabled=bloqueado)
    with f_prod:
        produto_busca = st.text_input("Produto", placeholder="Ex.: CAIXA QUADRADA (E)", key="produto_busca", disabled=bloqueado,
            help="Busca por produto com E / OU. Se preenchido, ignora os outros filtros.")

# ============================================================
# LINHA 2: BOTÕES
# ============================================================
st.write("")
st.markdown('<div class="section-heading">⚡ Ações</div>', unsafe_allow_html=True)
b1, b2, b3, b4, b5, b6 = st.columns([1.05, .85, 1.05, 1.25, 1.45, 1.15], vertical_alignment="bottom")

if "nf_num" not in st.session_state: st.session_state["nf_num"] = None

# ============================================================
# COMPRAS RECENTES / CONTEXTO DE NF
# ============================================================
if not compras_recentes.empty:
    with st.expander("📦 Compras recentes · selecionar uma NF", expanded=False):
        if st.session_state.get("nf_num"):
            c_msg, c_clear = st.columns([5, 1])
            with c_msg:
                st.success(f"Compra selecionada: NF {st.session_state['nf_num']}")
            with c_clear:
                if st.button("Limpar NF", use_container_width=True, key="btn_limpar_nf_top"):
                    st.session_state["nf_num"] = None
                    st.rerun()

        compras_view = compras_recentes.copy()
        compras_view["DataFormatada"] = pd.to_datetime(compras_view["DataCompra"]).dt.strftime("%d/%m/%Y")
        agrupado = compras_view.groupby("NumeroNF").agg({
            "DataCompra": "first", "DataFormatada": "first", "NomeFornecedor": "first",
            "Filial": "first", "CodigoProduto": "count",
            "Fabricante": lambda x: ", ".join(sorted(x.dropna().unique())),
        }).reset_index()
        agrupado = agrupado.sort_values(["DataCompra", "NomeFornecedor", "NumeroNF"],
            ascending=[False, True, True]).reset_index(drop=True)

        c_search, c_hint = st.columns([2, 3])
        with c_search:
            busca_compra = st.text_input("Buscar compra", placeholder="Fornecedor, fabricante ou NF", key="busca_compra")
        with c_hint:
            st.caption("Selecione uma linha para contextualizar a análise com os itens da nota.")
        if busca_compra:
            mask = (
                agrupado["NomeFornecedor"].str.contains(busca_compra, case=False, na=False) |
                agrupado["Fabricante"].str.contains(busca_compra, case=False, na=False) |
                agrupado["NumeroNF"].astype(str).str.contains(busca_compra, case=False, na=False)
            )
            agrupado = agrupado[mask]
        if agrupado.empty:
            st.info("Nenhuma compra encontrada com os filtros atuais.")
        else:
            df_display = agrupado[["Filial", "DataFormatada", "NomeFornecedor", "NumeroNF", "CodigoProduto", "Fabricante"]].copy()
            df_display.columns = ["FILIAL", "DATA", "FORNECEDOR", "NF", "ITENS", "FABRICANTES"]
            event = st.dataframe(df_display, use_container_width=True, hide_index=True, on_select="rerun",
                selection_mode="single-row", height=min(280, max(130, len(df_display) * 35 + 40)))
            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_nf = str(df_display.iloc[selected_idx]["NF"])
                if st.session_state.get("nf_num") != selected_nf:
                    st.session_state["nf_num"] = selected_nf
                    st.session_state["auto_consultar"] = True  # <-- GATILHO
                    st.rerun()

with b1: btn_consultar = st.button("🔍 Consultar", use_container_width=True, key="btn_consultar")
with b2: st.button("🧹 Limpar", use_container_width=True, on_click=_limpar_filtros, key="btn_limpar")
with b3: btn_params = st.button("⚙️ Parâmetros", use_container_width=True, key="btn_parametros")
with b4: btn_manual = st.button("📖 Manual do Gestor", use_container_width=True, key="btn_manual")

with b5:
    filial_pdf = st.selectbox(
        "Filial p/ PDF", 
        ["ATACADO", "ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE"], 
        index=None, placeholder="Selecione a Filial p/ PDF...",
        label_visibility="collapsed", key="filial_pdf_sel"
    )
    
with b6:
    btn_pdf_global = st.button("📄 Gerar PDF", use_container_width=True, disabled=(filial_pdf is None), key="btn_pdf")

if produto_busca and produto_busca.strip() and not bloqueado:
    st.markdown(
        '<div style="background-color: rgba(59,130,246,0.12); border-left: 3px solid #3B82F6; padding: 6px 12px; margin-top: 8px; border-radius: 4px; font-size: 0.85rem; color: #93C5FD;">'
        'ℹ️ <b>Busca por produto:</b> Fabricante, Departamento, Grupo, Subgrupo e Filial serão ignorados.'
        '</div>', unsafe_allow_html=True,
    )

# ============================================================
# PARÂMETROS
# ============================================================
if btn_params: st.session_state.show_params = not st.session_state.show_params

if st.session_state.show_params:
    with st.container(border=True):
        st.markdown('<div class="section-heading">⚙️ Configuração do planejamento</div>', unsafe_allow_html=True)
        st.caption("Parâmetros visuais e operacionais da consulta. As regras de cálculo permanecem no motor existente.")
        st.markdown("**Escopo e horizonte**")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        
        with r1c1: 
            lista_filial = ["(todas)"] + list(filiais.keys())
            idx_f = lista_filial.index(st.session_state.get("filial_param", "(todas)")) if st.session_state.get("filial_param") in lista_filial else 0
            v_filial = st.selectbox("Filial", lista_filial, index=idx_f, help="Apenas visual: o motor sempre analisa todas as filiais.", disabled=bloqueado)
            st.session_state["filial_param"] = v_filial
            
        with r1c2: 
            lista_cob = ["Para 7 dias", "Para 15 dias", "Para 30 dias", "Para 2 meses", "Para 3 meses", "Para 6 meses", "Para 1 ano"]
            idx_c = lista_cob.index(st.session_state.get("cobertura_opcao", "Para 30 dias")) if st.session_state.get("cobertura_opcao") in lista_cob else 2
            v_cob = st.selectbox("Cobertura de Vendas", lista_cob, index=idx_c, disabled=bloqueado)
            st.session_state["cobertura_opcao"] = v_cob
            
        with r1c3: 
            v_lead = st.number_input("Tempo de Transporte (dias)", 0, 30, value=int(st.session_state.get("lead_time", 10)), disabled=bloqueado)
            st.session_state["lead_time"] = v_lead
            
        with r1c4:
            v_dc = st.number_input("Período de Compras (dias)", 1, 90, value=int(st.session_state.get("dias_compra", 30)), disabled=bloqueado)
            st.session_state["dias_compra"] = v_dc

        st.markdown("**Política de estoque**")
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        
        with r2c1: 
            v_piso = st.number_input("Piso Exposição (un)", 0, 50, value=int(st.session_state.get("piso", 0)), disabled=bloqueado)
            st.session_state["piso"] = v_piso
            
        with r2c2: 
            v_reserva = st.number_input("Reserva Origem (%)", 0, 100, value=int(st.session_state.get("reserva", 25)), disabled=bloqueado)
            st.session_state["reserva"] = v_reserva
            
        with r2c3: 
            lista_sn = ["Não", "Sim"]
            idx_ap = lista_sn.index(st.session_state.get("atacado_piso", "Não")) if st.session_state.get("atacado_piso") in lista_sn else 0
            v_ap = st.selectbox("Atacado tem Piso?", lista_sn, index=idx_ap, disabled=bloqueado)
            st.session_state["atacado_piso"] = v_ap
            
        with r2c4: 
            idx_ar = lista_sn.index(st.session_state.get("atacado_reserva", "Não")) if st.session_state.get("atacado_reserva") in lista_sn else 0
            v_ar = st.selectbox("Atacado tem Reserva?", lista_sn, index=idx_ar, disabled=bloqueado)
            st.session_state["atacado_reserva"] = v_ar

        st.markdown("**Trânsito e proteção contra reposição repetida**")
        r3c1, r3c2, r3c3 = st.columns(3)
        
        with r3c1: 
            v_ag = st.number_input("Reposição Recente (dias)", 0, 90, value=int(st.session_state.get("anti_gangorra", 15)), disabled=bloqueado)
            st.session_state["anti_gangorra"] = v_ag
            
        with r3c2: 
            v_dt = st.number_input("Dias em Trânsito", 1, 60, value=int(st.session_state.get("dias_transito", 10)), disabled=bloqueado)
            st.session_state["dias_transito"] = v_dt
            
        with r3c3: 
            idx_am = lista_sn.index(st.session_state.get("atacado_min_compra", "Não")) if st.session_state.get("atacado_min_compra") in lista_sn else 0
            v_am = st.selectbox("Atacado tem Mínimo p/ Compra?", lista_sn, index=idx_am, help="Se Sim, usa o valor do Piso Exposição como quantidade mínima para sugerir compra.", disabled=bloqueado)
            st.session_state["atacado_min_compra"] = v_am

# Recupera os valores
opcao_data = st.session_state["opcao_data"]
filial_sel = st.session_state["filial_param"]
cobertura_opcao = st.session_state["cobertura_opcao"]
lead_time = st.session_state["lead_time"]
piso = st.session_state["piso"]
reserva = st.session_state["reserva"]
atacado_piso = st.session_state["atacado_piso"]
atacado_reserva = st.session_state["atacado_reserva"]
anti_gangorra = st.session_state["anti_gangorra"]
dias_transito = st.session_state["dias_transito"]
atacado_min_compra = st.session_state["atacado_min_compra"]

cobertura = {"Para 7 dias": 7, "Para 15 dias": 15, "Para 30 dias": 30, "Para 2 meses": 60, "Para 3 meses": 90, "Para 6 meses": 180, "Para 1 ano": 365}.get(cobertura_opcao, 30)
data_ref, lookback = calcular_janela_analise(opcao_data)

# ============================================================
# FUNÇÃO GERADORA DE PDF
# ============================================================
class HeaderFooterCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self.titulo = kwargs.pop("titulo", "Relatorio de Transferencias")
        self.gerado_em = kwargs.pop("gerado_em", "")
        self.parametros_texto = kwargs.pop("parametros_texto", "")
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
        w, h = landscape(A4)
        self.setFont("Helvetica-Bold", 10)
        self.setFillColor(colors.HexColor("#1E293B"))
        self.drawString(15, h - 22, self.titulo)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(15, h - 28, w - 15, h - 28)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(15, 12, f"Gerado em {self.gerado_em}")
        if self.parametros_texto: self.drawCentredString(w / 2, 12, self.parametros_texto)
        self.drawRightString(w - 15, 12, f"Página {self._pageNumber} de {page_count}")

def fmt_qtd(val):
    try:
        v = float(val)
        if v == 0: return "0"
        if v.is_integer(): return str(int(v))
        return f"{v:.2f}".replace(".", ",")
    except:
        return str(val)

def gerar_pdf_filial(nome_filial, cod, df, df_compras, df_demonstracao, nome_perfil, parametros_texto):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=15, leftMargin=15, topMargin=35, bottomMargin=25)
    elements = []
    styles = getSampleStyleSheet()
    
    filial_style = ParagraphStyle('F', parent=styles['Heading2'], fontSize=11, leading=13, textColor=colors.HexColor('#1E293B'), spaceBefore=0, spaceAfter=6)
    cell_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=0)
    cell_center = ParagraphStyle('CC', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=1)
    cell_right = ParagraphStyle('CR', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=2)
    header_style = ParagraphStyle('H', parent=styles['Normal'], fontSize=6.5, leading=8.5, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    
    # Estilo para o motivo COMPRA RECENTE
    cell_recente = ParagraphStyle('CRecente', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=0, fontName='Helvetica-Bold', textColor=colors.HexColor('#DC2626'))

    def _build(df_part, tipo):
        if df_part.empty: return Paragraph("<i>Nenhum item.</i>", cell_style)
        
        if tipo == "ENV":
            heads = ["#", "PRI.", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD", "TRANS.", "RES.", "IDEAL", "MOTIVO"]
            widths = [28, 34, 45, 150, 30, 120, 55, 55, 36, 40, 40, 36, 180]
            mapper = lambda r: [(r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialOrigem"], "C"), (r["NomeFilialDestino"], "C"), (fmt_qtd(r["QtdTransferir"]), "R"), (int(r["QtdEmTransito"]), "R"), (int(r["ReservaOrigem"]), "R"), (fmt_qtd(r["Qtd Ideal"]), "R"), (str(r["Motivo"]).upper(), "L")]
        
        elif tipo == "REC":
            heads = ["#", "PRI.", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD", "TRANS.", "DIAS", "IDEAL", "MOTIVO"]
            widths = [28, 34, 45, 150, 30, 120, 55, 55, 36, 40, 40, 36, 180]
            mapper = lambda r: [(r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialOrigem"], "C"), (r["NomeFilialDestino"], "C"), (fmt_qtd(r["QtdTransferir"]), "R"), (int(r["QtdEmTransito"]), "R"), (int(r["DiasAteZerarDestino"]) if pd.notna(r["DiasAteZerarDestino"]) else 0, "R"), (fmt_qtd(r["Qtd Ideal"]), "R"), (str(r["Motivo"]).upper(), "L")]

        elif tipo == "COMP":
            if cod == 5:
                heads = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN.", "MOTIVO"]
                widths = [28, 45, 160, 30, 110, 50, 40, 50, 50, 60, 150]
                mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (f"{r['Velocidade']:.2f}", "R"), (int(r["Ideal"]), "R"), (fmt_qtd(r["QtdSugerida"]), "R"), (f"R$ {r['Custo']:.2f}", "R"), (f"R$ {r['RetornoFinanceiro']:.2f}", "R"), (str(r["Motivo"]).upper(), "L")]
            else:
                heads = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN.", "MOTIVO"]
                widths = [28, 45, 160, 30, 110, 50, 40, 50, 50, 60, 150]
                mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (f"{r['Velocidade']:.2f}", "R"), (int(r["Ideal"]), "R"), (fmt_qtd(r["QtdSugerida"]), "R"), (f"R$ {r['Custo']:.2f}", "R"), (f"R$ {r['RetornoFinanceiro']:.2f}", "R"), (str(r["Motivo"]).upper(), "L")]

        elif tipo == "DEM":
            heads = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD", "MOTIVO"]
            widths = [28, 45, 170, 30, 120, 60, 85, 50, 200]
            mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialOrigem"], "C"), (r["NomeFilialDestino"], "C"), (fmt_qtd(r["QtdTransferir"]), "R"), (str(r["Motivo"]).upper(), "L")]

        data = [[Paragraph(h, header_style) for h in heads]]
        for _, row in df_part.iterrows():
            vals = []
            for v, align in mapper(row):
                if v is None or (isinstance(v, float) and pd.isna(v)): v = ""
                elif isinstance(v, float) and v.is_integer(): v = int(v)
                
                if align == "L" and str(v).upper() == "COMPRA RECENTE":
                    vals.append(Paragraph("[!!] COMPRA RECENTE", cell_recente))
                else:
                    stl = cell_right if align == "R" else (cell_center if align == "C" else cell_style)
                    vals.append(Paragraph(str(v), stl))
            data.append(vals)

        t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTSIZE', (0, 0), (-1, -1), 6.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        return t

    df_env = df[df["CodigoFilialOrigem"] == cod].copy()
    df_rec = df[df["CodigoFilialDestino"] == cod].copy()
    
    if not df_compras.empty:
        if cod == 5:
            _motivo_agg = lambda s: "SEM ESTOQUE" if (s == "SEM ESTOQUE").all() else "ESTOQUE COMPLEMENTAR"
            df_comp = df_compras.groupby(["CodigoProduto", "Produto", "Embalagem", "Fabricante"], as_index=False).agg({
                "QtdSugerida": "sum", 
                "Ideal": "sum",
                "RetornoFinanceiro": "sum",
                "Custo": "max",
                "Velocidade": "max",
                "Motivo": _motivo_agg,
            })
            df_comp = df_comp.sort_values("Produto").reset_index(drop=True)
        else:
            df_comp = df_compras[df_compras["NomeFilialDestino"] == nome_filial].copy()
    else:
        df_comp = pd.DataFrame()

    if not df_demonstracao.empty:
        if cod == 5:
            df_dem = df_demonstracao[df_demonstracao["NomeFilialOrigem"] == nome_filial].copy()
        else:
            df_dem = df_demonstracao[(df_demonstracao["NomeFilialOrigem"] == nome_filial) | (df_demonstracao["NomeFilialDestino"] == nome_filial)].copy()
    else:
        df_dem = pd.DataFrame()

    if df_env.empty and df_rec.empty and df_comp.empty and df_dem.empty:
        elements.append(Paragraph(f"<b>Sem movimentações para {nome_filial.title()}</b>", filial_style))
        agora = agora_br()
        doc.build(elements, canvasmaker=lambda *a, **kw: HeaderFooterCanvas(*a, titulo=f"Relatorio de Reposicao - {nome_perfil} - {nome_filial.title()}", gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), parametros_texto=parametros_texto, **kw))
        buffer.seek(0)
        return buffer, agora

    env_totais = df_env[~df_env["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])]
    liq_totais = df_env[df_env["NomeFilialDestino"] == "LIQUIDAR"]
    desc_totais = df_env[df_env["NomeFilialDestino"] == "DESCONTINUAR"]
    comp_totais = df_comp
    dem_totais = df_dem

    resumo_data = [
        ["", "ENVIAR", "RECEBER", "DEMONSTRAR", "DESCONTINUAR", "LIQUIDAR", "COMPRAR"],
        ["Itens", str(len(env_totais)), str(len(df_rec)), str(len(dem_totais)), str(len(desc_totais)), str(len(liq_totais)), str(len(comp_totais))],
        ["Unidades", str(int(env_totais["QtdTransferir"].sum()) if not env_totais.empty else 0), str(int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0), str(int(dem_totais["QtdTransferir"].sum()) if not dem_totais.empty else 0), str(int(desc_totais["QtdTransferir"].sum()) if not desc_totais.empty else 0), str(int(liq_totais["QtdTransferir"].sum()) if not liq_totais.empty else 0), str(int(comp_totais["QtdSugerida"].sum()) if not comp_totais.empty else 0)]
    ]
    t_resumo = Table(resumo_data, colWidths=[70, 70, 70, 80, 90, 70, 70], hAlign='LEFT')
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
        ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 14))
    
    df_liq = df_env[df_env["NomeFilialDestino"] == "LIQUIDAR"].copy()
    df_desc = df_env[df_env["NomeFilialDestino"] == "DESCONTINUAR"].copy()
    df_env = df_env[~df_env["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])].copy()

    if not df_env.empty:
        df_env = df_env.reset_index(drop=True); df_env.insert(0, "#", range(1, len(df_env) + 1))
        df_env["Qtd Ideal"] = df_env["IdealDestino"] if cod == 5 else df_env["IdealOrigem"]
        df_env["Prioridade"] = df_env["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>ENVIAR</b>", filial_style)); elements.append(_build(df_env, "ENV")); elements.append(Spacer(1, 14))
    
    if not df_rec.empty:
        df_rec = df_rec.reset_index(drop=True); df_rec.insert(0, "#", range(1, len(df_rec) + 1))
        df_rec["Qtd Ideal"] = df_rec["IdealDestino"]; df_rec["Prioridade"] = df_rec["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>RECEBER</b>", filial_style)); elements.append(_build(df_rec, "REC")); elements.append(Spacer(1, 14))
        
    if not df_dem.empty:
        df_dem = df_dem.reset_index(drop=True); df_dem.insert(0, "#", range(1, len(df_dem) + 1))
        elements.append(Paragraph("<b>DEMONSTRAR</b>", filial_style)); elements.append(_build(df_dem, "DEM")); elements.append(Spacer(1, 14))
    
    if not df_desc.empty:
        df_desc = df_desc.reset_index(drop=True); df_desc.insert(0, "#", range(1, len(df_desc) + 1))
        df_desc["Qtd Ideal"] = 0
        elements.append(Paragraph("<b>DESCONTINUAR</b>", filial_style)); elements.append(_build(df_desc, "DEM")); elements.append(Spacer(1, 14))
    
    if not df_liq.empty:
        df_liq = df_liq.reset_index(drop=True); df_liq.insert(0, "#", range(1, len(df_liq) + 1))
        df_liq["Qtd Ideal"] = 0
        elements.append(Paragraph("<b>LIQUIDAR</b>", filial_style)); elements.append(_build(df_liq, "DEM")); elements.append(Spacer(1, 14))

    if not df_comp.empty:
        df_comp = df_comp.reset_index(drop=True); df_comp.insert(0, "#", range(1, len(df_comp) + 1))
        elements.append(Paragraph("<b>COMPRAR</b>", filial_style)); elements.append(_build(df_comp, "COMP"))

    agora = agora_br()
    doc.build(elements, canvasmaker=lambda *a, **kw: HeaderFooterCanvas(*a, titulo=f"Relatorio de Reposicao - {nome_perfil} - {nome_filial.title()}", gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), parametros_texto=parametros_texto, **kw))
    buffer.seek(0)
    return buffer, agora

# ============================================================
# CONSULTAR E EXPORTAR
# ============================================================
executar_consulta = btn_consultar or st.session_state.get("auto_consultar", False)

if executar_consulta:
    st.session_state["auto_consultar"] = False # Reseta o gatilho para não rodar no próximo clique

    produto_preenchido = bool(produto_busca and produto_busca.strip())
    if produto_preenchido and not bloqueado:
        fabricante_filtro, departamento_filtro, grupo_filtro, subgrupo_filtro = "", "", "", ""
    else:
        fabricante_filtro = "" if fabricante_sel == "(todos)" or bloqueado else fabricantes[fabricante_sel]
        departamento_filtro = "" if depto_sel == "(todos)" or bloqueado else departamentos[depto_sel]
        grupo_filtro = "" if grupo_sel == "(todos)" or bloqueado else grupos[grupo_sel]
        subgrupo_filtro = "" if subgrupo_sel == "(todos)" or bloqueado else subgrupos[subgrupo_sel]

    nenhum_filtro = not produto_preenchido and not fabricante_filtro and not departamento_filtro and not grupo_filtro and not subgrupo_filtro

    if nenhum_filtro and not bloqueado:
        st.warning("⚠️ Digite um produto ou escolha pelo menos 1 filtro.")
    else:
        try:
            with st.spinner("⏳ Construindo Base..."):
                # Recarrega compras recentes com o período atualizado
                compras_recentes = carregar_compras_recentes(st.session_state.get("dias_compra", 30))
                
                df_base = carregar_base(
                    data_ref.strftime("%Y-%m-%d"), 
                    lookback, 
                    fabricante_filtro, 
                    departamento_filtro, 
                    grupo_filtro, 
                    subgrupo_filtro, 
                    "", 
                    produto_busca if not bloqueado else ""
                )
                st.session_state["df_base"] = df_base

            with st.spinner("⏳ Calculando sugestões..."):
                df_transito = carregar_transf_em_transito(data_ref.strftime("%Y-%m-%d"), dias_transito)
                df_recebidas = carregar_transf_recebidas_recentes(data_ref.strftime("%Y-%m-%d"), anti_gangorra)
                # Prepara IDs da NF (força fluxo normal no motor)
                forcar_normal_ids = None
                if bloqueado:
                    num_nf_pre = str(st.session_state.get("nf_num"))
                    df_nf_pre = compras_recentes[compras_recentes["NumeroNF"].astype(str) == num_nf_pre]
                    forcar_normal_ids = df_nf_pre["IdProduto"].dropna().astype(int).unique().tolist()

                df_transf, df_compras, df_demonstracao = gerar_sugestoes(
                    df_base, df_transito, df_recebidas, cobertura, lead_time, piso, reserva, 
                    (atacado_piso == "Sim"), (atacado_reserva == "Sim"), (atacado_min_compra == "Sim"),
                    forcar_normal_ids=forcar_normal_ids
                )
                
                # --- FILTRO E INJEÇÃO DA COMPRA RECENTE (Se houver NF selecionada) ---
                if bloqueado:
                    num_nf = st.session_state.get("nf_num")
                    df_nf = compras_recentes[compras_recentes["NumeroNF"].astype(str) == num_nf]
                    fab_nf = df_nf["Fabricante"].dropna().unique().tolist()
                    prod_nf = df_nf["CodigoProduto"].dropna().astype(str).unique().tolist()
                    filial_nf = df_nf["Filial"].iloc[0]
                    cod_filial_nf = codigos_filial.get(filial_nf, 0)
                    
                    # Quantidade disponível por produto (para capar transferências)
                    qtd_por_prod_nf = {str(k): float(v) for k, v in df_nf.groupby("CodigoProduto")["QtdComprada"].sum().items()}

                    # 1. ENVIAR / RECEBER
                    if not df_transf.empty:
                        df_transf = df_transf[df_transf["Fabricante"].isin(fab_nf)].copy()
                        
                        # Remove DESC/LIQ para os itens da nota (produto novo não é descontinuado)
                        mask_desc_liq = df_transf["NomeFilialDestino"].isin(["DESCONTINUAR", "LIQUIDAR"])
                        mask_prod_nf = df_transf["CodigoProduto"].astype(str).isin(prod_nf)
                        df_transf = df_transf[~(mask_desc_liq & mask_prod_nf)].copy()

                        # Cap quantidade + Força origem + Motivo COMPRA RECENTE
                        mask_comprado = df_transf["CodigoProduto"].astype(str).isin(prod_nf)
                        if mask_comprado.any():
                            disponivel_nf = dict(qtd_por_prod_nf)
                            for idx in df_transf[mask_comprado].sort_values("Prioridade").index:
                                cod_prod = str(df_transf.loc[idx, "CodigoProduto"])
                                disp = disponivel_nf.get(cod_prod, 0)
                                qtd = df_transf.loc[idx, "QtdTransferir"]
                                if qtd > disp:
                                    df_transf.loc[idx, "QtdTransferir"] = disp
                                    disponivel_nf[cod_prod] = 0
                                else:
                                    disponivel_nf[cod_prod] = disp - qtd
                            
                            df_transf.loc[mask_comprado, "NomeFilialOrigem"] = filial_nf
                            df_transf.loc[mask_comprado, "CodigoFilialOrigem"] = cod_filial_nf
                            df_transf.loc[mask_comprado, "Motivo"] = "COMPRA RECENTE"
                            df_transf.loc[mask_comprado, "Prioridade"] = 1
                            
                            df_transf = df_transf[df_transf["QtdTransferir"] > 0].copy()
                        
                        df_transf = df_transf.sort_values(["Prioridade", "NomeFilialDestino", "Produto"]).reset_index(drop=True)

                    # 2. COMPRAR — Remove itens da NF (eles já chegaram)
                    if not df_compras.empty:
                        df_compras = df_compras[df_compras["Fabricante"].isin(fab_nf)].copy()
                        df_compras = df_compras[~df_compras["CodigoProduto"].astype(str).isin(prod_nf)]

                    # 3. DEMONSTRAR — Converte itens da NF em ENVIAR/RECEBER (evita sumir da tela)
                    if not df_demonstracao.empty:
                        df_demonstracao = df_demonstracao[df_demonstracao["Fabricante"].isin(fab_nf)].copy()
                        
                        # Separa os que são da NF
                        mask_dem_nf = df_demonstracao["CodigoProduto"].astype(str).isin(prod_nf)
                        df_dem_nf = df_demonstracao[mask_dem_nf].copy()
                        df_demonstracao = df_demonstracao[~mask_dem_nf].copy()
                        
                        # Move para df_transf como COMPRA RECENTE
                        if not df_dem_nf.empty:
                            df_dem_nf["NomeFilialOrigem"] = filial_nf
                            df_dem_nf["CodigoFilialOrigem"] = cod_filial_nf
                            df_dem_nf["Motivo"] = "COMPRA RECENTE"
                            df_dem_nf["Prioridade"] = 1
                            df_transf = pd.concat([df_transf, df_dem_nf], ignore_index=True)

                st.session_state["df_transf"] = df_transf
                st.session_state["df_compras"] = df_compras
                st.session_state["df_demonstracao"] = df_demonstracao
                st.session_state["df_base_n"] = len(df_base)
                if "pdf_bytes_global" in st.session_state: del st.session_state["pdf_bytes_global"]
        except Exception as e:
            st.error(f"❌ Erro: {e}")

if btn_pdf_global:
    _tem_transf = "df_transf" in st.session_state and not st.session_state["df_transf"].empty
    _tem_compras = "df_compras" in st.session_state and not st.session_state["df_compras"].empty
    _tem_dem = "df_demonstracao" in st.session_state and not st.session_state["df_demonstracao"].empty
    if not (_tem_transf or _tem_compras or _tem_dem):
        st.warning("⚠️ Faça uma consulta primeiro para depois gerar o PDF.")
    else:
        df_atual = st.session_state["df_transf"]
        df_compras_atual = st.session_state.get("df_compras", pd.DataFrame())
        df_demonstracao_atual = st.session_state.get("df_demonstracao", pd.DataFrame())
        cod_pdf = codigos_filial[filial_pdf]
        parametros_str = f"Cob: {cobertura}d | Lead: {lead_time}d | Res: {reserva}% | Piso: {piso} | Quarentena: {anti_gangorra}d | Trânsito: {dias_transito}d | Mín.Compra: {atacado_min_compra}"
        
        with st.spinner("Gerando PDF..."):
            try:
                pdf_bytes, agora = gerar_pdf_filial(
                    filial_pdf, cod_pdf, df_atual, df_compras_atual, df_demonstracao_atual, 
                    "Padrão", parametros_str
                )
                nome_file = filial_pdf.title().replace(" ", "")
                st.session_state["pdf_bytes_global"] = (pdf_bytes, f"Reposicao {nome_file} {agora.strftime('%Y%m%d %H%M%S')}.pdf")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

if "pdf_bytes_global" in st.session_state and st.session_state["pdf_bytes_global"][0] is not None:
    import base64
    _pdf_data, _file_name = st.session_state["pdf_bytes_global"]
    
    # Converte o PDF em base64
    b64_pdf = base64.b64encode(_pdf_data.getvalue()).decode()
    
    # HTML/JS para acionar o download automaticamente
    dl_html = f'''
        <a id="auto_download_pdf" href="data:application/pdf;base64,{b64_pdf}" download="{_file_name}" style="display:none;"></a>
        <script>
            document.getElementById("auto_download_pdf").click();
        </script>
    '''
    components.html(dl_html, height=0)
    
    # Limpa o estado após o download para não baixar várias vezes no refresh
    st.session_state["pdf_bytes_global"] = (None, None)

# ============================================================
# RESULTADO (ABAS)
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]
    df_compras = st.session_state.get("df_compras", pd.DataFrame())
    df_demonstracao = st.session_state.get("df_demonstracao", pd.DataFrame())

    # Prepara dados da NF selecionada + ideals por filial (para usar nas abas)
    df_nf_view = pd.DataFrame()
    ideals_dict = {}
    if bloqueado:
        num_nf_view = st.session_state.get("nf_num")
        if num_nf_view:
            df_nf_view = compras_recentes[compras_recentes["NumeroNF"].astype(str) == str(num_nf_view)].copy()

        df_base_local = st.session_state.get("df_base", pd.DataFrame())
        if not df_base_local.empty and not df_nf_view.empty:
            cobertura_local = {"Para 7 dias": 7, "Para 15 dias": 15, "Para 30 dias": 30, "Para 2 meses": 60, "Para 3 meses": 90, "Para 6 meses": 180, "Para 1 ano": 365}.get(cobertura_opcao, 30)
            dias_local = cobertura_local + lead_time

            for _, row in df_base_local.iterrows():
                key = (str(row["CodigoProduto"]), int(row["CodigoFilial"]))
                pesavel = str(row.get("ProdutoPesavel", "N")).strip().upper() == "S"
                custo = float(row.get("CustoUnitario", 0))
                velocidade = float(row.get("VelocidadePeriodo", 0))
                cod_f = int(row["CodigoFilial"])

                piso_base = 0 if (cod_f == 5 and atacado_piso != "Sim") else piso
                if pesavel:
                    piso_ajustado = 0.1
                elif custo >= 20.0:
                    piso_ajustado = 1.0
                else:
                    piso_ajustado = float(piso_base)

                ideal_raw = max(piso_ajustado, velocidade * dias_local)
                ideal = round(ideal_raw, 2) if pesavel else math.ceil(ideal_raw)
                ideals_dict[key] = ideal

    if df.empty and df_compras.empty and df_demonstracao.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        nomes_todos = ["ATACADO", "ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE"]
        produto_preenchido = bool(produto_busca and produto_busca.strip())

        if filial_sel != "(todas)" and not produto_preenchido and not bloqueado:
            cod_sel = int(filiais[filial_sel])
            nomes = [n for n in nomes_todos if codigos_filial[n] == cod_sel]
        else:
            nomes = nomes_todos

        st.markdown('<div class="section-heading">🏬 Visão por filial</div>', unsafe_allow_html=True)
        st.caption("Acesse cada unidade para acompanhar transferências, compras e ações de estoque.")
        nomes_com_icone = [f"{icones_filial[n]} {n}" for n in nomes]
        tabs = st.tabs(nomes_com_icone)

        for i, nome in enumerate(nomes):
            cod = codigos_filial[nome]
            with tabs[i]:
                # "Itens desta NF" dentro da aba (com ideal específico da filial)
                if bloqueado and not df_nf_view.empty:
                    df_nf_tab = df_nf_view.copy()
                    df_nf_tab["QtdIdealFilial"] = df_nf_tab["CodigoProduto"].apply(
                        lambda cp: ideals_dict.get((str(cp), cod), 0)
                    )
                    df_nf_tab.insert(0, "#", range(1, len(df_nf_tab) + 1))
                    df_nf_tab_display = df_nf_tab[["#", "CodigoProduto", "Produto", "Fabricante", "QtdComprada", "QtdIdealFilial"]].copy()
                    df_nf_tab_display.columns = ["#", "COD", "PRODUTO", "FABRICANTE", "QTD COMPRADA", "QTD IDEAL"]
                    df_nf_tab_display["QTD COMPRADA"] = df_nf_tab_display["QTD COMPRADA"].map(fmt_qtd)
                    df_nf_tab_display["QTD IDEAL"] = df_nf_tab_display["QTD IDEAL"].map(fmt_qtd)

                    with st.expander(f"📋 Itens desta NF ({len(df_nf_tab)} itens)", expanded=False):
                        st.dataframe(df_nf_tab_display, use_container_width=True, hide_index=True)

                df_env_all = df[df["CodigoFilialOrigem"] == cod].copy().reset_index(drop=True)
                df_rec = df[df["CodigoFilialDestino"] == cod].copy().reset_index(drop=True)

                if not df_demonstracao.empty:
                    df_dem = df_demonstracao[(df_demonstracao["NomeFilialOrigem"] == nome) | (df_demonstracao["NomeFilialDestino"] == nome)].copy()
                else:
                    df_dem = pd.DataFrame()

                df_liq = df_env_all[df_env_all["NomeFilialDestino"] == "LIQUIDAR"].copy().reset_index(drop=True)
                df_desc = df_env_all[df_env_all["NomeFilialDestino"] == "DESCONTINUAR"].copy().reset_index(drop=True)
                df_env = df_env_all[~df_env_all["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])].copy().reset_index(drop=True)

                if nome == "ATACADO":
                    if not df_compras.empty:
                        _motivo_agg = lambda s: "SEM ESTOQUE" if (s == "SEM ESTOQUE").all() else "ESTOQUE COMPLEMENTAR"
                        df_comp_view = df_compras.groupby(["CodigoProduto", "Produto", "Embalagem", "Fabricante"], as_index=False).agg({
                            "QtdSugerida": "sum",
                            "Ideal": "sum",
                            "RetornoFinanceiro": "sum",
                            "Custo": "max",
                            "Velocidade": "max",
                            "Motivo": _motivo_agg,
                        })
                        df_comp_view = df_comp_view.sort_values("Produto").reset_index(drop=True)
                    else:
                        df_comp_view = pd.DataFrame()
                else:
                    df_comp_view = df_compras[df_compras["NomeFilialDestino"] == nome].copy() if not df_compras.empty else pd.DataFrame()

                env_itens = len(df_env)
                env_unid = int(df_env["QtdTransferir"].sum()) if not df_env.empty else 0

                rec_itens = len(df_rec)
                rec_unid = int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0

                dem_itens = len(df_dem)
                dem_unid = int(df_dem["QtdTransferir"].sum()) if not df_dem.empty else 0

                liq_itens = len(df_liq)
                liq_unid = int(df_liq["QtdTransferir"].sum()) if not df_liq.empty else 0

                desc_itens = len(df_desc)
                desc_unid = int(df_desc["QtdTransferir"].sum()) if not df_desc.empty else 0

                comp_itens = len(df_comp_view)
                comp_unid = int(df_comp_view["QtdSugerida"].sum()) if not df_comp_view.empty else 0

                html_metrics = f"""
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-card-title">📤 ENVIAR</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{env_itens}</div><div>{env_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">📥 RECEBER</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{rec_itens}</div><div>{rec_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🎯 DEMONSTRAR</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{dem_itens}</div><div>{dem_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">⏸️ DESC.</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{desc_itens}</div><div>{desc_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🔥 LIQUIDAR</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{liq_itens}</div><div>{liq_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🛒 COMPRAR</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{comp_itens}</div><div>{comp_unid}</div></div>
                    </div>
                </div>
                """
                st.markdown(html_metrics, unsafe_allow_html=True)
                st.write("")

                st.markdown('<div class="section-heading">Movimentações e recomendações</div>', unsafe_allow_html=True)
                st.caption("Escolha uma operação para consultar os itens da filial. Os indicadores acima permanecem consolidados.")
                oper_tabs = st.tabs(['📤 Enviar', '📥 Receber', '🎯 Demonstrar', '⏸️ Descontinuar', '🔥 Liquidar', '🛒 Comprar'])
                with oper_tabs[0]:
                    if df_env.empty:
                        st.caption("Nada a enviar")
                    else:
                        dfe = df_env.copy(); dfe.insert(0, "#", range(1, len(dfe) + 1))
                        dfe["Qtd Ideal"] = dfe["IdealDestino"] if cod == 5 else dfe["IdealOrigem"]
                        dfe["Prioridade"] = dfe["Prioridade"].map(PRIO_TXT).fillna("-")
                        dfe["Motivo"] = dfe["Motivo"].astype(str).str.upper()
                        dfe = dfe[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "NomeFilialDestino", "QtdTransferir", "QtdEmTransito", "ReservaOrigem", "Qtd Ideal", "Motivo"]]
                        dfe.columns = ["#", "PRIORIDADE", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD TRANSF.", "EM TRÂNSITO", "RESERVA", "QTD IDEAL", "MOTIVO"]
                        st.dataframe(dfe.style.format({
                            "QTD TRANSF.": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "QTD IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "EM TRÂNSITO": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "RESERVA": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                        }).set_properties(subset=["QTD TRANSF.", "EM TRÂNSITO", "RESERVA", "QTD IDEAL"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfe) * 36 + 42)))

                with oper_tabs[1]:
                    if df_rec.empty:
                        st.caption("Nada a receber")
                    else:
                        dfr = df_rec.copy(); dfr.insert(0, "#", range(1, len(dfr) + 1))
                        dfr["Qtd Ideal"] = dfr["IdealDestino"]; dfr["Prioridade"] = dfr["Prioridade"].map(PRIO_TXT).fillna("-")
                        dfr["Dias p/ Zerar"] = dfr["DiasAteZerarDestino"].apply(lambda x: 0 if pd.isna(x) or x is None else int(x)).astype(int)
                        dfr["Motivo"] = dfr["Motivo"].astype(str).str.upper()
                        dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "NomeFilialDestino", "QtdTransferir", "QtdEmTransito", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]]
                        dfr.columns = ["#", "PRIORIDADE", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD TRANSF.", "EM TRÂNSITO", "DIAS P/ ZERAR", "QTD IDEAL", "MOTIVO"]
                        st.dataframe(dfr.style.format({
                            "QTD TRANSF.": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "QTD IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "EM TRÂNSITO": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "DIAS P/ ZERAR": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                        }).set_properties(subset=["QTD TRANSF.", "EM TRÂNSITO", "DIAS P/ ZERAR", "QTD IDEAL"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfr) * 36 + 42)))

                with oper_tabs[2]:
                    if df_dem.empty:
                        st.caption("Nenhum produto para demonstração")
                    else:
                        dfm = df_dem.copy()
                        dfm.insert(0, "#", range(1, len(dfm) + 1))
                        dfm["Motivo"] = dfm["Motivo"].astype(str).str.upper()
                        dfm = dfm[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "NomeFilialDestino", "QtdTransferir", "Motivo"]]
                        dfm.columns = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD", "MOTIVO"]
                        st.dataframe(dfm.style.format({
                            "QTD": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                        }).set_properties(subset=["QTD"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfm) * 36 + 42)), column_config={"DESTINO": st.column_config.TextColumn("DESTINO", width="medium")})

                with oper_tabs[3]:
                    if df_desc.empty:
                        st.caption("Nenhum produto para descontinuar")
                    else:
                        dfd = df_desc.copy(); dfd.insert(0, "#", range(1, len(dfd) + 1))
                        dfd["Motivo"] = dfd["Motivo"].astype(str).str.upper()
                        dfd = dfd[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "NomeFilialDestino", "QtdTransferir", "IdealOrigem", "Motivo"]]
                        dfd.columns = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD P/ DESC.", "QTD IDEAL", "MOTIVO"]
                        st.dataframe(dfd.style.format({
                            "QTD P/ DESC.": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "QTD IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                        }).set_properties(subset=["QTD P/ DESC.", "QTD IDEAL"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfd) * 36 + 42)), column_config={"DESTINO": st.column_config.TextColumn("DESTINO", width="medium")})

                with oper_tabs[4]:
                    if df_liq.empty:
                        st.caption("Nenhum produto para liquidar")
                    else:
                        dfi = df_liq.copy(); dfi.insert(0, "#", range(1, len(dfi) + 1))
                        dfi["Motivo"] = dfi["Motivo"].astype(str).str.upper()
                        dfi = dfi[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "NomeFilialDestino", "QtdTransferir", "IdealOrigem", "Motivo"]]
                        dfi.columns = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "ORIGEM", "DESTINO", "QTD P/ LIQ.", "QTD IDEAL", "MOTIVO"]
                        st.dataframe(dfi.style.format({
                            "QTD P/ LIQ.": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            "QTD IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                        }).set_properties(subset=["QTD P/ LIQ.", "QTD IDEAL"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfi) * 36 + 42)), column_config={"DESTINO": st.column_config.TextColumn("DESTINO", width="medium")})

                with oper_tabs[5]:
                    if df_comp_view.empty:
                        st.caption("Nenhuma compra sugerida no momento")
                    else:
                        dfc = df_comp_view.copy()
                        dfc.insert(0, "#", range(1, len(dfc) + 1))
                        dfc["Motivo"] = dfc["Motivo"].astype(str).str.upper()

                        if nome == "ATACADO":
                            dfc = dfc[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "Velocidade", "Ideal", "QtdSugerida", "Custo", "RetornoFinanceiro", "Motivo"]]
                            dfc["Velocidade"] = dfc["Velocidade"].apply(lambda x: f"{x:.2f}")
                            dfc.columns = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN. (R$)", "MOTIVO"]
                            st.dataframe(dfc.style.format({
                                "CUSTO": "R$ {:.2f}",
                                "RETORNO FIN. (R$)": "R$ {:.2f}",
                                "SUGESTÃO": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                                "IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            }).set_properties(subset=["VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN. (R$)"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfc) * 36 + 42)))
                        else:
                            dfc = dfc[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "Velocidade", "Ideal", "QtdSugerida", "Custo", "RetornoFinanceiro", "Motivo"]]
                            dfc["Velocidade"] = dfc["Velocidade"].apply(lambda x: f"{x:.2f}")
                            dfc.columns = ["#", "COD", "PRODUTO", "EMB.", "FABRICANTE", "VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN. (R$)", "MOTIVO"]
                            st.dataframe(dfc.style.format({
                                "CUSTO": "R$ {:.2f}",
                                "RETORNO FIN. (R$)": "R$ {:.2f}",
                                "SUGESTÃO": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                                "IDEAL": lambda x: f"{x:.2f}".replace(".", ",") if x != int(x) else str(int(x)),
                            }).set_properties(subset=["VELOCIDADE", "IDEAL", "SUGESTÃO", "CUSTO", "RETORNO FIN. (R$)"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfc) * 36 + 42)))

if btn_manual:
    st.session_state["view"] = "manual"
    st.rerun()

st.markdown('<div class="rodape">v4.4 — 2026-11-17</div>', unsafe_allow_html=True)