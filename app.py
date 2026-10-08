import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from src.db import (
    carregar_filiais, carregar_fabricantes,
    carregar_departamentos, carregar_grupos, carregar_subgrupos,
)
from src.base import carregar_base
from src.transferencia import gerar_sugestoes


# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="PB Transferência", layout="wide", page_icon="📊")


# ============================================================
# CSS
# ============================================================
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

        /* Centralizar abas */
        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.88rem;
            padding: 8px 18px;
        }

        /* Centralizar métricas */
        [data-testid="stMetric"] {
            text-align: center;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem;
            text-align: center;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.82rem;
            text-align: center;
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
    </style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO
# ============================================================
st.markdown('<div class="titulo-pagina">PB Transferência</div>', unsafe_allow_html=True)


# ============================================================
# MAPEAMENTO DE PRIORIDADE
# ============================================================
PRIO_TXT = {1: "Crítica", 2: "Alta", 3: "Normal"}


# ============================================================
# CARREGAR LISTAS
# ============================================================
filiais = carregar_filiais()
fabricantes = carregar_fabricantes()
departamentos = carregar_departamentos()
grupos = carregar_grupos()
subgrupos = carregar_subgrupos()


# ============================================================
# ESTADO
# ============================================================
if "show_params" not in st.session_state:
    st.session_state.show_params = False


# ============================================================
# FILTROS + BOTÕES (alinhados verticalmente pela base)
# ============================================================
hoje = date.today()

c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns(
    [1.1, 1.2, 2.2, 1.6, 1.6, 1.6, 0.45, 0.45, 0.45, 0.45],
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
    # Placeholder — será preenchido com o botão PDF após o resultado
    pdf_placeholder = st.empty()

with c10:
    btn_params = st.button("⚙️", use_container_width=True, help="Parâmetros")


# ============================================================
# PARÂMETROS (toggle)
# ============================================================
if btn_params:
    st.session_state.show_params = not st.session_state.show_params

if st.session_state.show_params:
    with st.container(border=True):
        p1, p2, p3, p4, p5, p6, p7, p8 = st.columns(8)
        with p1: anti_gangorra = st.number_input("Anti-gangorra (dias)", 0, 90, 15, key="p_ag")
        with p2: cobertura = st.number_input("Cobertura Alvo (dias)", 1, 120, 30, key="p_cob")
        with p3: piso = st.number_input("Piso Exposição (un)", 0, 50, 0, key="p_piso")
        with p4: lead_time = st.number_input("Lead Time (dias)", 0, 30, 5, key="p_lead")
        with p5: reserva = st.number_input("Reserva Origem (%)", 0, 100, 25, key="p_res")
        with p6: lookback = st.number_input("Máx. Lookback (dias)", 30, 730, 365, key="p_look")
        with p7: modo_env = st.selectbox("Qtd Ideal ENV", ["Destino", "Origem"], key="p_modo")
        with p8: atacado_piso = st.selectbox("Atacado tem Piso?", ["Não", "Sim"], key="p_atac")
else:
    anti_gangorra = 15
    cobertura = 30
    piso = 0
    lead_time = 5
    reserva = 25
    lookback = 365
    modo_env = "Destino"
    atacado_piso = "Não"


# ============================================================
# LIMPAR
# ============================================================
if btn_limpar:
    for k in ["df_base", "df_transf", "df_base_n", "modo_env_usado"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ============================================================
# PDF (gera todas as filiais)
# ============================================================
def gerar_pdf_completo(df, modo):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=15, leftMargin=15, topMargin=20, bottomMargin=20,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=14, leading=16, alignment=1)
    filial_style = ParagraphStyle('F', parent=styles['Heading2'], fontSize=12, leading=14,
                                  textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=6)
    sub_style = ParagraphStyle('S', parent=styles['Normal'], fontSize=8, leading=10,
                               alignment=1, textColor=colors.HexColor('#475569'))
    cell_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=7, leading=9)
    header_style = ParagraphStyle('H', parent=styles['Normal'], fontSize=7, leading=9,
                                  fontName='Helvetica-Bold', textColor=colors.white, alignment=1)

    elements.append(Paragraph("<b>Relatorio de Transferencias</b>", title_style))
    elements.append(Paragraph(f"Gerado em {date.today().strftime('%d/%m/%Y')}", sub_style))
    elements.append(Spacer(1, 12))

    def _build(df_part, tipo):
        if df_part.empty:
            return Paragraph("<i>Nenhum item.</i>", cell_style)

        if tipo == "ENV":
            heads = ["#", "Pr.", "Produto", "Destino", "Qtd", "Reserva", "Ideal", "Motivo"]
            widths = [25, 45, 200, 70, 45, 50, 45, 250]
            mapper = lambda r: [
                r["#"], r["Prioridade"], r["Produto"], r["NomeFilialDestino"],
                int(r["QtdTransferir"]), int(r["ReservaOrigem"]),
                int(r["Qtd Ideal"]), r["Motivo"],
            ]
        else:
            heads = ["#", "Pr.", "Produto", "Origem", "Qtd", "Dias", "Ideal", "Motivo"]
            widths = [25, 45, 200, 70, 45, 50, 45, 250]
            mapper = lambda r: [
                r["#"], r["Prioridade"], r["Produto"], r["NomeFilialOrigem"],
                int(r["QtdTransferir"]),
                int(r["DiasAteZerarDestino"]) if pd.notna(r["DiasAteZerarDestino"]) else "-",
                int(r["Qtd Ideal"]), r["Motivo"],
            ]

        data = [[Paragraph(h, header_style) for h in heads]]
        for _, row in df_part.iterrows():
            vals = []
            for v in mapper(row):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    v = ""
                elif isinstance(v, float) and v.is_integer():
                    v = int(v)
                vals.append(Paragraph(str(v), cell_style))
            data.append(vals)

        t = Table(data, colWidths=widths, repeatRows=1)
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

    codigos = {"ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4, "ATACADO": 5}
    primeiro = True

    for nome_filial, cod in codigos.items():
        df_env = df[df["CodigoFilialOrigem"] == cod].copy()
        df_rec = df[df["CodigoFilialDestino"] == cod].copy()

        if df_env.empty and df_rec.empty:
            continue

        if not primeiro:
            elements.append(PageBreak())
        primeiro = False

        elements.append(Paragraph(f"<b>{nome_filial}</b>", filial_style))

        df_env = df_env.reset_index(drop=True)
        df_env.insert(0, "#", range(1, len(df_env) + 1))
        df_env["Qtd Ideal"] = df_env["IdealDestino"] if modo == "Destino" else df_env["IdealOrigem"]
        df_env["Prioridade"] = df_env["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>ENVIAR</b>", styles['Heading3']))
        elements.append(_build(df_env, "ENV"))
        elements.append(Spacer(1, 12))

        df_rec = df_rec.reset_index(drop=True)
        df_rec.insert(0, "#", range(1, len(df_rec) + 1))
        df_rec["Qtd Ideal"] = df_rec["IdealDestino"] if modo == "Destino" else df_rec["IdealOrigem"]
        df_rec["Prioridade"] = df_rec["Prioridade"].map(PRIO_TXT).fillna("-")
        elements.append(Paragraph("<b>RECEBER</b>", styles['Heading3']))
        elements.append(_build(df_rec, "REC"))

    doc.build(elements)
    buffer.seek(0)
    return buffer


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
                )
                st.session_state["df_transf"] = df_transf
                st.session_state["df_base_n"] = len(df_base)
                st.session_state["modo_env_usado"] = modo_env
        except Exception as e:
            st.error(f"❌ Erro: {e}")


