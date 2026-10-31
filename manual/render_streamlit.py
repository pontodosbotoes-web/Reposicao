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

    st.markdown("# 📖 Manual do Gestor (Guia Definitivo)")
    st.markdown("**Reposição de Produtos** — A ciência e a prática da operação.")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "1. O Problema", "2. A Ciência", "3. Acesso", "4. Filtros", "5. Parâmetros",
        "6. Resultados", "7. Motivos", "8. Rotina", "9. FAQ", "10. Casos Práticos"
    ])

    # ---------------- ABA 1 - O Problema ----------------
    with tab1:
        st.header("Por que este sistema existe?")
        st.markdown(
            "Se você está começando hoje, imagine a dor de cabeça de gerenciar **5 lojas** e **milhares de produtos**. "
            "Todos os dias você precisa decidir: **Quanto mandar para cada loja? De onde tirar? Se ninguém tiver, quanto comprar?**"
        )
        
        st.subheader("O Custo da Ruptura (Prateleira Vazia)")
        render_box(
            "No varejo, falhas de abastecimento causam até <b>42% de perda de vendas</b>. O cliente quer comprar, não encontra, e leva o dinheiro para o concorrente.<br/><br/>"
            "<b>O que o sistema faz:</b> Calcula o Estoque Ideal para que a prateleira nunca fique vazia.",
            cor_borda="#EF4444"
        )

        st.subheader("O Custo do Excesso (Dinheiro Parado)")
        render_box(
            "Ter mais produto do que vende significa capital imobilizado, custo de armazenagem e perda por validade ou obsolescência.<br/><br/>"
            "<b>O que o sistema faz:</b> Move o produto de onde ele está parado para onde ele está girando.",
            cor_borda="#F59E0B"
        )

        st.subheader("A Rotina Manual vs. O Sistema")
        st.markdown(
            "**Antes:** 4 a 6 horas por semana montando planilhas, ligando para as filiais e decidindo por intuição.\n\n"
            "**Com o sistema:** O motor faz o cálculo para milhares de produtos em segundos. Você foca apenas em aprovar o que é crítico."
        )

    # ---------------- ABA 2 - A Ciência ----------------
    with tab2:
        st.header("A Ciência por trás do Motor")
        st.markdown("O sistema não foi inventado. Ele aplica 3 práticas consolidadas no varejo mundial:")

        st.subheader("1. DRP (Distribution Requirements Planning)")
        st.markdown(
            "**O que é:** Planejamento baseado no consumo real.\n"
            "**Onde entra:** É a base do Estoque Ideal.\n"
            "**Quem usa:** Walmart, Carrefour, Pão de Açúcar."
        )
        st.subheader("2. IST (Inter-Store Transfers)")
        st.markdown(
            "**O que é:** Transferências entre lojas (Matriz de Proximidade).\n"
            "**Quem usa:** Zara (ciclo de 2 semanas), H&M.\n"
            "**Por que é bom:** É mais rápido e barato transferir de uma loja vizinha do que esperar o CD."
        )
        st.subheader("3. MEIO (Multi-Echelon Inventory Optimization)")
        st.markdown(
            "**O que é:** Otimização com Hub Central (Atacado).\n"
            "**Quem usa:** Amazon (reduziu capital de giro em até 27%).\n"
            "**Por que é bom:** O Atacado consolida o estoque e amortiza as variações das lojas."
        )

        st.subheader("A Cascata de Decisão (Waterfall)")
        st.markdown(
            "Para evitar que um produto apareça em várias abas ao mesmo tempo, o motor usa a lógica de **eliminação em cascata**.\n\n"
            "1. O motor verifica primeiro se alguma loja **nunca recebeu** o produto (DEMONSTRAR).\n"
            "2. Se não houver lojas nessa situação, ele verifica a **velocidade da rede** (DESCONTINUAR ou LIQUIDAR).\n"
            "3. Se o produto for saudável, ele gera o fluxo normal (ENVIAR/RECEBER/COMPRAR).\n\n"
            "**Inovações recentes:**\n"
            "* **Produtos Pesáveis (KG/MTS):** O sistema lê a flag `ProdutoPesavel` do ERP e envia apenas 0,1 (100g) para teste no DEMONSTRAR.\n"
            "* **Trava de Recompra:** Se o Atacado tem estoque e as lojas têm falta, o produto vai para ENVIAR/RECEBER (não vai para DESC/LIQ).\n"
            "* **Trava de Compra:** A aba COMPRAR só sugere itens se a filial tiver velocidade local >= 0.10."
        )

    # ---------------- ABA 3 - Acesso ----------------
    with tab3:
        st.header("Primeiro Acesso")
        st.markdown(
            "1. Abra o navegador (Chrome, Edge, Firefox).\n"
            "2. Digite: `https://pb-reposicao.streamlit.app`\n"
            "3. Pressione Enter.\n\n"
            "**Se o app estiver dormindo:** Clique em `Yes, get this app back up!` e aguarde 30 segundos."
        )
        st.subheader("Mapa da Tela")
        st.markdown(
            "- **Topo:** Filtros (Perfil, Fabricante, etc.).\n"
            "- **Meio:** Botões de Ação (Consultar, Parâmetros).\n"
            "- **Baixo:** 6 Cards (Enviar, Receber, Demonstrar, Desc., Liquidar, Comprar) e as tabelas."
        )

    # ---------------- ABA 4 - Filtros ----------------
    with tab4:
        st.header("Dicionário de Filtros")
        render_tabela(["Filtro", "O que faz"], [
            ["Perfil de Análise", "Configura os 9 parâmetros automaticamente."],
            ["Fabricante", "Filtra produtos de uma marca."],
            ["Departamento", "Categoria macro (ex: FITAS)."],
            ["Grupo", "Subdivisão da categoria."],
            ["Subgrupo", "Nível mais específico."],
            ["Produto", "Busca por nome, código ou referência. **Atenção:** Ignora os outros filtros se usado."]
        ])
        st.info(
            "**Busca Avançada:** Digite `CAIXA QUADRADA` (espaço = E) ou `CAPA, CAPUZ` (vírgula = OU). "
            "Se você usar o campo Produto, o sistema busca em **toda a rede** e ignora a Filial."
        )

    # ---------------- ABA 5 - Parâmetros ----------------
    with tab5:
        st.header("Dicionário de Parâmetros (Tela ⚙️)")
        
        st.subheader("O Perfil de Análise")
        st.markdown("O perfil preenche os 9 parâmetros automaticamente. Se você errar o perfil, o cálculo será desastroso.")
        with st.expander("Qual perfil escolher? (MUITO IMPORTANTE)"):
            render_tabela(["Perfil", "Motivo de usar", "O que acontece se errar?"], [
                ["Padrão", "Produtos normais.", "Se usar em sazonal, acumula estoque."],
                ["Lançamento", "Sem histórico de venda.", "Se usar Padrão, não manda nada (prateleira vazia)."],
                ["Classe A", "Campeão de vendas.", "Se usar Baixo Giro, deixa faltar o principal."],
                ["Alto Giro", "Venda rápida.", "Se usar Padrão, zera antes do caminhão chegar."],
                ["Sazonal Longo", "Natal, Carnaval.", "Se usar Curto, acaba no meio da campanha."],
                ["Sazonal Curto", "Páscoa, Halloween.", "Se usar Longo, sobra estoque após a data."],
                ["Baixo Giro", "Encalhados.", "Se usar Classe A, compra uma montanha."],
                ["Liquidação", "Fim de ciclo.", "Se usar Padrão, transfere produto morto (gasta frete)."],
            ])

        st.subheader("Entendendo os Parâmetros no Detalhe")
        
        parametros_dict = {
            "1. Período de Análise": "Janela de tempo (1 ano).",
            "2. Filial": "Apenas visual (filtra abas).",
            "3. Cobertura de Vendas": "Dias de estoque (30d). Aumentar = Ideal maior = mais pedidos.",
            "4. Tempo de Transporte": "Dias de viagem (10d). Se subestimar, zera antes do produto chegar.",
            "5. Piso Exposição": "Mínimo na prateleira (0). Evita prateleira vazia em produtos de baixo giro.",
            "6. Reserva Origem": "% que a origem guarda (25%). Evita que ela zere após doar.",
            "7 e 8. Atacado tem Piso/Reserva?": "O Atacado é hub. Deixe 'Não'.",
            "9. Reposição Recente": "Quarentena (15d). Bloqueia pedidos duplicados.",
            "10. Dias em Trânsito": "Janela do que está a caminho (10d).",
            "11. Atacado tem Mínimo p/ Compra?": "Se Sim, usa o Piso como MOQ de compra."
        }
        
        for titulo, descricao in parametros_dict.items():
            st.markdown(f"**{titulo}:** {descricao}")

    # ---------------- ABA 6 - Resultados ----------------
    with tab6:
        st.header("Lendo os Resultados")
        
        st.subheader("O Grande Segredo: Ideal vs. Quantidade de Transferência")
        st.markdown(
            "Essa é a maior dúvida:\n"
            "- **Qtd Ideal:** É a quantidade para satisfazer o período.\n"
            "- **Qtd Transf.:** É a ação de hoje. O que falta para cobrir o saldo mais o necessário para o período.\n\n"
            "*Exemplo:* Ideal 100, Saldo 40. Transfere 60. O Ideal é o necessário para o período; a transferência cobre o saldo atual e a necessidade projetada."
        )

        st.subheader("Os 6 Cards e a Hierarquia")
        st.markdown(
            "O motor não mistura as sugestões. Se o item cai na primeira regra, ele é ignorado nas seguintes:"
        )
        render_tabela(["Etapa", "Seção", "O que significa?"], [
            ["1º", "🎯 DEMONSTRAR", "Loja sem histórico. Envia 5 un (ou 0,1 kg) da doadora com excedente para teste."],
            ["2º", "⏸️ DESCONTINUAR", "Venda fraca na rede (0 < vel < 0.1). Deve sair do mix."],
            ["3º", "🔥 LIQUIDAR", "Venda zero na rede. Deve ser promovido."],
            ["4º", "📤 ENVIAR", "A filial tem demais e vai doar."],
            ["4º", "📥 RECEBER", "A filial tem falta e vai receber."],
            ["4º", "🛒 COMPRAR", "Ninguém na rede tem o suficiente. Precisa comprar do fornecedor."]
        ])
        st.info("💡 **Por que não há coluna de Prioridade em DEMONSTRAR, DESC e LIQUIDAR?** Essas são ações absolutas. A prioridade só se aplica ao fluxo de transferências normais (ENVIAR/RECEBER).")

        st.subheader("O que é o 'Retorno Financeiro' (R$)?")
        st.markdown(
            "Na aba **COMPRAR**, você verá a coluna **Retorno Fin. (R$)**. Ela mostra qual será o lucro bruto "
            "gerado por aquela compra.\n\n"
            "**Fórmula:** `(Preço de Venda - Custo Unitário) × Quantidade Sugerida`.\n\n"
            "Isso ajuda você a priorizar. Se o orçamento está curto, compre primeiro os itens que trazem mais retorno. "
            "No Atacado, esse valor é a **soma** do retorno de todas as lojas, mostrando o impacto total no caixa da rede."
        )

    # ---------------- ABA 7 - Motivos ----------------
    with tab7:
        st.header("O Livro dos Motivos")
        st.markdown("O Motivo é o coração do sistema. Ele diz exatamente o que está acontecendo.")
        
        motivos = {
            "SEM REGISTRO NA FILIAL": "A loja nunca recebeu o item e o sistema está enviando a quantidade inicial (5 un ou 0,1 kg) para iniciar o histórico.",
            "SEM ESTOQUE": "A loja está zerada e não há nada no caminhão nem na rede.",
            "AGUARDANDO TRANSFERENCIA": "A loja tem falta, **MAS** já tem um caminhão cheio de produto indo para lá.",
            "RECEBIDO RECENTEMENTE": "A loja recebeu produto há poucos dias. Está em quarentena.",
            "URGENTE - zera hoje": "O estoque acaba em menos de 24 horas.",
            "URGENTE - zera em N dias": "Vai acabar logo.",
            "Origem parada, destino vendendo": "A doadora quase não vende, mas a receptora vende muito.",
            "Alta rotacao no destino": "A receptora vende o dobro da doadora.",
            "Maior giro no destino": "A receptora vende 1.5x mais que a doadora.",
            "Reposicao de ciclo": "Fluxo normal.",
            "ESTOQUE COMPLEMENTAR": "Motivo de compra. A rede tem um pouco, mas não o suficiente.",
            "ESTOQUE PARADO": "Liquidar. A velocidade de venda é zero na rede.",
            "FIM DE CICLO NA REDE": "Descontinuar. O produto vende muito pouco em todas as lojas."
        }
        for k, v in motivos.items():
            st.markdown(f"**{k}:** {v}")

    # ---------------- ABA 8 - Rotina ----------------
    with tab8:
        st.header("Sua Rotina Semanal")
        st.markdown(
            "**Segunda (10 min):**\n"
            "1. Escolha o Perfil e o Fabricante.\n"
            "2. Clique em Consultar.\n"
            "3. Filtre por Prioridade Crítica.\n\n"
            "**Terça a Quinta (Ação):**\n"
            "1. Leia o Motivo. 2. Confirme a Qtd. 3. Gere o PDF. 4. Crie a ordem no ERP.\n"
            "5. Se houver itens em COMPRAR, envie para o time de Compras.\n"
            "6. Se houver itens em DEMONSTRAR, avise o gerente da loja para fazer merchandising ou incluir o produto no mix.\n\n"
            "**Sexta (10 min):**\n"
            "1. Reabra o app e compare com a semana anterior."
        )

    # ---------------- ABA 9 - FAQ ----------------
    with tab9:
        st.header("Perguntas Frequentes")
        faq = [
            ("A sugestão parece errada. O que faço?", "1. Leia o Motivo. 2. Confira o Saldo e o Em Trânsito. 3. Verifique se o produto não caiu em DESC ou LIQ por causa da velocidade da rede."),
            ("Por que um produto não aparece em mais de uma aba?", "O sistema usa cascata. Se ele foi para DEMONSTRAR, não vai para ENVIAR. Se foi para DESC, não vai para LIQ. Isso evita duplicidade."),
            ("Como o sistema trata produtos vendidos a granel (KG, MTS)?", "Ele lê a flag `ProdutoPesavel` do ERP. Para esses itens, o teste inicial no DEMONSTRAR é de 0,1 (100g) e o limite para descontinuar é mais flexível."),
            ("O que é a Trava de Recompra?", "Se o Atacado tem estoque novo e as lojas têm falta, o sistema força a distribuição (ENVIAR/RECEBER) em vez de liquidar o produto."),
            ("O que é a Trava de Compra?", "A aba COMPRAR só sugere itens se a filial tiver uma velocidade local mínima. Isso evita comprar produtos que a loja não vende."),
            ("O que significa um saldo negativo (ex: -60)?", "É um erro de movimentação. O motor trata esse saldo como ZERO para não pedir quantidades absurdas."),
            ("Como ajustar se estiver sugerindo MUITO?", "Aumente a Reposição Recente ou a Reserva Origem. Diminua a Cobertura."),
            ("Como ajustar se estiver sugerindo POUCO?", "Diminua a Reposição Recente ou a Reserva Origem. Aumente a Cobertura."),
            ("O Atacado compra para ele mesmo?", "Sim. Se ele estiver abaixo do Ideal, a aba COMPRAR dele sugere a compra para repor o CD."),
            ("Isso substitui o ERP?", "Não. É uma ferramenta de decisão. A execução continua no ERP.")
        ]
        for i, (pergunta, resposta) in enumerate(faq, 1):
            with st.expander(f"{i}. {pergunta}"):
                st.markdown(resposta)

    # ---------------- ABA 10 - Casos Práticos ----------------
    with tab10:
        st.header("Casos Práticos Reais")
        
        with st.expander("Cenário 1: Produto em falta crítica (RECEBER)"):
            st.markdown(
                "**O que vejo:** Fita Adesiva, 85 un, Motivo: `URGENTE - zera hoje`.\n"
                "**Ação:** Gere o PDF, envie para o Atacado, crie a ordem no ERP."
            )

        with st.expander("Cenário 2: A rede inteira está sem estoque (COMPRAR)"):
            st.markdown(
                "**O que vejo:** Fita Crepe na aba COMPRAR do Atacado, Sugestão 50, Retorno Financeiro R$ 25.00.\n"
                "**Ação:** Nenhuma loja tem. Envie a lista para o time de Compras."
            )

        with st.expander("Cenário 3: O produto já está a caminho (AGUARDANDO)"):
            st.markdown(
                "**O que vejo:** Papel Kraft, Em Trânsito: 20 un.\n"
                "**Ação:** O caminhão já saiu. Apenas aguarde a entrega."
            )

        with st.expander("Cenário 4: Loja nunca recebeu o produto (DEMONSTRAR)"):
            st.markdown(
                "**O que vejo:** Papel Colorido, Origem: ATACADO, Destino: ZONA NORTE, Qtd: 5, Motivo: `SEM REGISTRO NA FILIAL`.\n"
                "**Ação:** O produto vende em outras lojas, mas a Zona Norte nunca recebeu. O sistema está sugerindo enviar 5 un do Atacado para iniciar o histórico."
            )

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")