import streamlit as st
import pandas as pd
from datetime import date, datetime
from zoneinfo import ZoneInfo
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from src.db import (
    carregar_filiais, carregar_fabricantes,
    carregar_departamentos, carregar_grupos, carregar_subgrupos,
)
from src.base import carregar_base
from src.transferencia import gerar_sugestoes


st.set_page_config(page_title="PB Transferência", layout="wide", page_icon="📊")


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


st.markdown('<div class="titulo-pagina">PB Transferência</div>', unsafe_allow_html=True)


PRIO_TXT = {1: "Crítica", 2: "Alta", 3: "Normal"}

try:
    TZ_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    from datetime import timezone, timedelta
    TZ_BR = timezone(timedelta(hours=-3))


def agora_br():
    return datetime.now(TZ_BR)


# ============================================================
# CARREGAR LISTAS
# ============================================================
filiais = carregar_filiais()
fabricantes = carregar_fabricantes()
departamentos = carregar_departamentos()
grupos = carregar_grupos()
subgrupos = carregar_subgrupos()


if "show_params" not in st.session_state:
    st.session_state.show_params = False


# ============================================================
# FILTROS + BOTÕES
# ============================================================
hoje = date.today()

c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(
    [1.1, 1.2, 2.2, 1.6, 1.6, 1.6, 0.5, 0.5, 0.5],
    vertical_alignment="bottom",
)

with c1:
    data_ref = st.date_input("Data de Referência", value=hoje, format="DD/MM/YYYY", key="data_ref")

with c2:
    filial_sel = st.selectbox("Filial", ["(todas)"] + list(filiais.keys()), key="filial_sel")

with c3:
    fabricante_sel = st.selectbox("Fabricante", ["(todos)"] + list(fabricantes.keys()), key="fabricante_sel")

with c4:
    depto_sel = st.selectbox("Departamento", ["(todos)"] + list(departamentos.keys()), key="depto_sel")

with c5:
    grupo_sel = st.selectbox("Grupo", ["(todos)"] + list(grupos.keys()), key="grupo_sel")

with c6:
    subgrupo_sel = st.selectbox("Subgrupo", ["(todos)"] + list(subgrupos.keys()), key="subgrupo_sel")

with c7:
    btn_consultar = st.button("🔍", type="primary", use_container_width=True, help="Consultar")

with c8:
    btn_limpar = st.button("🧹", use_container_width=True, help="Limpar filtros")

with c9:
    btn_params = st.button("⚙️", use_container_width=True, help="Parâmetros")


# ============================================================
# PARÂMETROS
# ============================================================
if btn_params:
    st.session_state.show_params = not st.session_state.show_params

if st.session_state.show_params:
    with st.container(border=True):
        # Linha 1
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1: anti_gangorra = st.number_input("Anti-gangorra (dias)", 0, 90, 15, key="p_ag")
        with r1c2: cobertura = st.number_input("Cobertura Alvo (dias)", 1, 120, 30, key="p_cob")
        with r1c3: piso = st.number_input("Piso Exposição (un)", 0, 50, 0, key="p_piso")
        with r1c4: lead_time = st.number_input("Lead Time (dias)", 0, 30, 10, key="p_lead")

        # Linha 2
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1: reserva = st.number_input("Reserva Origem (%)", 0, 100, 25, key="p_res")
        with r2c2: lookback = st.number_input("Máx. Lookback (dias)", 30, 730, 365, key="p_look")
        with r2c3: atacado_piso = st.selectbox("Atacado tem Piso?", ["Não", "Sim"], key="p_atac")
        with r2c4: atacado_reserva = st.selectbox("Atacado tem Reserva?", ["Não", "Sim"], key="p_atac_res")
else:
    anti_gangorra = 15
    cobertura = 30
    piso = 0
    lead_time = 10
    reserva = 25
    lookback = 365
    atacado_piso = "Não"
    atacado_reserva = "Não"