# ============================================================
# PREENCHE PDF PLACEHOLDER (após consulta)
# ============================================================
if "df_transf" in st.session_state and not st.session_state["df_transf"].empty:
    with pdf_placeholder.container():
        try:
            pdf_bytes = gerar_pdf_completo(
                st.session_state["df_transf"],
                st.session_state.get("modo_env_usado", "Destino"),
            )
            st.download_button(
                "📄",
                data=pdf_bytes,
                file_name=f"transferencias_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Gerar PDF completo",
            )
        except Exception as e:
            st.button("📄", disabled=True, use_container_width=True, help=f"Erro: {e}")
else:
    with pdf_placeholder.container():
        st.button("📄", disabled=True, use_container_width=True, help="Faça uma consulta primeiro")


# ============================================================
# RESULTADO — ABAS
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]

    if df.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        modo = st.session_state.get("modo_env_usado", "Destino")
        nomes = ["ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE", "ATACADO"]
        codigos = {"ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4, "ATACADO": 5}

        tabs = st.tabs(nomes)
        for tab, nome in zip(tabs, nomes):
            cod = codigos[nome]
            with tab:
                df_env = df[df["CodigoFilialOrigem"] == cod].copy().reset_index(drop=True)
                df_rec = df[df["CodigoFilialDestino"] == cod].copy().reset_index(drop=True)

                # MÉTRICAS
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📤 Enviar (itens)", len(df_env))
                m2.metric("📤 Enviar (un)", int(df_env["QtdTransferir"].sum()) if not df_env.empty else 0)
                m3.metric("📥 Receber (itens)", len(df_rec))
                m4.metric("📥 Receber (un)", int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0)

                # ENVIAR
                st.markdown('<div class="secao-titulo">📤 ENVIAR</div>', unsafe_allow_html=True)
                if df_env.empty:
                    st.caption("Nada a enviar")
                else:
                    dfe = df_env.copy()
                    dfe.insert(0, "#", range(1, len(dfe) + 1))
                    dfe["Qtd Ideal"] = dfe["IdealDestino"] if modo == "Destino" else dfe["IdealOrigem"]
                    dfe["Prioridade"] = dfe["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfe = dfe[["#", "Prioridade", "CodigoProduto", "Produto", "Fabricante",
                               "Embalagem", "NomeFilialDestino", "QtdTransferir",
                               "ReservaOrigem", "Qtd Ideal", "Motivo"]]
                    dfe.columns = ["#", "Prioridade", "Cod", "Produto", "Fabricante",
                                   "Emb.", "Destino", "Qtd Transf.", "Reserva", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfe) * 36 + 42))
                    st.dataframe(dfe, use_container_width=True, hide_index=True, height=h)

                # RECEBER
                st.markdown('<div class="secao-titulo">📥 RECEBER</div>', unsafe_allow_html=True)
                if df_rec.empty:
                    st.caption("Nada a receber")
                else:
                    dfr = df_rec.copy()
                    dfr.insert(0, "#", range(1, len(dfr) + 1))
                    dfr["Qtd Ideal"] = dfr["IdealDestino"] if modo == "Destino" else dfr["IdealOrigem"]
                    dfr["Prioridade"] = dfr["Prioridade"].map(PRIO_TXT).fillna("-")
                    dfr = dfr[["#", "Prioridade", "CodigoProduto", "Produto", "Fabricante",
                               "Embalagem", "NomeFilialOrigem", "QtdTransferir",
                               "DiasAteZerarDestino", "Qtd Ideal", "Motivo"]]
                    dfr.columns = ["#", "Prioridade", "Cod", "Produto", "Fabricante",
                                   "Emb.", "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
                    h = min(420, max(120, len(dfr) * 36 + 42))
                    st.dataframe(dfr, use_container_width=True, hide_index=True, height=h)