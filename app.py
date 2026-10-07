import streamlit as st
import pandas as pd
from datetime import date

from src.db import (
    carregar_filiais, carregar_fabricantes,
    carregar_departamentos, carregar_grupos, carregar_subgrupos,
)
from src.base import carregar_base
from src.transferencia import gerar_sugestoes


st.set_page_config(page_title="PB Transferência", layout="wide", page_icon="🔄")

st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        .titulo-pagina {
            font-size: 1.6rem;
            font-weight: bold;
            text-align: center;
            margin-top: 5px;
            margin-bottom: 25px;
            color: #FAFAFA;
        }
        div[data-testid="stButton"] button {
            width: 100% !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem;
            padding: 6px 12px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo-pagina">🔄 PB Transferência</div>', unsafe_allow_html=True)


# ---------- Carregar listas ----------
filiais = carregar_filiais()
fabricantes = carregar_fabricantes()
departamentos = carregar_departamentos()
grupos = carregar_grupos()
subgrupos = carregar_subgrupos()


# ---------- Filtros ----------
hoje = date.today()
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 1.4, 2.4, 1.6, 1.6, 1.6, 0.5, 0.5])

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
    btn_consultar = st.button("🔍", type="primary", use_container_width=True)

with c8:
    st.write("")
    btn_limpar = st.button("🧹", use_container_width=True)


# ---------- Parâmetros ----------
with st.expander("⚙️ Parâmetros de Transferência", expanded=False):
    p1, p2, p3, p4, p5, p6, p7, p8 = st.columns(8)
    with p1: anti_gangorra = st.number_input("Anti-gangorra (dias)", 0, 90, 15)
    with p2: cobertura = st.number_input("Cobertura Alvo (dias)", 1, 120, 30)
    with p3: piso = st.number_input("Piso Exposição (un)", 0, 50, 0)
    with p4: lead_time = st.number_input("Lead Time (dias)", 0, 30, 5)
    with p5: reserva = st.number_input("Reserva Origem (%)", 0, 100, 25)
    with p6: lookback = st.number_input("Máx. Lookback (dias)", 30, 730, 365)
    with p7: modo_env = st.selectbox("Qtd Ideal ENV", ["Destino", "Origem"])
    with p8: atacado_piso = st.selectbox("Atacado tem Piso?", ["Não", "Sim"])


# ---------- Limpar ----------
if btn_limpar:
    for k in ["df_base", "df_transf"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ---------- Consultar ----------
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

            st.success(f"✅ Base: {len(df_base)} linhas | Sugestões: {len(df_transf)}")
        except Exception as e:
            st.error(f"❌ Erro: {e}")


# ---------- Resultado ----------
if "df_transf" in st.session_state:
    df = st.session_state["df_transf"]

    if df.empty:
        st.info("Nenhuma sugestão encontrada.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Sugestões", len(df))
        m2.metric("Total (un)", f"{df['QtdTransferir'].sum():,.0f}")
        m3.metric("Filiais", df["NomeFilialDestino"].nunique())

        nomes = ["ALECRIM", "VIA DIRETA", "ZONA SUL", "ZONA NORTE", "ATACADO"]
        codigos = {"ALECRIM": 1, "VIA DIRETA": 2, "ZONA SUL": 3, "ZONA NORTE": 4, "ATACADO": 5}

        tabs = st.tabs(nomes)
        for tab, nome in zip(tabs, nomes):
            cod = codigos[nome]
            with tab:
                ce, cr = st.columns(2)

                with ce:
                    st.markdown("### 📤 ENVIAR")
                    dfe = df[df["CodigoFilialOrigem"] == cod].copy()
                    if dfe.empty:
                        st.caption("Nada a enviar")
                    else:
                        dfe["Qtd Ideal"] = dfe["IdealDestino"] if modo_env == "Destino" else dfe["IdealOrigem"]
                        st.dataframe(
                            dfe[["Prioridade", "CodigoProduto", "Produto", "Fabricante",
                                 "Embalagem", "NomeFilialDestino", "QtdTransferir",
                                 "ReservaOrigem", "Qtd Ideal", "Motivo"]],
                            use_container_width=True, hide_index=True, height=520,
                        )

                with cr:
                    st.markdown("### 📥 RECEBER")
                    dfr = df[df["CodigoFilialDestino"] == cod].copy()
                    if dfr.empty:
                        st.caption("Nada a receber")
                    else:
                        dfr["Qtd Ideal"] = dfr["IdealDestino"] if modo_env == "Destino" else dfr["IdealOrigem"]
                        st.dataframe(
                            dfr[["Prioridade", "CodigoProduto", "Produto", "Fabricante",
                                 "Embalagem", "NomeFilialOrigem", "QtdTransferir",
                                 "DiasAteZerarDestino", "Qtd Ideal", "Motivo"]],
                            use_container_width=True, hide_index=True, height=520,
                        )