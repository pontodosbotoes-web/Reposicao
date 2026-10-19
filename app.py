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
        /* --- LIMPEZA DA TELA (Esconder cabeçalhos do Streamlit) --- */
        #MainMenu {visibility: hidden;} /* Esconde o menu de 3 pontinhos */
        header {visibility: hidden;}    /* Esconde a barra superior inteira */
        footer {visibility: hidden;}    /* Esconde o rodapé ("Manage app") */
        .stAppDeployButton {display: none;} /* Esconde o botão Deploy */

        /* --- ÁREA ÚTIL DO APP (Expandir ao máximo) --- */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            max-width: 100% !important; /* Força o uso de 100% da largura */
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
    "Lançamento": {
        "opcao_data":       "30 dias atrás",
        "cobertura_opcao":  "Para 30 dias",
        "lead_time":        10,
        "piso":             5,         # Garante exposição da novidade
        "reserva":          0,         # Foco em distribuir
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    7,
        "dias_transito":    10,
    },
    "Classe A": {
        "opcao_data":       "3 meses atrás",
        "cobertura_opcao":  "Para 15 dias",
        "lead_time":        7,
        "piso":             10,        # Prateleira sempre cheia
        "reserva":          40,        # Protege a origem contra ruptura
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    7,
        "dias_transito":    7,
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
    "Sazonal Longo": {
        "opcao_data":       "2 meses atrás",      # Corrigido para combinar com o dropdown
        "cobertura_opcao":  "Para 30 dias",
        "lead_time":        10,
        "piso":             5,
        "reserva":          15,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    7,
        "dias_transito":    10,
    },
    "Sazonal Curto": {
        "opcao_data":       "30 dias atrás",
        "cobertura_opcao":  "Para 15 dias",
        "lead_time":        7,
        "piso":             3,
        "reserva":          5,
        "atacado_piso":     "Não",
        "atacado_reserva":  "Não",
        "anti_gangorra":    5,
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
# VALORES PADRÃO DOS WIDGETS (controlados via session_state)
# ============================================================
_DEFAULTS = {
    "perfil_sel":       "Padrão",
    "fabricante_sel":   "(todos)",
    "depto_sel":        "(todos)",
    "grupo_sel":        "(todos)",
    "subgrupo_sel":     "(todos)",
    "produto_busca":    "",
    "opcao_data":       "1 ano atrás",
    "filial_param":     "(todas)",
    "cobertura_opcao":  "Para 30 dias",
    "lead_time":        10,
    "piso":             0,
    "reserva":          25,
    "atacado_piso":     "Não",
    "atacado_reserva":  "Não",
    "anti_gangorra":    15,
    "dias_transito":    10,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

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

def _limpar_filtros():
    """Limpa filtros, parâmetros e resultados — chamado ANTES do rerun."""
    # Seta valores padrão (não deleta — deletar não reseta widgets no Streamlit)
    for _k, _v in _DEFAULTS.items():
        st.session_state[_k] = _v

    # Marca como se o Perfil "Padrão" já estivesse aplicado
    st.session_state["_ultimo_perfil_aplicado"] = "Padrão"

    # Limpa resultados em memória
    for _k in ("df_base", "df_transf", "df_base_n"):
        if _k in st.session_state:
            del st.session_state[_k]

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
        key="perfil_sel",
        help=(
            "**Perfil de Análise**\n\n"
            "Escolha um perfil para ajustar automaticamente os 9 parâmetros. "
            "**Um mesmo produto pode usar perfis diferentes dependendo do momento da análise.**\n\n"
            "**🔹 Padrão** — Uso geral. *1 ano de histórico, cobertura 30d, reserva 25%.*\n"
            "👉 *Ex: Materiais de escritório do dia a dia.*\n\n"
            "**🔹 Lançamento** — Novidade na prateleira. *30 dias de histórico, piso 5, reserva 0%.*\n"
            "👉 *Ex: Chegou a nova coleção de fitas de cetim de fim de ano. Mesmo sem histórico de venda, o piso garante a exposição.*\n\n"
            "**🔹 Classe A** — O carro-chefe da loja. *3 meses de histórico, piso 10, reserva 40%.*\n"
            "👉 *Ex: Papel kraft e fita adesiva básica. Não podem faltar nunca.*\n\n"
            "**🔹 Alto Giro** — Venda rápida e constante. *3 meses de histórico, cobertura 15d, lead 7d.*\n"
            "👉 *Ex: Bexigas de aniversário na primavera.*\n\n"
            "**🔹 Sazonal Longo** — Campanhas longas (Natal/Carnaval). *2 meses de histórico, piso 5, cobertura 30d.*\n"
            "👉 *Ex: Artigos de Natal em novembro. A demanda dura várias semanas.*\n\n"
            "**🔹 Sazonal Curto** — Pico explosivo (Páscoa/Mães/Halloween). *1 mês de histórico, cobertura 15d, reserva 5%.*\n"
            "👉 *Ex: Máscaras de Halloween. Vende tudo em uma semana, não pode estocar demais para não sobrar.*\n\n"
            "**🔹 Baixo Giro** — Produtos encalhados. *1 ano de histórico, piso 3, reserva 30%.*\n"
            "👉 *Ex: Tecido de seda específico que vende 1 rolo por mês.*\n\n"
            "**🔹 Liquidação** — Fim de ciclo. *6 meses de histórico, cobertura 7d, reserva 0%.*\n"
            "👉 *Ex: Itens de Halloween na primeira semana de novembro.*"
        ),
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
        placeholder='Ex: CAIXA QUADRADA (E) | CAPA, CAPUZ (OU)',
        key="produto_busca",
        help=(
            "Busca por produto com E / OU:\n\n"
            "• Espaço = E (AND): 'CAIXA QUADRADA' acha produtos que tenham "
            "as DUAS palavras.\n\n"
            "• Vírgula = OU (OR): 'CAPA, CAPUZ' acha produtos com UMA ou "
            "OUTRA.\n\n"
            "• Combine: 'CAIXA QUADRADA, CAPA' = (CAIXA E QUADRADA) OU CAPA."
        ),
    )

with b1:
    btn_consultar = st.button("🔍", type="primary", use_container_width=True, help="Consultar")
with b2:
    st.button("🧹", use_container_width=True, help="Limpar filtros", on_click=_limpar_filtros)
with b3:
    btn_params = st.button("⚙️", use_container_width=True, help="Parâmetros")
with b4:
    btn_manual = st.button("📖", use_container_width=True, help="Manual do Gestor")

# ============================================================
# AVISO — Busca por Produto ignora os outros filtros
# ============================================================
if produto_busca and produto_busca.strip():
    st.markdown(
        '<div style="'
        'background-color: rgba(59,130,246,0.12); '
        'border-left: 3px solid #3B82F6; '
        'padding: 6px 12px; '
        'margin-top: 8px; '
        'border-radius: 4px; '
        'font-size: 0.85rem; '
        'color: #93C5FD;">'
        'ℹ️ <b>Busca por produto:</b> '
        'Fabricante, Departamento, Grupo, Subgrupo e Filial serão ignorados.'
        '</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# APLICA O PERFIL NA PRIMEIRA CARGA
# ============================================================
if "_ultimo_perfil_aplicado" not in st.session_state:
    _perfil = st.session_state.get("perfil_sel", "Padrão")
    if _perfil in PERFIS:
        for _chave, _valor in PERFIS[_perfil].items():
            st.session_state[_chave] = _valor
    st.session_state["_ultimo_perfil_aplicado"] = _perfil

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
                key="opcao_data",
            )
        with r1c2:
            filial_sel = st.selectbox(
                "Filial",
                ["(todas)"] + list(filiais.keys()),
                key="filial_param",
                help="Apenas visual: o motor sempre analisa todas as filiais.",
            )
        with r1c3:
            cobertura_opcao = st.selectbox(
                "Cobertura de Vendas",
                ["Para 7 dias", "Para 15 dias", "Para 30 dias",
                 "Para 2 meses", "Para 3 meses", "Para 6 meses", "Para 1 ano"],
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
            atacado_piso = st.selectbox("Atacado tem Piso?", ["Não", "Sim"], key="atacado_piso")
        with r2c4:
            atacado_reserva = st.selectbox("Atacado tem Reserva?", ["Não", "Sim"], key="atacado_reserva")

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
# PDF
# ============================================================
class HeaderFooterCanvas(canvas.Canvas):
    """Desenha cabeçalho e rodapé em todas as páginas."""

    def __init__(self, *args, **kwargs):
        self.titulo = kwargs.pop("titulo", "Relatorio de Transferencias")
        self.gerado_em = kwargs.pop("gerado_em", "")
        self.parametros_texto = kwargs.pop("parametros_texto", "") # NOVO
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

        # Centro: Parâmetros
        if self.parametros_texto:
            self.drawCentredString(w / 2, 12, self.parametros_texto)

        # Direita: Página X de Y
        self.drawRightString(w - 15, 12, f"Página {self._pageNumber} de {page_count}")

def gerar_pdf_filial(nome_filial, cod, df, nome_perfil, parametros_texto):
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
    cell_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=0)
    cell_center = ParagraphStyle('CC', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=1)
    cell_right = ParagraphStyle('CR', parent=styles['Normal'], fontSize=6.5, leading=8.5, alignment=2)
    header_style = ParagraphStyle('H', parent=styles['Normal'], fontSize=6.5, leading=8.5,
                                  fontName='Helvetica-Bold', textColor=colors.white, alignment=1)

    def _build(df_part, tipo):
        if df_part.empty:
            return Paragraph("<i>Nenhum item.</i>", cell_style)

        if tipo == "ENV":
            heads = ["#", "Pr.", "Cod", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Res.", "Ideal", "Motivo"]
            widths = [28, 34, 45, 240, 30, 138, 55, 36, 40, 36, 130]
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
            widths = [28, 34, 45, 240, 30, 138, 55, 36, 40, 36, 130]
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
            ('FONTSIZE', (0, 0), (-1, -1), 6.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
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
        titulo_cab = f"Relatorio de Reposicao - {nome_perfil} - {nome_filial.title()}"
        doc.build(
            elements,
            canvasmaker=lambda *a, **kw: HeaderFooterCanvas(
                *a, titulo=titulo_cab,
                gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), 
                parametros_texto=parametros_texto, **kw
            ),
        )
        buffer.seek(0)
        return buffer, agora

    # ============================================================
    # RESUMO DA FILIAL NO TOPO DO PDF
    # ============================================================
    env_totais = df_env[~df_env["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])]
    liq_totais = df_env[df_env["NomeFilialDestino"] == "LIQUIDAR"]
    desc_totais = df_env[df_env["NomeFilialDestino"] == "DESCONTINUAR"]

    resumo_data = [
        ["", "ENVIAR", "RECEBER", "DESCONTINUAR", "LIQUIDAR"],
        ["Itens", str(len(env_totais)), str(len(df_rec)), str(len(desc_totais)), str(len(liq_totais))],
        ["Unidades", 
         str(int(env_totais["QtdTransferir"].sum()) if not env_totais.empty else 0),
         str(int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0),
         str(int(desc_totais["QtdTransferir"].sum()) if not desc_totais.empty else 0),
         str(int(liq_totais["QtdTransferir"].sum()) if not liq_totais.empty else 0)]
    ]
    
    t_resumo = Table(resumo_data, colWidths=[70, 70, 70, 90, 70], hAlign='LEFT')
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'), # Destaca a coluna "Itens / Unidades"
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 14))
    # ============================================================
    # ============================================================
    
    # Separa as categorias para o PDF
    df_liq = df_env[df_env["NomeFilialDestino"] == "LIQUIDAR"].copy()
    df_desc = df_env[df_env["NomeFilialDestino"] == "DESCONTINUAR"].copy()
    df_env = df_env[~df_env["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])].copy()

    # ENVIAR
    if not df_env.empty:
        df_env = df_env.reset_index(drop=True)
        df_env.insert(0, "#", range(1, len(df_env) + 1))
        df_env["Qtd Ideal"] = df_env["IdealDestino"] if cod == 5 else df_env["IdealOrigem"]
        df_env["Prioridade"] = df_env["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>ENVIAR</b>", filial_style))
        elements.append(_build(df_env, "ENV"))
        elements.append(Spacer(1, 14))

    # RECEBER
    if not df_rec.empty:
        df_rec = df_rec.reset_index(drop=True)
        df_rec.insert(0, "#", range(1, len(df_rec) + 1))
        df_rec["Qtd Ideal"] = df_rec["IdealDestino"]
        df_rec["Prioridade"] = df_rec["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>RECEBER</b>", filial_style))
        elements.append(_build(df_rec, "REC"))
        elements.append(Spacer(1, 14))

    # DESCONTINUAR
    if not df_desc.empty:
        df_desc = df_desc.reset_index(drop=True)
        df_desc.insert(0, "#", range(1, len(df_desc) + 1))
        df_desc["Prioridade"] = df_desc["Prioridade"].map(PRIO_TXT).fillna("-")
        df_desc["Qtd Ideal"] = 0
        df_desc["NomeFilialDestino"] = df_desc["NomeFilialOrigem"] # Item 4: Destino é a própria filial
        elements.append(Paragraph("<b>DESCONTINUAR</b>", filial_style)) # Item 2: Título limpo
        elements.append(_build(df_desc, "ENV"))
        elements.append(Spacer(1, 14))

    # LIQUIDAR
    if not df_liq.empty:
        df_liq = df_liq.reset_index(drop=True)
        df_liq.insert(0, "#", range(1, len(df_liq) + 1))
        df_liq["Prioridade"] = df_liq["Prioridade"].map(PRIO_TXT).fillna("-")
        df_liq["Qtd Ideal"] = 0
        df_liq["NomeFilialDestino"] = df_liq["NomeFilialOrigem"] # Item 4: Destino é a própria filial
        elements.append(Paragraph("<b>LIQUIDAR</b>", filial_style)) # Item 3: Título limpo
        elements.append(_build(df_liq, "ENV"))

    # Gera
    agora = agora_br()
    titulo_cab = f"Relatorio de Reposicao - {nome_perfil} - {nome_filial.title()}"
    doc.build(
        elements,
        canvasmaker=lambda *a, **kw: HeaderFooterCanvas(
            *a, titulo=titulo_cab,
            gerado_em=agora.strftime('%d/%m/%Y %H:%M:%S'), 
            parametros_texto=parametros_texto, **kw
        ),
    )
    buffer.seek(0)
    return buffer, agora

# ============================================================
# CONSULTAR
# ============================================================
if btn_consultar:
    # Regra 1: se o campo Produto estiver preenchido, ele é EXCLUSIVO.
    # Regra 2: o campo Filial é apenas visual — o motor sempre analisa todas
    #          as filiais para poder decidir quem doa e quem recebe.
    produto_preenchido = bool(produto_busca and produto_busca.strip())

    if produto_preenchido:
        fabricante_filtro   = ""
        departamento_filtro = ""
        grupo_filtro        = ""
        subgrupo_filtro     = ""
    else:
        fabricante_filtro   = "" if fabricante_sel == "(todos)" else fabricantes[fabricante_sel]
        departamento_filtro = "" if depto_sel == "(todos)" else departamentos[depto_sel]
        grupo_filtro        = "" if grupo_sel == "(todos)" else grupos[grupo_sel]
        subgrupo_filtro     = "" if subgrupo_sel == "(todos)" else subgrupos[subgrupo_sel]

    # Validação: Filial NÃO conta como filtro obrigatório (é só visual).
    nenhum_filtro = (
        not produto_preenchido
        and not fabricante_filtro
        and not departamento_filtro
        and not grupo_filtro
        and not subgrupo_filtro
    )

    if nenhum_filtro:
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
                    filial="",   # sempre todas as filiais (Filial é só visual)
                    produto=produto_busca,
                )
                st.session_state["df_base"] = df_base

            with st.spinner("⏳ Calculando sugestões..."):
                df_transito = carregar_transf_em_transito(
                    data_referencia=data_ref.strftime("%Y-%m-%d"),
                    dias_transito=dias_transito,
                )

                df_recebidas = carregar_transf_recebidas_recentes(
                    data_referencia=data_ref.strftime("%Y-%m-%d"),
                    dias_reposicao=anti_gangorra,
                )

                df_transf = gerar_sugestoes(
                    df_base,
                    df_transito=df_transito,
                    df_recebidas_recentes=df_recebidas,
                    cobertura_alvo=cobertura,
                    lead_time=lead_time,
                    piso_exposicao=piso,
                    reserva_pct=reserva,
                    atacado_tem_piso=(atacado_piso == "Sim"),
                    atacado_tem_reserva=(atacado_reserva == "Sim"),
                )
                st.session_state["df_transf"] = df_transf
                st.session_state["df_base_n"] = len(df_base)
        except Exception as e:
            st.error(f"❌ Erro: {e}")


# ============================================================
# RESULTADO
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]

    if df.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        nomes_todos = ["ATACADO", "ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE"]
        codigos = {"ATACADO": 5, "ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4}

        # Filial é apenas visual: filtra quais abas serão exibidas.
        # Exceção: quando o Produto está preenchido, Filial também é ignorado
        # (mostra todas as 5 abas).
        produto_preenchido = bool(produto_busca and produto_busca.strip())
        if filial_sel != "(todas)" and not produto_preenchido:
            cod_sel = int(filiais[filial_sel])
            nomes = [n for n in nomes_todos if codigos[n] == cod_sel]
        else:
            nomes = nomes_todos

        tabs = st.tabs(nomes)
        for tab, nome in zip(tabs, nomes):
            cod = codigos[nome]
            with tab:
                # Filtra as filiais base
                df_env_all = df[df["CodigoFilialOrigem"] == cod].copy().reset_index(drop=True)
                df_rec = df[df["CodigoFilialDestino"] == cod].copy().reset_index(drop=True)

                # Separa as categorias antecipadamente
                df_liq = df_env_all[df_env_all["NomeFilialDestino"] == "LIQUIDAR"].copy().reset_index(drop=True)
                df_desc = df_env_all[df_env_all["NomeFilialDestino"] == "DESCONTINUAR"].copy().reset_index(drop=True)
                df_env = df_env_all[~df_env_all["NomeFilialDestino"].isin(["LIQUIDAR", "DESCONTINUAR"])].copy().reset_index(drop=True)

                # ---- MÉTRICAS E BOTÃO PDF NA MESMA LINHA ----
                m1, m2, m3, m4, m5, m6, m7, m8, m9 = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1.5])
                
                m1.metric("📤 Enviar (itens)", len(df_env))
                m2.metric("📤 Enviar (un)", int(df_env["QtdTransferir"].sum()) if not df_env.empty else 0)
                
                m3.metric("📥 Receber (itens)", len(df_rec))
                m4.metric("📥 Receber (un)", int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0)
                
                m5.metric("🔥 Liquidar (itens)", len(df_liq))
                m6.metric("🔥 Liquidar (un)", int(df_liq["QtdTransferir"].sum()) if not df_liq.empty else 0)
                
                m7.metric("⏸️ Desc. (itens)", len(df_desc))
                m8.metric("⏸️ Desc. (un)", int(df_desc["QtdTransferir"].sum()) if not df_desc.empty else 0)

                with m9:
                    st.write("")
                    # Chave estável: filial + impressão digital do conteúdo real
                    _h = hashlib.md5(
                        pd.util.hash_pandas_object(df, index=True).values.tobytes()
                    ).hexdigest()[:10]
                    cache_key = f"pdf_cache_{cod}_{_h}"

                    if cache_key not in st.session_state:
                        try:
                            # Monta a string com os parâmetros atuais
                            parametros_str = (
                                f"Cob: {cobertura}d | Lead: {lead_time}d | Res: {reserva}% | "
                                f"Piso: {piso} | Quarentena: {anti_gangorra}d | Trânsito: {dias_transito}d"
                            )
                            
                            pdf_bytes, agora = gerar_pdf_filial(
                                nome, cod, df, 
                                st.session_state.get("perfil_sel", "Padrão"), 
                                parametros_str
                            )
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
                               "NomeFilialDestino", "QtdTransferir", "ReservaOrigem", "Qtd Ideal", "Motivo"]]
                    dfe.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante",
                                   "Destino", "Qtd Transf.", "Reserva", "Qtd Ideal", "Motivo"]
                    styler_e = dfe.style.set_properties(subset=["Qtd Transf.", "Reserva", "Qtd Ideal"], **{"text-align": "right"})
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
                    dfr["Dias p/ Zerar"] = dfr["DiasAteZerarDestino"].apply(lambda x: 0 if pd.isna(x) or x is None else int(x)).astype(int)
                    dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante",
                               "NomeFilialOrigem", "QtdTransferir", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]]
                    dfr.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante",
                                   "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfr) * 36 + 42))
                    st.dataframe(dfr, use_container_width=True, hide_index=True, height=h)

                # ---- DESCONTINUAR ----
                st.markdown('<div class="secao-titulo">⏸️ DESCONTINUAR</div>', unsafe_allow_html=True)
                if df_desc.empty:
                    st.caption("Nenhum produto para descontinuar")
                else:
                    dfd = df_desc.copy()
                    dfd.insert(0, "#", range(1, len(dfd) + 1))
                    dfd["Prioridade"] = dfd["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfd = dfd[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "QtdTransferir", "IdealOrigem", "Motivo"]]
                    dfd.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Desc.", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfd) * 36 + 42))
                    st.dataframe(dfd, use_container_width=True, hide_index=True, height=h)

                # ---- LIQUIDAR ----
                st.markdown('<div class="secao-titulo">🔥 LIQUIDAR</div>', unsafe_allow_html=True)
                if df_liq.empty:
                    st.caption("Nenhum produto para liquidar")
                else:
                    dfi = df_liq.copy()
                    dfi.insert(0, "#", range(1, len(dfi) + 1))
                    dfi["Prioridade"] = dfi["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfi = dfi[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante", "QtdTransferir", "IdealOrigem", "Motivo"]]
                    dfi.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Liq.", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfi) * 36 + 42))
                    st.dataframe(dfi, use_container_width=True, hide_index=True, height=h)
                    


if btn_manual:
    st.session_state["view"] = "manual"
    st.rerun()