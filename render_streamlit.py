"""Renderiza o Manual do Gestor dentro do Streamlit."""

import streamlit as st
from io import BytesIO

from gerar_manual import gerar as gerar_pdf_manual


@st.cache_data
def _gerar_manual_pdf_cached() -> bytes | None:
    try:
        buffer = BytesIO()
        gerar_pdf_manual(buffer=buffer)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"⚠️ Erro ao gerar PDF: {e}")
        return None


def render_tabela(headers, rows):
    md = "| " + " | ".join(headers) + " |\n"
    md += "|" + "|".join(["---"] * len(headers)) + "|\n"
    for row in rows:
        row_clean = [str(cell).replace("\n", " ") for cell in row]
        md += "| " + " | ".join(row_clean) + " |\n"
    st.markdown(md)


def render_box(texto, cor_borda="#3B82F6", cor_fundo="#1E293B"):
    html = f"""
    <div style="background-color: {cor_fundo}; border-left: 4px solid {cor_borda}; padding: 12px 16px; margin-bottom: 12px; border-radius: 4px; color: #E2E8F0;">
        {texto}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_manual() -> None:
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap !important;
                justify-content: center !important;
                gap: 8px !important;
                padding-bottom: 15px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: transparent !important;
                border: 1px solid #334155 !important; 
                border-radius: 8px !important;
                padding: 8px 16px !important;
                color: #94A3B8 !important; 
                transition: all 0.2s ease;
            }
            .stTabs [aria-selected="true"] {
                background-color: #1E293B !important; 
                border: 1px solid #3B82F6 !important; 
                color: #F8FAFC !important; 
                font-weight: 600 !important;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            }
            .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
            .stTabs [data-baseweb="tab-border"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    col_voltar, col_download, _ = st.columns([1, 1.3, 4])

    with col_voltar:
        if st.button("← Voltar", use_container_width=True, key="btn_voltar_manual"):
            st.session_state["view"] = "calculadora"
            st.rerun()

    with col_download:
        pdf_bytes = _gerar_manual_pdf_cached()
        if pdf_bytes is not None:
            st.download_button("⬇️ Baixar PDF", data=pdf_bytes, file_name="Manual_Reposicao_Gestor.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.button("⬇️ Baixar PDF", disabled=True, use_container_width=True)

    st.markdown("# 🛠️ Manual de Engenharia e Operação")
    st.markdown("**Reposição de Produtos** — Não é apenas um sistema. É a ciência do varejo aplicada.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. A Engenharia", "2. A Mecânica", "3. O Design do Painel", "4. Auditoria e Ação"
    ])

    # ---------------- ABA 1 - A Engenharia ----------------
    with tab1:
        st.header("Módulo 1: A Engenharia do Sistema")
        st.markdown(
            "Para confiar no que o sistema está sugerindo, você precisa entender as leis da física "
            "que governam o motor. Nada foi inventado; tudo vem de algoritmos consagrados."
        )

        st.subheader("A Origem Científica")
        render_box(
            "<b>1. DRP (Distribution Requirements Planning):</b> Usado por gigantes como Walmart e Carrefour. "
            "É a base do nosso <i>Estoque Ideal</i>. Ele assume que a demanda passada projeta a futura.<br/><br/>"
            "<b>2. IST (Inter-Store Transfers):</b> Adotado pela Zara. Em vez de esperar o centro de distribuição, "
            "as lojas se abastecem mutuamente. É a nossa <i>Matriz de Proximidade</i>.<br/><br/>"
            "<b>3. MEIO (Multi-Echelon Inventory Optimization):</b> A Amazon usa isso para reduzir capital de giro. "
            "O Atacado atua como um hub central (<i>Risk Pooling</i>) para amortecer as variações das lojas.",
            cor_borda="#8B5CF6"
        )

        st.subheader("A Matemática do Estoque Ideal")
        st.markdown(
            "Não usamos médias simples. Usamos a **Velocidade Período**, que dilui dias de venda e dias parados.\n\n"
            "`Estoque Ideal = Velocidade Período × (Cobertura + Tempo de Transporte)`\n\n"
            "**Por que somamos o Tempo de Transporte?** Imagine que a loja vende 5 fitas por dia e o caminhão demora 10 dias. "
            "Se você mandar 50 fitas, quando elas chegarem, a loja já terá vendido 50. Então, você precisa mandar 50 (para o caminhão) + 150 (para 30 dias de cobertura) = 200 unidades."
        )

        st.subheader("O Combate ao Efeito Chicote (P&G)")
        st.markdown(
            "A P&G estudou as fraldas Pampers e descobriu que, mesmo com vendas estáveis, os pedidos oscilavam. "
            "Isso porque cada loja pedia um pouco a mais por medo. O sistema resolve isso com a **Reposição Recente**: "
            "uma trava que impede pedidos duplicados se a loja já recebeu algo há poucos dias."
        )

    # ---------------- ABA 2 - A Mecânica ----------------
    with tab2:
        st.header("Módulo 2: A Mecânica (O Motor por Dentro)")
        st.markdown("Como o código toma decisões? Ele não chuta. Ele segue uma hierarquia de prioridades e travas.")

        st.subheader("A Matriz de Proximidade (O Grafo)")
        st.markdown(
            "O sistema usa um grafo direcionado. A Zona Sul nunca pede para a Zona Norte se o Atacado tiver. "
            "Ele segue a ordem lógica de escoamento para economizar frete. O Atacado é o nível 1 (maior volume). "
            "As lojas vizinhas são o nível 2."
        )

        st.subheader("A Regra do Mínimo de 5 unidades (MOQ)")
        st.markdown(
            "Baseado na Teoria dos Custos de Transação (Coase, 1937). O custo de mover 3 unidades (frete, separação, combustível) "
            "é maior que o benefício de ter essas 3 unidades na prateleira. O sistema simplesmente ignora transferências abaixo de 5. "
            "A Amazon faz exatamente isso entre seus Fulfillment Centers."
        )

        st.subheader("O Resgate de Saldos Negativos")
        st.markdown(
            "Você verá sugestões maiores que o Ideal (ex: Ideal 20, Transf. 80). Isso acontece quando o sistema detecta "
            "que a loja tem um saldo físico negativo (fruto de erro de inventário ou venda não baixada). A fórmula de compra/transferência "
            "é `(Ideal - Saldo)`. Se o saldo é -60, ele manda 80. O sistema está te ajudando a **resgatar** o estoque."
        )

    # ---------------- ABA 3 - O Design do Painel ----------------
    with tab3:
        st.header("Módulo 3: O Design do Painel (A Interface)")
        st.markdown(
            "A tela foi desenhada com base em Ciência Cognitiva para evitar sobrecarga. Você deve olhar para ela como um diretor."
        )

        st.subheader("Os 5 Cards Superiores")
        st.markdown(
            "Antes de ver a tabela gigante, os cards dão o **Resumo Executivo**. "
            "Se você vê 'Enviar: 26 itens', já sabe que terá trabalho. Se vê 'Comprar: 0', "
            "sabe que não precisará ligar para o fornecedor. É o seu painel de avião."
        )

        st.subheader("A Psicologia das Cores e Prioridades")
        render_box(
            "<b>🔴 Crítica (Prioridade 1):</b> O produto zera em menos de 7 dias (ou já zerou). Ação hoje.<br/><br/>"
            "<b>🟡 Alta (Prioridade 2):</b> Zera entre 7 e 14 dias. Ação nesta semana.<br/><br/>"
            "<b>🟢 Normal (Prioridade 3):</b> Fluxo regular. Ação no ciclo normal.",
            cor_borda="#EF4444"
        )

    # ---------------- ABA 4 - Auditoria e Ação ----------------
    with tab4:
        st.header("Módulo 4: Auditoria e Ação (O Gestor como Engenheiro)")
        st.markdown(
            "O sistema é seu assistente, mas você é o engenheiro-chefe. Se uma sugestão parecer absurda, use o método de auditoria."
        )

        st.subheader("Checklist de Auditoria de uma Sugestão")
        st.markdown(
            "Se a quantidade sugerida for estranha:\n"
            "1. **Verifique o Motivo:** Ele explica o porquê (ex: `AGUARDANDO TRANSFERENCIA`).\n"
            "2. **Verifique o Em Trânsito:** O sistema já está contabilizando um caminhão na estrada?\n"
            "3. **Verifique o Saldo:** É um resgate de saldo negativo?\n"
            "4. **Verifique o Perfil:** O perfil escolhido está correto para o ciclo de vida do produto?"
        )

        st.subheader("O Livro dos Motivos (Auditoria Rápida)")
        st.markdown(
            "O motivo é a string de log do motor. Ele diz exatamente qual condição foi acionada:\n\n"
            "- **SEM ESTOQUE:** Loja zerada e sem nada a caminho.\n"
            "- **AGUARDANDO TRANSFERENCIA:** Loja com falta, mas já há caminhão a caminho (a trava anti-gangorra funcionou).\n"
            "- **ESTOQUE COMPLEMENTAR:** Compra sugerida. A rede tem um pouco, mas não o ideal.\n"
            "- **RECEBIDO RECENTEMENTE:** A quarentena de 15 dias está ativa.\n"
            "- **ESTOQUE PARADO:** Velocidade zero. O motor não transferiu, ele liquidou."
        )

        st.subheader("O que fazer em cenários de erro sistêmico")
        st.markdown(
            "**Erro de Inventário (Saldo Negativo):** O sistema vai pedir 100. Você sabe que na loja só tem 10. "
            "Ação: **Ajuste o inventário físico primeiro**. Se você transferir baseado no negativo, a loja vai inflar o estoque.\n\n"
            "**Lançamento de Coleção Nova:** O motor não tem histórico (Velocidade = 0). "
            "Ação: Use o perfil de **Lançamento**. O sistema vai usar o *Piso Exposição* para forçar o envio, garantindo prateleira cheia sem dados de venda."
        )

    st.markdown("---")
    st.caption("Manual de Engenharia — Reposição de Produtos | Uso interno")