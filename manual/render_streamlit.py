"""Renderiza o Manual do Gestor dentro do Streamlit."""

import streamlit as st
from io import BytesIO

from gerar_manual import gerar as gerar_pdf_manual


@st.cache_data
def _gerar_manual_pdf_cached() -> bytes | None:
    """Gera o PDF do manual em memória (cacheado)."""
    try:
        buffer = BytesIO()
        gerar_pdf_manual(buffer=buffer)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"⚠️ Erro ao gerar PDF: {e}")
        return None


def render_tabela(headers, rows):
    """Renderiza uma tabela Markdown limpa, sem índices e ajustada ao conteúdo."""
    md = "| " + " | ".join(headers) + " |\n"
    md += "|" + "|".join(["---"] * len(headers)) + "|\n"
    for row in rows:
        row_clean = [str(cell).replace("\n", " ") for cell in row]
        md += "| " + " | ".join(row_clean) + " |\n"
    st.markdown(md)


def render_manual() -> None:
    """Renderiza o manual do gestor."""

    # CSS atualizado: Abas sem fundo azul, apenas underline padrão
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap !important; 
                justify-content: center !important;
                gap: 6px !important;
                padding-bottom: 10px;
            }
            .stTabs [data-baseweb="tab"] {
                flex-grow: 1 !important;
                justify-content: center !important;
                padding: 6px 12px !important;
                font-size: 0.85rem !important;
            }
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
            st.download_button(
                "⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name="Manual_Reposicao_Gestor.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("⬇️ Baixar PDF", disabled=True, use_container_width=True)

    st.markdown("# 📖 Manual do Gestor")
    st.markdown("**Reposição de Produtos** — Sistema de sugestão de transferências entre filiais")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "🏁 Introdução", "🧠 Como Pensa", "🚪 Primeiro Acesso", "🎛️ Filtros & Parâmetros",
        "📊 Resultado", "📅 Rotina", "🔧 Ajustes", "❓ FAQ", "📚 Glossário", "🛠️ Casos Práticos"
    ])

    # ---------------- ABA 1 - Introdução ----------------
    with tab1:
        st.header("1.1 Por que este sistema existe")
        st.markdown(
            "Imagine o dia a dia de uma rede com **5 filiais** e **milhares de produtos**. "
            "Todos os dias você precisa responder:\n\n"
            "- ❓ **Quanto** mandar de cada produto para cada loja?\n"
            "- ❓ **Quando** mandar?\n"
            "- ❓ Se uma loja tem **excesso** e outra tem **falta**, como fazer essa troca?\n"
            "- ❓ Como evitar que o Atacado mande produto demais para uma loja e de menos para outra?\n"
            "- ❓ Como não deixar prateleiras vazias sem inflar o estoque?"
        )
        st.info(
            "**Antes deste sistema**: as decisões eram tomadas por telefone, "
            "planilhas manuais e intuição. Levava horas por semana e gerava erros frequentes.\n\n"
            "**Com este sistema**: o motor faz essas perguntas para TODOS os produtos "
            "em segundos, e ainda prioriza os mais urgentes."
        )

        st.subheader("1.2 O que o sistema faz")
        st.markdown(
            "✅ **1. Analisa** histórico de vendas\n\n"
            "✅ **2. Calcula** o estoque ideal de cada filial\n\n"
            "✅ **3. Identifica** excesso (doador) e falta (receptor)\n\n"
            "✅ **4. Sugere** qual filial envia, para quem, e quanto\n\n"
            "✅ **5. Sugere Compras** caso falte produto na rede inteira\n\n"
            "✅ **6. Prioriza** por urgência\n\n"
            "✅ **7. Gera** relatórios em PDF por filial"
        )

        st.subheader("1.3 O que o sistema NÃO faz")
        st.markdown(
            "- ❌ **Não substitui sua decisão** — ele sugere, você aprova\n"
            "- ❌ **Não executa transferências** — você cria a ordem no ERP\n"
            "- ❌ **Não altera dados** no banco — é somente leitura\n"
            "- ❌ **Não substitui o bom senso** — sempre confira o Motivo antes de aprovar"
        )

        st.subheader("1.4 Em 1 parágrafo")
        st.success(
            "O sistema olha os últimos **365 dias** de cada produto, calcula o "
            "**ritmo de venda** de cada filial, define **quanto cada uma precisa "
            "ter em estoque** para cobrir **30 dias** de venda + **10 dias** de "
            "transporte, e cruza tudo: quem tem demais é sugerido como **doador**, "
            "quem tem de menos é sugerido como **receptor**. Se ninguém tiver o produto, "
            "o sistema sugere a **Compra**. O **Atacado** entra como hub principal."
        )

    # ---------------- ABA 2 - Como Pensa ----------------
    with tab2:
        st.header("2.1 A metáfora da caixa d'água")
        st.markdown("Imagine que cada filial é uma **caixa d'água**. O sistema tenta manter cada caixa no nível ideal:")
        render_tabela(["Nível", "Estado"], [
            ["100% (Ideal)", "Tudo perfeito"],
            ["80%", "Atenção"],
            ["40%", "Crítico"],
            ["0% (Ruptura)", "Urgente"]
        ])

        st.header("2.2 Estoque Ideal")
        st.code("Estoque Ideal = max(Piso Exposição, Velocidade Período x (Cobertura + Tempo de Transporte))", language="text")
        st.warning(
            "**Atenção:** O **Piso Exposição** garante um mínimo na prateleira. "
            "A velocidade usada é a **Período** (vendas / dias corridos)."
        )

        st.header("2.3 O que acontece quando a rede inteira está sem estoque? (COMPRAR)")
        st.markdown(
            "Se a filial precisa do produto e não há em nenhuma outra filial para transferir, "
            "o sistema vai sugerir a **COMPRA**.\n\n"
            "**Como é calculada a quantidade?**\n"
            "- O sistema soma o que as lojas precisam (ideal).\n"
            "- Subtrai o que as lojas já têm e o que já vai chegar (Em Trânsito).\n"
            "- A diferença é a **Qtd Sugerida** para compra."
        )

        st.header("2.4 A Matriz de Proximidade")
        st.markdown("Quem ajuda quem:")
        render_tabela(["Destino", "Ordem de prioridade dos doadores"], [
            ["Alecrim", "1º Atacado, 2º Via Direta, 3º Zona Sul, 4º Zona Norte"],
            ["Via Direta", "1º Atacado, 2º Alecrim, 3º Zona Sul"],
            ["Zona Sul", "1º Atacado, 2º Alecrim, 3º Via Direta"],
            ["Zona Norte", "1º Atacado, 2º Alecrim"],
            ["Atacado", "Nunca recebe"]
        ])

        st.header("2.5 Regra do Mínimo de 5 unidades (MOQ)")
        st.markdown(
            "O motor **ignora transferências menores que 5 unidades** em todas as regras. "
            "Abaixo desse volume, o custo logístico da transferência supera o ganho de disponibilidade."
        )

    # ---------------- ABA 3 - Primeiro Acesso ----------------
    with tab3:
        st.header("3.1 Como abrir")
        st.markdown(
            "1. Abra o navegador (Chrome, Edge ou Firefox)\n"
            "2. Digite: `https://pb-reposicao.streamlit.app`\n"
            "3. Pressione Enter"
        )
        st.info(
            "**Primeira vez do dia:** Se o app estiver 'dormindo', você verá o botão "
            "**'Yes, get this app back up!'**. Clique e aguarde ~30 segundos."
        )

        st.header("3.2 Mapa visual da tela")
        render_tabela(["Área", "O que tem"], [
            ["Topo", "Título 'Reposição de Produtos'"],
            ["Linha 1", "6 filtros: Perfil, Fabricante, Depto, Grupo, Subgrupo, Produto"],
            ["Botões", "Consultar, Limpar, Parâmetros, Manual e Gerar PDF"],
            ["Cards", "Enviar, Receber, Liquidar, Desc., Comprar (Itens e Unid)"],
            ["Resultados", "Aparece após consultar (5 abas por filial)"]
        ])

    # ---------------- ABA 4 - Filtros e Parâmetros ----------------
    with tab4:
        st.header("4.1 Perfil de Análise")
        st.markdown(
            "O **Perfil de Análise** configura automaticamente os 9 parâmetros do motor. "
            "Um mesmo produto pode ser analisado com perfis diferentes, dependendo do seu momento de vida."
        )

        st.markdown("**Perfis disponíveis:**")
        render_tabela(["Perfil", "Quando usar", "Exemplo do Dia a Dia"], [
            ["Padrão", "Uso geral", "Materiais contínuos."],
            ["Lançamento", "Produto novo/coleção", "Nova coleção de tecidos."],
            ["Classe A", "Maior faturamento", "Fita adesiva básica, papel kraft."],
            ["Alto Giro", "Venda rápida constante", "Bexigas de aniversário."],
            ["Sazonal Longo", "Campanhas longas (Natal/Carnaval)", "Artigos de Natal em novembro."],
            ["Sazonal Curto", "Pico explosivo (Páscoa/Mães/Halloween)", "Máscaras de Halloween."],
            ["Baixo Giro", "Produtos encalhados", "Tecido de seda (1 rolo/mês)."],
            ["Liquidação", "Fim de ciclo / queima", "Itens de Halloween na 1ª sem. nov."]
        ])

        st.subheader("Os 9 parâmetros de cada perfil (tabela técnica)")
        render_tabela(
            ["Parâmetro", "Padrão", "Lanç.", "Classe A", "Alto Giro", "Saz.Longo", "Saz.Curto", "Baixo Giro", "Liquid."],
            [
                ["Período análise", "1 ano", "30d", "3m", "3m", "2m", "30d", "1 ano", "6m"],
                ["Cobertura", "30d", "30d", "15d", "15d", "30d", "15d", "30d", "7d"],
                ["Lead time", "10", "10", "7", "7", "10", "7", "10", "10"],
                ["Piso Exposição", "0", "5", "10", "5", "5", "3", "3", "0"],
                ["Reserva Origem", "25%", "0%", "25%", "15%", "15%", "5%", "30%", "0%"],
                ["Atacado tem Piso?", "Não", "Não", "Não", "Não", "Não", "Não", "Não", "Não"],
                ["Atacado tem Reserva?", "Não", "Não", "Não", "Não", "Não", "Não", "Não", "Não"],
                ["Reposição Recente", "15", "7", "7", "7", "7", "5", "20", "30"],
                ["Dias em Trânsito", "10", "10", "7", "7", "10", "7", "10", "10"],
                ["Mín. Compra", "Não", "Não", "Sim", "Não", "Sim", "Não", "Não", "Não"]
            ]
        )

        st.header("4.2 Parâmetros em detalhe")
        st.markdown(
            "**Atacado tem Mínimo p/ Compra?** Se 'Sim', o sistema só sugere comprar se a "
            "necessidade for maior ou igual ao Piso Exposição. Isso evita comprar volumes "
            "irrisórios de fornecedores."
        )

    # ---------------- ABA 5 - Resultado ----------------
    with tab5:
        st.header("5.1 Como ler os cards")
        st.markdown(
            "Acima de cada aba, você verá 5 cards: **Enviar, Receber, Liquidar, Desc. e Comprar**. "
            "Cada um mostra a quantidade de **Itens** (linhas) e **Unid** (soma das quantidades)."
        )

        st.header("5.2 As colunas essenciais")
        render_tabela(["Coluna", "Significado"], [
            ["Prioridade", "Crítica / Alta / Normal"],
            ["Em Trânsito", "Quantidade que já está a caminho para a filial"],
            ["Qtd Transf.", "Quanto transferir ou comprar"],
            ["Qtd Ideal", "Estoque ideal da filial"],
            ["Motivo", "Por que foi sugerido"]
        ])

        st.header("5.3 Motivos possíveis")
        render_tabela(["Motivo", "Significado"], [
            ["SEM ESTOQUE", "Loja zerada e sem produto em trânsito (Alarme Vermelho)"],
            ["AGUARDANDO TRANSFERENCIA", "Produto já está a caminho (caminhão na estrada)"],
            ["RECEBIDO RECENTEMENTE", "Recebeu nos últimos N dias (quarentena)"],
            ["URGENTE - zera hoje", "Vai zerar em menos de 1 dia"],
            ["URGENTE - zera em N dias", "Vai zerar em breve (1 a 6 dias)"],
            ["ESTOQUE COMPLEMENTAR", "Falta na rede, mas ainda há um pouco de estoque nas lojas"]
        ])

        st.header("5.4 Ações de Fim de Linha (Liquidar e Descontinuar)")
        st.markdown(
            "Quando um produto não vende em nenhuma filial, transferi-lo gera custo de frete. "
            "O sistema cria seções exclusivas de ação comercial para não poluir a tela de transferências."
        )

    # ---------------- ABA 6 - Rotina ----------------
    with tab6:
        st.header("6.1 Segunda-feira (10 min)")
        st.markdown(
            "1. Abra o app\n"
            "2. Escolha o Perfil\n"
            "3. Escolha um Fabricante\n"
            "4. Clique em Consultar\n"
            "5. Filtre por Prioridade = Crítica"
        )
        st.header("6.2 Terça a Quinta (ação)")
        st.markdown(
            "1. Veja o **Motivo**\n"
            "2. Confirme a **Qtd Transf.**\n"
            "3. Gere o PDF\n"
            "4. Crie a ordem no ERP\n"
            "5. Se houver itens em **COMPRAR**, envie a lista para o time de Compras."
        )

    # ---------------- ABA 7 - Ajustes ----------------
    with tab7:
        st.header("Cenários e Soluções")
        st.subheader("Cenário A — Sugerindo transferência demais")
        st.markdown("- Aumentar Reposição Recente (15 -> 30)\n- Aumentar Reserva Origem (25% -> 40%)\n- Diminuir Cobertura (30 -> 15)")
        
        st.subheader("Cenário B — Sugerindo transferência de menos")
        st.markdown("- Diminuir Reposição Recente (15 -> 7)\n- Diminuir Reserva Origem (25% -> 15%)\n- Aumentar Cobertura (30 -> 45)")

    # ---------------- ABA 8 - FAQ ----------------
    with tab8:
        st.header("Perguntas frequentes")
        faq = [
            ("Por que meu produto está na aba COMPRAR?", "Porque a rede inteira está sem estoque suficiente. Transferir não resolve, precisamos comprar do fornecedor."),
            ("O que significa 'ESTOQUE COMPLEMENTAR'?", "Significa que a rede tem um pouco do produto, mas não o suficiente para o período ideal. O sistema sugere comprar apenas o complemento."),
            ("O que é 'Em Trânsito'?", "É a quantidade que já foi despachada pela origem e está no caminhão a caminho do destino."),
            ("Por que o Motivo difere do Em Trânsito?", "Se a loja tem -100 de saldo e 20 em trânsito, o motivo será SEM ESTOQUE (pois o caminhão não salva). Se tem -10 e 20 em trânsito, o motivo será AGUARDANDO TRANSFERENCIA."),
            ("O sistema compra sozinho?", "Não. Ele apenas sugere a lista. A compra é feita pelo ERP."),
        ]
        for i, (pergunta, resposta) in enumerate(faq, 1):
            with st.expander(f"{i}. {pergunta}"):
                st.markdown(resposta)

    # ---------------- ABA 9 - Glossário ----------------
    with tab9:
        st.header("Glossário")
        render_tabela(["Termo", "Definição"], [
            ["Estoque Ideal", "max(Piso, VelocPeriodo x (Cob + Lead))"],
            ["Em Trânsito", "Quantidade já despachada, a caminho da filial"],
            ["ESTOQUE COMPLEMENTAR", "Motivo de compra quando há estoque na rede, mas abaixo do ideal"],
            ["MOQ", "Minimum Order Quantity - mínimo de 5 un por transferência ou compra"],
            ["Saldo Ajustado", "SaldoProvavel + QtdEmTransito"],
        ])

    # ---------------- ABA 10 - Casos Práticos ----------------
    with tab10:
        st.header("Casos Práticos")
        
        with st.expander("Caso 1 — Produto em falta crítica (RECEBER)"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Motivo"], [
                ["1", "Crítica", "562351", "FITA ADESIVA", "Atacado", "85", "URGENTE - zera hoje"]
            ])
            st.markdown("**Ação:** gerar PDF, enviar para o Atacado, criar ordem no ERP.")

        with st.expander("Caso 2 — Produto que precisa ser COMPRADO"):
            st.markdown("**Aba Alecrim (COMPRAR):**")
            render_tabela(["#", "Cod", "Produto", "Velocidade", "Ideal", "Sugestão", "Motivo"], [
                ["1", "563551", "FITA ADESIVA", "0.58", "23", "2", "ESTOQUE COMPLEMENTAR"],
                ["2", "627885", "FITA CREPE", "0.33", "13", "13", "SEM ESTOQUE"]
            ])
            st.markdown("**Ação:** enviar a lista para o time de Compras do Atacado.")

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")