import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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
            font-size: 1.6rem;
            font-weight: bold;
            text-align: center;
            margin-top: 0;
            margin-bottom: 18px;
            color: #FAFAFA;
        }
        .info-linha {
            text-align: center;
            font-size: 0.95rem;
            color: #E2E8F0;
            padding: 10px;
            background-color: #1E293B;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #22C55E;
        }
        .secao-titulo {
            font-size: 1.1rem;
            font-weight: bold;
            padding: 8px 0;
            margin-top: 10px;
            margin-bottom: 8px;
            border-bottom: 2px solid #334155;
        }
        div[data-testid="stButton"] button {
            width: 100% !important;
            padding: 4px 2px !important;
        }
        div[data-testid="stDownloadButton"] button {
            width: 100% !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem;
            padding: 6px 12px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.4rem;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO (sem emoji)
# ============================================================
st.markdown('<div class="titulo-pagina">PB Transferência</div>', unsafe_allow_html=True)


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
# FILTROS + BOTÕES
# ============================================================
hoje = date.today()

c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(
    [1.1, 1.2, 2.2, 1.6, 1.6, 1.6, 0.4, 0.4, 0.4]
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
    st.write("")
    btn_consultar = st.button("🔍", type="primary", use_container_width=True, help="Consultar")

with c8:
    st.write("")
    btn_limpar = st.button("🧹", use_container_width=True, help="Limpar filtros")

with c9:
    st.write("")
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
    for k in ["df_base", "df_transf"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


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
        except Exception as e:
            st.error(f"❌ Erro: {e}")


# ============================================================
# PDF
# ============================================================
def gerar_pdf(nome_filial, df_env, df_rec):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=15, leftMargin=15, topMargin=20, bottomMargin=20,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        fontSize=14, leading=16, alignment=1,
    )
    sub_style = ParagraphStyle(
        'SubStyle', parent=styles['Normal'],
        fontSize=8, leading=10, alignment=1, textColor=colors.HexColor('#475569'),
    )
    cell_style = ParagraphStyle(
        'CellText', parent=styles['Normal'], fontSize=7, leading=9,
    )
    header_style = ParagraphStyle(
        'HeaderStyle', parent=styles['Normal'],
        fontSize=7, leading=9, fontName='Helvetica-Bold',
        textColor=colors.white, alignment=1,
    )

    elements.append(Paragraph(f"<b>Relatorio de Transferencias - {nome_filial}</b>", title_style))
    elements.append(Paragraph(
        f"Gerado em {date.today().strftime('%d/%m/%Y')} | "
        f"Enviar: {len(df_env)} itens ({int(df_env['QtdTransferir'].sum()) if not df_env.empty else 0} un) | "
        f"Receber: {len(df_rec)} itens ({int(df_rec['QtdTransferir'].sum()) if not df_rec.empty else 0} un)",
        sub_style
    ))
    elements.append(Spacer(1, 12))

    def _build_table(df, cols, header_titles, col_widths):
        if df.empty:
            return Paragraph("<i>Nenhum item.</i>", cell_style)
        data = [[Paragraph(h, header_style) for h in header_titles]]
        for _, row in df.iterrows():
            r = []
            for col in cols:
                v = row[col]
                if pd.isna(v):
                    v = ""
                elif isinstance(v, float) and v.is_integer():
                    v = int(v)
                r.append(Paragraph(str(v), cell_style))
            data.append(r)
        t = Table(data, colWidths=col_widths, repeatRows=1)
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

    elements.append(Paragraph("<b>ENVIAR</b>", styles['Heading3']))
    cols_env = ["#", "Prioridade", "Produto", "Destino", "Qtd Transf.", "Reserva", "Qtd Ideal", "Motivo"]
    elements.append(_build_table(
        df_env, cols_env,
        ["#", "Pr.", "Produto", "Destino", "Qtd", "Reserva", "Ideal", "Motivo"],
        [25, 25, 200, 70, 45, 50, 45, 250]
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>RECEBER</b>", styles['Heading3']))
    cols_rec = ["#", "Prioridade", "Produto", "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
    elements.append(_build_table(
        df_rec, cols_rec,
        ["#", "Pr.", "Produto", "Origem", "Qtd", "Dias", "Ideal", "Motivo"],
        [25, 25, 200, 70, 45, 50, 45, 250]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ============================================================
# RENDER RESULTADO
# ============================================================
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]

    if df.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        # ---- LINHA INFORMATIVA ----
        base_n = st.session_state.get("df_base_n", 0)
        qtd_env = int(df["QtdTransferir"].sum())
        qtd_rec = int(df["QtdTransferir"].sum())
        n_filiais = df["NomeFilialDestino"].nunique()

        st.markdown(
            f'<div class="info-linha">✅ Produtos: <b>{base_n}</b> '
            f'| Sugestões: <b>{len(df)}</b> '
            f'| Qtd Enviar: <b>{qtd_env}</b> '
            f'| Qtd Receber: <b>{qtd_rec}</b> '
            f'| <b>{n_filiais}</b> filiais</div>',
            unsafe_allow_html=True,
        )

        # ---- ABAS ----
        nomes = ["ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE", "ATACADO"]
        codigos = {"ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4, "ATACADO": 5}

        tabs = st.tabs(nomes)
        for tab, nome in zip(tabs, nomes):
            cod = codigos[nome]
            with tab:
                df_env = df[df["CodigoFilialOrigem"] == cod].copy()
                df_rec = df[df["CodigoFilialDestino"] == cod].copy()

                # ---- MÉTRICAS DA FILIAL ----
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📤 Enviar (itens)", len(df_env))
                m2.metric("📤 Enviar (un)", int(df_env["QtdTransferir"].sum()) if not df_env.empty else 0)
                m3.metric("📥 Receber (itens)", len(df_rec))
                m4.metric("📥 Receber (un)", int(df_rec["QtdTransferir"].sum()) if not df_rec.empty else 0)

                # ---- PDF ----
                col_pdf, _ = st.columns([1, 5])
                with col_pdf:
                    if not df_env.empty or not df_rec.empty:
                        # Adiciona contador
                        df_env_pdf = df_env.copy().reset_index(drop=True)
                        df_env_pdf.insert(0, "#", range(1, len(df_env_pdf) + 1))
                        df_rec_pdf = df_rec.copy().reset_index(drop=True)
                        df_rec_pdf.insert(0, "#", range(1, len(df_rec_pdf) + 1))

                        # Qtd Ideal conforme modo
                        if modo_env == "Destino":
                            df_env_pdf["Qtd Ideal"] = df_env_pdf["IdealDestino"]
                            df_rec_pdf["Qtd Ideal"] = df_rec_pdf["IdealDestino"]
                        else:
                            df_env_pdf["Qtd Ideal"] = df_env_pdf["IdealOrigem"]
                            df_rec_pdf["Qtd Ideal"] = df_rec_pdf["IdealOrigem"]

                        pdf_bytes = gerar_pdf(nome, df_env_pdf, df_rec_pdf)
                        st.download_button(
                            "📄 Gerar PDF da Filial",
                            data=pdf_bytes,
                            file_name=f"transferencia_{nome.lower()}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                # ---- TABELAS ENVIAR / RECEBER (empilhadas) ----
                cor_prio = {1: "background-color: #FFE5E5", 2: "background-color: #FFF3E0", 3: "background-color: #FFFDE7"}

                # ENVIAR
                st.markdown('<div class="secao-titulo">📤 ENVIAR</div>', unsafe_allow_html=True)
                if df_env.empty:
                    st.caption("Nada a enviar")
                else:
                    dfe = df_env.copy().reset_index(drop=True)
                    dfe.insert(0, "#", range(1, len(dfe) + 1))
                    dfe["Qtd Ideal"] = dfe["IdealDestino"] if modo_env == "Destino" else dfe["IdealOrigem"]
                    dfe["Prioridade"] = dfe["Prioridade"].apply(
                        lambda p: {1: "🔴", 2: "🟠", 3: "🟡"}.get(p, "⚪")
                    )
                    cols_show = ["#", "Prioridade", "CodigoProduto", "Produto", "Fabricante",
                                 "Embalagem", "NomeFilialDestino", "QtdTransferir",
                                 "ReservaOrigem", "Qtd Ideal", "Motivo"]
                    dfe = dfe[cols_show]
                    dfe.columns = ["#", "Pr.", "Cod", "Produto", "Fabricante",
                                   "Emb.", "Destino", "Qtd Transf.", "Reserva", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfe, use_container_width=True, hide_index=True, height=380)

                # RECEBER
                st.markdown('<div class="secao-titulo">📥 RECEBER</div>', unsafe_allow_html=True)
                if df_rec.empty:
                    st.caption("Nada a receber")
                else:
                    dfr = df_rec.copy().reset_index(drop=True)
                    dfr.insert(0, "#", range(1, len(dfr) + 1))
                    dfr["Qtd Ideal"] = dfr["IdealDestino"] if modo_env == "Destino" else dfr["IdealOrigem"]
                    dfr["Prioridade"] = dfr["Prioridade"].apply(
                        lambda p: {1: "🔴", 2: "🟠", 3: "🟡"}.get(p, "⚪")
                    )
                    cols_show = ["#", "Prioridade", "CodigoProduto", "Produto", "Fabricante",
                                 "Embalagem", "NomeFilialOrigem", "QtdTransferir",
                                 "DiasAteZerarDestino", "Qtd Ideal", "Motivo"]
                    dfr = dfr[cols_show]
                    dfr.columns = ["#", "Pr.", "Cod", "Produto", "Fabricante",
                                   "Emb.", "Origem", "Qtd Transf.", "Dias p/ Zerar", "Qtd Ideal", "Motivo"]
                    st.dataframe(dfr, use_container_width=True, hide_index=True, height=380)