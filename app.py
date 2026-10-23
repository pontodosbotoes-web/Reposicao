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
        /* --- LIMPEZA DA TELA --- */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stAppDeployButton {display: none;}

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            max-width: 100% !important;
        }

        .titulo-pagina {
            font-size: 1.6rem;
            font-weight: 700;
            text-align: center;
            margin: 0 0 15px 0;
            padding: 0;
            color: #FAFAFA;
            line-height: 1.2;
        }
        
        .secao-titulo {
            font-size: 1.05rem;
            font-weight: bold;
            padding: 6px 0;
            margin-top: 10px;
            margin-bottom: 6px;
            border-bottom: 2px solid #334155;
        }
        
        .rodape {
            position: fixed;
            bottom: 10px;
            right: 15px;
            font-size: 0.75rem;
            color: #64748B;
            z-index: 1000;
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

        /* --- GRID RESPONSIVO PARA MÉTRICAS --- */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
            margin-top: 10px;
        }
        .metric-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }
        .metric-card-title {
            font-size: 0.9rem;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 8px;
            border-bottom: 1px solid #334155;
            padding-bottom: 4px;
        }
        .metric-card-row {
            display: flex;
            justify-content: space-around;
            font-size: 0.75rem;
            color: #94A3B8;
            margin-bottom: 4px;
        }
        .metric-card-values {
            display: flex;
            justify-content: space-around;
            font-size: 1.2rem;
            font-weight: bold;
            color: #F8FAFC;
        }

        /* --- ESTILIZAÇÃO DOS BOTÕES --- */
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            width: 100% !important;
            height: 42px !important;
            padding: 4px 2px !important;
            font-size: 1.05rem !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.2s;
        }

        .st-key-btn_consultar button { background-color: #2563EB !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_consultar button:hover { background-color: #1D4ED8 !important; }
        
        .st-key-btn_limpar button { background-color: #DC2626 !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_limpar button:hover { background-color: #B91C1C !important; }
        
        .st-key-btn_parametros button { background-color: #7C3AED !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_parametros button:hover { background-color: #6D28D9 !important; }
        
        .st-key-btn_manual button { background-color: #059669 !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_manual button:hover { background-color: #047857 !important; }
        
        .st-key-btn_pdf button { background-color: #D97706 !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_pdf button:hover { background-color: #B45309 !important; }
        .st-key-btn_pdf button:disabled { background-color: #334155 !important; color: #94A3B8 !important; cursor: not-allowed; }
        
        .st-key-btn_download_pdf button { background-color: #0891B2 !important; color: #FFFFFF !important; border: none !important; }
        .st-key-btn_download_pdf button:hover { background-color: #0E7490 !important; }

        div[data-testid="stDataFrame"] div[role="columnheader"] {
            justify-content: center !important;
            text-align: center !important;
        }
    </style>
""", unsafe_allow_html=True)


st.markdown('<div class="titulo-pagina">Reposição de Produtos</div>', unsafe_allow_html=True)


PRIO_TXT = {1: "Crítica", 2: "Alta", 3: "Normal"}
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

PERFIS = {
    "Padrão": {"opcao_data": "1 ano atrás", "cobertura_opcao": "Para 30 dias", "lead_time": 10, "piso": 0, "reserva": 25, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 15, "dias_transito": 10},
    "Lançamento": {"opcao_data": "30 dias atrás", "cobertura_opcao": "Para 30 dias", "lead_time": 10, "piso": 5, "reserva": 0, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 7, "dias_transito": 10},
    "Classe A": {"opcao_data": "3 meses atrás", "cobertura_opcao": "Para 15 dias", "lead_time": 7, "piso": 10, "reserva": 25, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Sim", "anti_gangorra": 7, "dias_transito": 7},
    "Alto Giro": {"opcao_data": "3 meses atrás", "cobertura_opcao": "Para 15 dias", "lead_time": 7, "piso": 5, "reserva": 15, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 7, "dias_transito": 7},
    "Sazonal Longo": {"opcao_data": "2 meses atrás", "cobertura_opcao": "Para 30 dias", "lead_time": 10, "piso": 5, "reserva": 15, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Sim", "anti_gangorra": 7, "dias_transito": 10},
    "Sazonal Curto": {"opcao_data": "30 dias atrás", "cobertura_opcao": "Para 15 dias", "lead_time": 7, "piso": 3, "reserva": 5, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 5, "dias_transito": 7},
    "Baixo Giro": {"opcao_data": "1 ano atrás", "cobertura_opcao": "Para 30 dias", "lead_time": 10, "piso": 3, "reserva": 30, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 20, "dias_transito": 10},
    "Liquidação": {"opcao_data": "6 meses atrás", "cobertura_opcao": "Para 7 dias", "lead_time": 10, "piso": 0, "reserva": 0, "atacado_piso": "Não", "atacado_reserva": "Não", "atacado_min_compra": "Não", "anti_gangorra": 30, "dias_transito": 10},
}

if "show_params" not in st.session_state: st.session_state.show_params = False
if "view" not in st.session_state: st.session_state["view"] = "calculadora"

if st.session_state["view"] == "manual":
    render_manual()
    st.stop()

# ============================================================
# INICIALIZAÇÃO E SINCRONIA DE ESTADO
# ============================================================
if "perfil_sel" not in st.session_state:
    st.session_state["perfil_sel"] = "Padrão"

if st.session_state.get("_ultimo_perfil_aplicado") != st.session_state["perfil_sel"]:
    perfil_atual = st.session_state["perfil_sel"]
    for k, v in PERFIS[perfil_atual].items():
        st.session_state[k] = v
    st.session_state["_ultimo_perfil_aplicado"] = perfil_atual

for k, v in PERFIS["Padrão"].items():
    if k not in st.session_state:
        st.session_state[k] = v
if "fabricante_sel" not in st.session_state: st.session_state["fabricante_sel"] = "(todos)"
if "depto_sel" not in st.session_state: st.session_state["depto_sel"] = "(todos)"
if "grupo_sel" not in st.session_state: st.session_state["grupo_sel"] = "(todos)"
if "subgrupo_sel" not in st.session_state: st.session_state["subgrupo_sel"] = "(todos)"
if "produto_busca" not in st.session_state: st.session_state["produto_busca"] = ""
if "filial_param" not in st.session_state: st.session_state["filial_param"] = "(todas)"

# ============================================================
# CALLBACKS
# ============================================================
def _limpar_filtros():
    perfil_atual = st.session_state.get("perfil_sel", "Padrão")
    for k, v in PERFIS[perfil_atual].items():
        st.session_state[k] = v
    st.session_state["_ultimo_perfil_aplicado"] = perfil_atual
    
    st.session_state["fabricante_sel"] = "(todos)"
    st.session_state["depto_sel"] = "(todos)"
    st.session_state["grupo_sel"] = "(todos)"
    st.session_state["subgrupo_sel"] = "(todos)"
    st.session_state["produto_busca"] = ""
    st.session_state["filial_param"] = "(todas)"
    
    for _k in ("df_base", "df_transf", "df_compras", "df_demonstracao", "df_base_n", "pdf_bytes_global", "filial_pdf_sel"):
        if _k in st.session_state: del st.session_state[_k]

def _mudar_perfil():
    perfil_novo = st.session_state["perfil_sel"]
    for k, v in PERFIS[perfil_novo].items():
        st.session_state[k] = v
    st.session_state["_ultimo_perfil_aplicado"] = perfil_novo

# ============================================================
# LINHA 1: FILTROS
# ============================================================
f0, f1, f2, f3, f4, f5 = st.columns([1.6, 1.9, 1.3, 1.3, 1.3, 1.8], vertical_alignment="bottom")

with f0:
    st.selectbox(
        "Perfil de Análise", list(PERFIS.keys()), key="perfil_sel",
        help="**Perfil de Análise**\n\nEscolha um perfil para ajustar automaticamente os 9 parâmetros.",
        on_change=_mudar_perfil
    )
with f1: fabricante_sel = st.selectbox("Fabricante", ["(todos)"] + list(fabricantes.keys()), key="fabricante_sel")
with f2: depto_sel = st.selectbox("Departamento", ["(todos)"] + list(departamentos.keys()), key="depto_sel")
with f3: grupo_sel = st.selectbox("Grupo", ["(todos)"] + list(grupos.keys()), key="grupo_sel")
with f4: subgrupo_sel = st.selectbox("Subgrupo", ["(todos)"] + list(subgrupos.keys()), key="subgrupo_sel")
with f5:
    produto_busca = st.text_input(
        "Produto", placeholder='Ex: CAIXA QUADRADA (E) | CAPA, CAPUZ (OU)', key="produto_busca",
        help="Busca por produto com E / OU. Se preenchido, ignora os outros filtros."
    )

# ============================================================
# LINHA 2: BOTÕES
# ============================================================
st.write("")
b1, b2, b3, b4, b5, b6 = st.columns([1, 1, 1, 1.2, 1.5, 1.2])

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

if produto_busca and produto_busca.strip():
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
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        
        with r1c1: 
            lista_periodo = ["1 ano atrás", "6 meses atrás", "3 meses atrás", "2 meses atrás", "30 dias atrás", "15 dias atrás", "7 dias atrás"]
            idx_p = lista_periodo.index(st.session_state.get("opcao_data", "1 ano atrás")) if st.session_state.get("opcao_data") in lista_periodo else 0
            v_opcao = st.selectbox("Período de Análise", lista_periodo, index=idx_p)
            st.session_state["opcao_data"] = v_opcao
            
        with r1c2: 
            lista_filial = ["(todas)"] + list(filiais.keys())
            idx_f = lista_filial.index(st.session_state.get("filial_param", "(todas)")) if st.session_state.get("filial_param") in lista_filial else 0
            v_filial = st.selectbox("Filial", lista_filial, index=idx_f, help="Apenas visual: o motor sempre analisa todas as filiais.")
            st.session_state["filial_param"] = v_filial
            
        with r1c3: 
            lista_cob = ["Para 7 dias", "Para 15 dias", "Para 30 dias", "Para 2 meses", "Para 3 meses", "Para 6 meses", "Para 1 ano"]
            idx_c = lista_cob.index(st.session_state.get("cobertura_opcao", "Para 30 dias")) if st.session_state.get("cobertura_opcao") in lista_cob else 2
            v_cob = st.selectbox("Cobertura de Vendas", lista_cob, index=idx_c)
            st.session_state["cobertura_opcao"] = v_cob
            
        with r1c4: 
            v_lead = st.number_input("Tempo de Transporte (dias)", 0, 30, value=int(st.session_state.get("lead_time", 10)))
            st.session_state["lead_time"] = v_lead

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        
        with r2c1: 
            v_piso = st.number_input("Piso Exposição (un)", 0, 50, value=int(st.session_state.get("piso", 0)))
            st.session_state["piso"] = v_piso
            
        with r2c2: 
            v_reserva = st.number_input("Reserva Origem (%)", 0, 100, value=int(st.session_state.get("reserva", 25)))
            st.session_state["reserva"] = v_reserva
            
        with r2c3: 
            lista_sn = ["Não", "Sim"]
            idx_ap = lista_sn.index(st.session_state.get("atacado_piso", "Não")) if st.session_state.get("atacado_piso") in lista_sn else 0
            v_ap = st.selectbox("Atacado tem Piso?", lista_sn, index=idx_ap)
            st.session_state["atacado_piso"] = v_ap
            
        with r2c4: 
            idx_ar = lista_sn.index(st.session_state.get("atacado_reserva", "Não")) if st.session_state.get("atacado_reserva") in lista_sn else 0
            v_ar = st.selectbox("Atacado tem Reserva?", lista_sn, index=idx_ar)
            st.session_state["atacado_reserva"] = v_ar

        r3c1, r3c2, r3c3 = st.columns(3)
        
        with r3c1: 
            v_ag = st.number_input("Reposição Recente (dias)", 0, 90, value=int(st.session_state.get("anti_gangorra", 15)))
            st.session_state["anti_gangorra"] = v_ag
            
        with r3c2: 
            v_dt = st.number_input("Dias em Trânsito", 1, 60, value=int(st.session_state.get("dias_transito", 10)))
            st.session_state["dias_transito"] = v_dt
            
        with r3c3: 
            idx_am = lista_sn.index(st.session_state.get("atacado_min_compra", "Não")) if st.session_state.get("atacado_min_compra") in lista_sn else 0
            v_am = st.selectbox("Atacado tem Mínimo p/ Compra?", lista_sn, index=idx_am, help="Se Sim, usa o valor do Piso Exposição como quantidade mínima para sugerir compra.")
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

    def _build(df_part, tipo):
        if df_part.empty: return Paragraph("<i>Nenhum item.</i>", cell_style)
        
        if tipo == "ENV":
            heads = ["#", "Pr.", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Trans.", "Res.", "Ideal", "Motivo"]
            widths = [28, 34, 45, 180, 30, 120, 55, 36, 40, 40, 36, 150]
            mapper = lambda r: [(r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialDestino"], "C"), (int(r["QtdTransferir"]), "R"), (int(r["QtdEmTransito"]), "R"), (int(r["ReservaOrigem"]), "R"), (int(r["Qtd Ideal"]), "R"), (r["Motivo"], "L")]
        
        elif tipo == "REC":
            heads = ["#", "Pr.", "Cod", "Produto", "Emb.", "Fabricante", "Origem", "Qtd", "Trans.", "Dias", "Ideal", "Motivo"]
            widths = [28, 34, 45, 180, 30, 120, 55, 36, 40, 40, 36, 150]
            mapper = lambda r: [(r["#"], "C"), (r["Prioridade"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialOrigem"], "C"), (int(r["QtdTransferir"]), "R"), (int(r["QtdEmTransito"]), "R"), (int(r["DiasAteZerarDestino"]) if pd.notna(r["DiasAteZerarDestino"]) else 0, "R"), (int(r["Qtd Ideal"]), "R"), (r["Motivo"], "L")]

        elif tipo == "COMP":
            if cod == 5:
                heads = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Ideal", "Sugestão", "Retorno Fin.", "Motivo"]
                widths = [28, 45, 200, 30, 120, 50, 50, 60, 150]
                mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (int(r["Ideal"]), "R"), (int(r["QtdSugerida"]), "R"), (f"R$ {r['RetornoFinanceiro']:.2f}", "R"), (r["Motivo"], "L")]
            else:
                heads = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Velocidade", "Ideal", "Sugestão", "Retorno Fin.", "Motivo"]
                widths = [28, 45, 160, 30, 110, 50, 40, 50, 60, 150]
                mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (f"{r['Velocidade']:.2f}", "R"), (int(r["Ideal"]), "R"), (int(r["QtdSugerida"]), "R"), (f"R$ {r['RetornoFinanceiro']:.2f}", "R"), (r["Motivo"], "L")]

        elif tipo == "DEM":
            heads = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Motivo"]
            widths = [28, 45, 250, 30, 150, 80, 50, 200]
            mapper = lambda r: [(r["#"], "C"), (r["CodigoProduto"], "C"), (r["Produto"], "L"), (r["Embalagem"], "C"), (r["Fabricante"], "L"), (r["NomeFilialDestino"], "C"), (int(r["QtdTransferir"]), "R"), (r["Motivo"], "L")]

        data = [[Paragraph(h, header_style) for h in heads]]
        for _, row in df_part.iterrows():
            vals = []
            for v, align in mapper(row):
                if v is None or (isinstance(v, float) and pd.isna(v)): v = ""
                elif isinstance(v, float) and v.is_integer(): v = int(v)
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
            df_comp = df_compras.groupby(["CodigoProduto", "Produto", "Embalagem", "Fabricante"], as_index=False).agg({
                "QtdSugerida": "sum", 
                "Ideal": "sum",
                "RetornoFinanceiro": "sum"
            })
            df_comp["Motivo"] = df_comp.apply(lambda r: "SEM ESTOQUE" if r["QtdSugerida"] == r["Ideal"] else "ESTOQUE COMPLEMENTAR", axis=1)
            df_comp = df_comp.sort_values("Produto").reset_index(drop=True)
        else:
            df_comp = df_compras[df_compras["NomeFilialDestino"] == nome_filial].copy()
    else:
        df_comp = pd.DataFrame()

    if not df_demonstracao.empty:
        df_dem = df_demonstracao[df_demonstracao["NomeFilialOrigem"] == nome_filial].copy()
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
        df_desc["Prioridade"] = df_desc["Prioridade"].map(PRIO_TXT).fillna("-"); df_desc["Qtd Ideal"] = 0
        df_desc["NomeFilialDestino"] = df_desc["NomeFilialOrigem"]
        elements.append(Paragraph("<b>DESCONTINUAR</b>", filial_style)); elements.append(_build(df_desc, "ENV")); elements.append(Spacer(1, 14))
    
    if not df_liq.empty:
        df_liq = df_liq.reset_index(drop=True); df_liq.insert(0, "#", range(1, len(df_liq) + 1))
        df_liq["Prioridade"] = df_liq["Prioridade"].map(PRIO_TXT).fillna("-"); df_liq["Qtd Ideal"] = 0
        df_liq["NomeFilialDestino"] = df_liq["NomeFilialOrigem"]
        elements.append(Paragraph("<b>LIQUIDAR</b>", filial_style)); elements.append(_build(df_liq, "ENV")); elements.append(Spacer(1, 14))

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
if btn_consultar:
    produto_preenchido = bool(produto_busca and produto_busca.strip())
    if produto_preenchido:
        fabricante_filtro, departamento_filtro, grupo_filtro, subgrupo_filtro = "", "", "", ""
    else:
        fabricante_filtro = "" if fabricante_sel == "(todos)" else fabricantes[fabricante_sel]
        departamento_filtro = "" if depto_sel == "(todos)" else departamentos[depto_sel]
        grupo_filtro = "" if grupo_sel == "(todos)" else grupos[grupo_sel]
        subgrupo_filtro = "" if subgrupo_sel == "(todos)" else subgrupos[subgrupo_sel]

    nenhum_filtro = not produto_preenchido and not fabricante_filtro and not departamento_filtro and not grupo_filtro and not subgrupo_filtro

    if nenhum_filtro:
        st.warning("⚠️ Digite um produto ou escolha pelo menos 1 filtro.")
    else:
        try:
            with st.spinner("⏳ Construindo Base..."):
                df_base = carregar_base(data_ref.strftime("%Y-%m-%d"), lookback, fabricante_filtro, departamento_filtro, grupo_filtro, subgrupo_filtro, "", produto_busca)
                st.session_state["df_base"] = df_base

            with st.spinner("⏳ Calculando sugestões..."):
                df_transito = carregar_transf_em_transito(data_ref.strftime("%Y-%m-%d"), dias_transito)
                df_recebidas = carregar_transf_recebidas_recentes(data_ref.strftime("%Y-%m-%d"), anti_gangorra)
                df_transf, df_compras, df_demonstracao = gerar_sugestoes(
                    df_base, df_transito, df_recebidas, cobertura, lead_time, piso, reserva, 
                    (atacado_piso == "Sim"), (atacado_reserva == "Sim"), (atacado_min_compra == "Sim")
                )
                
                st.session_state["df_transf"] = df_transf
                st.session_state["df_compras"] = df_compras
                st.session_state["df_demonstracao"] = df_demonstracao
                st.session_state["df_base_n"] = len(df_base)
                if "pdf_bytes_global" in st.session_state: del st.session_state["pdf_bytes_global"]
        except Exception as e:
            st.error(f"❌ Erro: {e}")

if btn_pdf_global:
    if "df_transf" not in st.session_state or st.session_state["df_transf"].empty:
        st.warning("⚠️ Faça uma consulta primeiro para depois gerar o PDF.")
    else:
        df_atual = st.session_state["df_transf"]
        df_compras_atual = st.session_state.get("df_compras", pd.DataFrame())
        df_demonstracao_atual = st.session_state.get("df_demonstracao", pd.DataFrame())
        cod_pdf = codigos_filial[filial_pdf]
        parametros_str = f"Cob: {cobertura}d | Lead: {lead_time}d | Res: {reserva}% | Piso: {piso} | Quarentena: {anti_gangorra}d | Trânsito: {dias_transito}d | Mín.Compra: {atacado_min_compra}"
        
        with st.spinner("Gerando PDF..."):
            try:
                pdf_bytes, agora = gerar_pdf_filial(filial_pdf, cod_pdf, df_atual, df_compras_atual, df_demonstracao_atual, st.session_state.get("perfil_sel", "Padrão"), parametros_str)
                nome_file = filial_pdf.title().replace(" ", "")
                st.session_state["pdf_bytes_global"] = (pdf_bytes, f"Reposicao {nome_file} {agora.strftime('%Y%m%d %H%M%S')}.pdf")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

if "pdf_bytes_global" in st.session_state and st.session_state["pdf_bytes_global"][0] is not None:
    _pdf_data, _file_name = st.session_state["pdf_bytes_global"]
    st.download_button(
        label=f"⬇️ Baixar {_file_name}",
        data=_pdf_data,
        file_name=_file_name,
        mime="application/pdf",
        key="btn_download_pdf"
    )

# ============================================================
# RESULTADO (ABAS)
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]
    df_compras = st.session_state.get("df_compras", pd.DataFrame())
    df_demonstracao = st.session_state.get("df_demonstracao", pd.DataFrame())

    if df.empty and df_compras.empty and df_demonstracao.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        nomes_todos = ["ATACADO", "ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE"]
        produto_preenchido = bool(produto_busca and produto_busca.strip())
        
        if filial_sel != "(todas)" and not produto_preenchido:
            cod_sel = int(filiais[filial_sel])
            nomes = [n for n in nomes_todos if codigos_filial[n] == cod_sel]
        else:
            nomes = nomes_todos

        nomes_com_icone = [f"{icones_filial[n]} {n}" for n in nomes]
        tabs = st.tabs(nomes_com_icone)
        
        for i, nome in enumerate(nomes):
            cod = codigos_filial[nome]
            with tabs[i]:
                df_env_all = df[df["CodigoFilialOrigem"] == cod].copy().reset_index(drop=True)
                df_rec = df[df["CodigoFilialDestino"] == cod].copy().reset_index(drop=True)
                df_dem = df_demonstracao[df_demonstracao["NomeFilialOrigem"] == nome].copy() if not df_demonstracao.empty else pd.DataFrame()

                df_liq = df_env_all[df_env_all["NomeFilialDestino"] == "LIQUIDAR"].copy().reset_index(drop=True)
                df_desc = df_env_all[df_env_all["NomeFilialDestino"] == "DESCONTINUAR"].copy().reset_index(drop=True)
                df_env = df_env_all[~df_env_all["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])].copy().reset_index(drop=True)

                if nome == "ATACADO":
                    if not df_compras.empty:
                        df_comp_view = df_compras.groupby(["CodigoProduto", "Produto", "Embalagem", "Fabricante"], as_index=False).agg({
                            "QtdSugerida": "sum",
                            "Ideal": "sum",
                            "RetornoFinanceiro": "sum"
                        })
                        df_comp_view["Motivo"] = df_comp_view.apply(
                            lambda r: "SEM ESTOQUE" if r["QtdSugerida"] == r["Ideal"] else "ESTOQUE COMPLEMENTAR", 
                            axis=1
                        )
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
                        <div class="metric-card-title">📤 Enviar</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{env_itens}</div><div>{env_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">📥 Receber</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{rec_itens}</div><div>{rec_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🎯 Demonstrar</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{dem_itens}</div><div>{dem_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">⏸️ Desc.</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{desc_itens}</div><div>{desc_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🔥 Liquidar</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{liq_itens}</div><div>{liq_unid}</div></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-title">🛒 Comprar</div>
                        <div class="metric-card-row"><div>Itens</div><div>Unid</div></div>
                        <div class="metric-card-values"><div>{comp_itens}</div><div>{comp_unid}</div></div>
                    </div>
                </div>
                """
                st.markdown(html_metrics, unsafe_allow_html=True)
                st.write("")

                st.markdown('<div class="secao-titulo">📤 ENVIAR</div>', unsafe_allow_html=True)
                if df_env.empty:
                    st.caption("Nada a enviar")
                else:
                    dfe = df_env.copy(); dfe.insert(0, "#", range(1, len(dfe) + 1))
                    dfe["Qtd Ideal"] = dfe["IdealDestino"] if cod == 5 else dfe["IdealOrigem"]
                    dfe["Prioridade"] = dfe["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfe = dfe[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialDestino", "QtdTransferir", "QtdEmTransito", "ReservaOrigem", "Qtd Ideal", "Motivo"]]
                    dfe.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd Transf.", "Em Trânsito", "Reserva", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfe.style.set_properties(subset=["Qtd Transf.", "Em Trânsito", "Reserva", "Qtd Ideal"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfe) * 36 + 42)))

                st.markdown('<div class="secao-titulo">📥 RECEBER</div>', unsafe_allow_html=True)
                if df_rec.empty:
                    st.caption("Nada a receber")
                else:
                    dfr = df_rec.copy(); dfr.insert(0, "#", range(1, len(dfr) + 1))
                    dfr["Qtd Ideal"] = dfr["IdealDestino"]; dfr["Prioridade"] = dfr["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfr["Dias p/ Zerar"] = dfr["DiasAteZerarDestino"].apply(lambda x: 0 if pd.isna(x) or x is None else int(x)).astype(int)
                    dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialOrigem", "QtdTransferir", "QtdEmTransito", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]]
                    dfr.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Origem", "Qtd Transf.", "Em Trânsito", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfr.style.set_properties(subset=["Qtd Transf.", "Em Trânsito", "Dias p/ Zerar", "Qtd Ideal"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfr) * 36 + 42)))

                st.markdown('<div class="secao-titulo">🎯 DEMONSTRAR</div>', unsafe_allow_html=True)
                if df_dem.empty:
                    st.caption("Nenhum produto para demonstração")
                else:
                    dfm = df_dem.copy()
                    dfm.insert(0, "#", range(1, len(dfm) + 1))
                    dfm = dfm[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "NomeFilialDestino", "QtdTransferir", "Motivo"]]
                    dfm.columns = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Motivo"]
                    st.dataframe(dfm.style.set_properties(subset=["Qtd"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfm) * 36 + 42)))

                st.markdown('<div class="secao-titulo">⏸️ DESCONTINUAR</div>', unsafe_allow_html=True)
                if df_desc.empty:
                    st.caption("Nenhum produto para descontinuar")
                else:
                    dfd = df_desc.copy(); dfd.insert(0, "#", range(1, len(dfd) + 1))
                    dfd["Prioridade"] = dfd["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfd = dfd[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "QtdTransferir", "IdealOrigem", "Motivo"]]
                    dfd.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Desc.", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfd, use_container_width=True, hide_index=True, height=min(420, max(120, len(dfd) * 36 + 42)))

                st.markdown('<div class="secao-titulo">🔥 LIQUIDAR</div>', unsafe_allow_html=True)
                if df_liq.empty:
                    st.caption("Nenhum produto para liquidar")
                else:
                    dfi = df_liq.copy(); dfi.insert(0, "#", range(1, len(dfi) + 1))
                    dfi["Prioridade"] = dfi["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfi = dfi[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "QtdTransferir", "IdealOrigem", "Motivo"]]
                    dfi.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Liq.", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfi, use_container_width=True, hide_index=True, height=min(420, max(120, len(dfi) * 36 + 42)))

                st.markdown('<div class="secao-titulo">🛒 COMPRAR</div>', unsafe_allow_html=True)
                if df_comp_view.empty:
                    st.caption("Nenhuma compra sugerida no momento")
                else:
                    dfc = df_comp_view.copy()
                    dfc.insert(0, "#", range(1, len(dfc) + 1))
                    
                    if nome == "ATACADO":
                        dfc = dfc[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "Ideal", "QtdSugerida", "RetornoFinanceiro", "Motivo"]]
                        dfc.columns = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Ideal", "Sugestão", "Retorno Fin. (R$)", "Motivo"]
                        st.dataframe(dfc.style.format({"Retorno Fin. (R$)": "R$ {:.2f}"}).set_properties(subset=["Ideal", "Sugestão", "Retorno Fin. (R$)"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfc) * 36 + 42)))
                    else:
                        dfc = dfc[["#", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "Velocidade", "Ideal", "QtdSugerida", "RetornoFinanceiro", "Motivo"]]
                        dfc.columns = ["#", "Cod", "Produto", "Emb.", "Fabricante", "Velocidade", "Ideal", "Sugestão", "Retorno Fin. (R$)", "Motivo"]
                        dfc["Velocidade"] = dfc["Velocidade"].apply(lambda x: f"{x:.2f}")
                        st.dataframe(dfc.style.format({"Retorno Fin. (R$)": "R$ {:.2f}"}).set_properties(subset=["Velocidade", "Ideal", "Sugestão", "Retorno Fin. (R$)"], **{"text-align": "right"}), use_container_width=True, hide_index=True, height=min(420, max(120, len(dfc) * 36 + 42)))

if btn_manual:
    st.session_state["view"] = "manual"
    st.rerun()

st.markdown('<div class="rodape">v4.1 — 2026-10-23</div>', unsafe_allow_html=True)