# ============================================================
# LIMPAR
# ============================================================
if btn_limpar:
    for k in ["df_base", "df_transf", "df_base_n"]:
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
            heads = ["#", "Pr.", "Produto", "Emb.", "Fabricante", "Destino", "Qtd", "Reserva", "Ideal", "Motivo"]
            widths = [22, 42, 320, 35, 80, 60, 40, 42, 40, 110]
            mapper = lambda r: [
                (r["#"], "C"), (r["Prioridade"], "C"), (r["Produto"], "C"),
                (r["Embalagem"], "C"), (r["Fabricante"], "C"),
                (r["NomeFilialDestino"], "C"),
                (int(r["QtdTransferir"]), "R"),
                (int(r["ReservaOrigem"]), "R"),
                (int(r["Qtd Ideal"]), "R"),
                (r["Motivo"], "C"),
            ]
        else:
            heads = ["#", "Pr.", "Produto", "Emb.", "Fabricante", "Origem", "Qtd", "Dias", "Ideal", "Motivo"]
            widths = [22, 42, 320, 35, 80, 60, 40, 42, 40, 110]
            mapper = lambda r: [
                (r["#"], "C"), (r["Prioridade"], "C"), (r["Produto"], "C"),
                (r["Embalagem"], "C"), (r["Fabricante"], "C"),
                (r["NomeFilialOrigem"], "C"),
                (int(r["QtdTransferir"]), "R"),
                (int(r["DiasAteZerarDestino"]) if pd.notna(r["DiasAteZerarDestino"]) else "-", "R"),
                (int(r["Qtd Ideal"]), "R"),
                (r["Motivo"], "C"),
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
        titulo_cab = f"Relatorio de Transferencias - {nome_filial.title()}"
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
    titulo_cab = f"Relatorio de Transferencias - {nome_filial.title()}"
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
    if (filial_sel == "(todas)" and fabricante_sel == "(todos)"
        and depto_sel == "(todos)" and grupo_sel == "(todos)"
        and subgrupo_sel == "(todos)"):
        st.warning("⚠️ Escolha pelo menos 1 filtro.")
    else:
        try:
            with st.spinner("⏳ Construindo Base..."):
                df_base = carregar_base(
                    data_referencia=data_ref.strftime("%Y-%m-%d"),
                    max_lookback=lookback,
                    fabricante="" if fabricante_sel == "(todos)" else fabricantes[fabricante_sel],
                    departamento="" if depto_sel == "(todos)" else departamentos[depto_sel],
                    grupo="" if grupo_sel == "(todos)" else grupos[grupo_sel],
                    subgrupo="" if subgrupo_sel == "(todos)" else subgrupos[subgrupo_sel],
                    filial="" if filial_sel == "(todas)" else filiais[filial_sel],
                )
                st.session_state["df_base"] = df_base

            with st.spinner("⏳ Calculando sugestões..."):
                df_transf = gerar_sugestoes(
                    df_base,
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
        nomes = ["ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE", "ATACADO"]
        codigos = {"ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4, "ATACADO": 5}

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
                    # Cache do PDF pela chave filial + hash dos dados
                    cache_key = f"pdf_cache_{cod}_{len(df_env)}_{len(df_rec)}"
                    
                    if cache_key not in st.session_state:
                        try:
                            pdf_bytes, agora = gerar_pdf_filial(nome, cod, df)
                            st.session_state[cache_key] = (pdf_bytes, agora)
                        except Exception as e:
                            st.session_state[cache_key] = (None, None)
                    
                    pdf_bytes, agora = st.session_state[cache_key]
                    
                    if pdf_bytes is not None:
                        nome_file = nome.title().replace(" ", "")
                        file_name = f"Transferencia {nome_file} {agora.strftime('%Y%m%d %H%M%S')}.pdf"
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
                    h = min(420, max(120, len(dfe) * 36 + 42))
                    st.dataframe(dfe, use_container_width=True, hide_index=True, height=h)

                # ---- RECEBER ----
                st.markdown('<div class="secao-titulo">📥 RECEBER</div>', unsafe_allow_html=True)
                if df_rec.empty:
                    st.caption("Nada a receber")
                else:
                    dfr = df_rec.copy()
                    dfr.insert(0, "#", range(1, len(dfr) + 1))
                    dfr["Qtd Ideal"] = dfr["IdealDestino"]
                    dfr["Prioridade"] = dfr["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Embalagem", "Fabricante",
                               "NomeFilialOrigem", "QtdTransferir",
                               "DiasAteZerarDestino", "Qtd Ideal", "Motivo"]]
                    dfr.columns = ["#", "Prioridade", "Cod", "Produto", "Emb.", "Fabricante",
                                   "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfr) * 36 + 42))
                    st.dataframe(dfr, use_container_width=True, hide_index=True, height=h)