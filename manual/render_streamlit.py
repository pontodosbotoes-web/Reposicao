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


def render_manual() -> None:
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap !important; justify-content: center !important; gap: 6px !important; padding-bottom: 10px; }
            .stTabs [data-baseweb="tab"] { flex-grow: 1 !important; justify-content: center !important; padding: 6px 12px !important; font-size: 0.85rem !important; }
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
    st.markdown("**Reposição de Produtos** — Tudo o que você precisa saber, do zero.")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "1. O Básico", "2. O Motor", "3. Filtros", "4. Dicionário de Parâmetros", 
        "5. Lendo os Resultados", "6. O Livro dos Motivos", "7. Cenários Reais", "8. FAQ"
    ])

    # ---------------- ABA 1 - O Básico ----------------
    with tab1:
        st.header("Para que serve este sistema?")
        st.markdown(
            "Imagine que você é o gerente de uma rede com **5 lojas** e **milhares de produtos**. "
            "Todo dia você precisa decidir:\n"
            "1. **Quanto** mandar de produto para cada loja?\n"
            "2. De onde tirar (do Atacado ou de outra loja)?\n"
            "3. Se ninguém tiver, quanto **comprar**?\n\n"
            "Fazer isso na mão é impossível. O sistema faz esse cálculo para todos os produtos em segundos. "
            "Ele é o seu **assistente inteligente**."
        )
        
        st.subheader("O que ele FAZ e o que ele NÃO FAZ")
        col1, col2 = st.columns(2)
        with col1:
            st.success(
                "✅ Analisa vendas\n\n"
                "✅ Calcula o Estoque Ideal\n\n"
                "✅ Identifica quem tem sobrando (doador) e quem tem falta (receptor)\n\n"
                "✅ Sugere Transferências e Compras\n\n"
                "✅ Gera PDF para o time executar"
            )
        with col2:
            st.error(
                "❌ Não aprova nada sozinho (você é o chefe)\n\n"
                "❌ Não faz a transferência real (isso é no ERP)\n\n"
                "❌ Não altera o banco de dados\n\n"
                "❌ Não substitui o seu bom senso (sempre leia o Motivo)"
            )

        st.subheader("Como usar o sistema em 4 passos")
        st.markdown(
            "1. Escolha o **Perfil de Análise** (ex: Padrão).\n"
            "2. Escolha o **Fabricante** (ex: ADERE).\n"
            "3. Clique em **🔍 Consultar**.\n"
            "4. Leia os resultados e clique em **📄 Gerar PDF**."
        )

    # ---------------- ABA 2 - O Motor ----------------
    with tab2:
        st.header("Como o motor pensa? (A Matemática por trás)")
        st.markdown(
            "O sistema funciona como uma **caixa d'água**. Ele quer manter o nível sempre no topo. "
            "Para isso, ele precisa saber qual é o tamanho ideal dessa caixa."
        )

        st.subheader("A Fórmula do Estoque Ideal")
        st.info(
            "**Estoque Ideal = Velocidade de Venda × (Cobertura + Tempo de Transporte)**\n\n"
            "*(Se o Piso Exposição for maior que esse resultado, o sistema usa o Piso)*"
        )
        
        with st.expander("Ver exemplo prático"):
            st.markdown(
                "**Produto:** Fita Adesiva\n"
                "- Vende **5** unidades por dia.\n"
                "- Quero cobrir **30** dias de venda.\n"
                "- O caminhão demora **10** dias para chegar.\n"
                "- **Conta:** `5 × (30 + 10) = 200 unidades`.\n"
                "- **Conclusão:** A loja precisa ter 200 unidades. Se tiver 50, precisa receber 150."
            )

        st.subheader("A Fórmula do Saldo Ajustado")
        st.warning(
            "**Saldo Ajustado = Saldo Físico + O que está no Caminhão (Em Trânsito)**\n\n"
            "O sistema nunca olha só o que está na prateleira. Se tem 20 unidades chegando, ele já conta isso. "
            "Isso evita que você peça o mesmo produto duas vezes."
        )

        st.subheader("A Lógica de Compra (Aba COMPRAR)")
        st.markdown(
            "Se uma loja precisa de um produto e **nenhuma** outra loja tem sobrando para transferir, "
            "o sistema avisa: *'Chefe, precisamos comprar!'*.\n\n"
            "A quantidade de compra é o que falta para chegar no Ideal, descontando o que já está na rede."
        )

    # ---------------- ABA 3 - Filtros ----------------
    with tab3:
        st.header("Os Filtros do Topo")
        st.markdown("Estes filtros ajudam a focar em um grupo de produtos.")
        
        render_tabela(["Filtro", "Para que serve"], [
            ["Perfil de Análise", "Configura os 9 parâmetros automaticamente para o tipo de produto (ver aba 4)."],
            ["Fabricante", "Filtra todos os produtos de uma marca (ex: ADERE)."],
            ["Departamento", "Filtra a categoria principal (ex: FITAS)."],
            ["Grupo", "Filtra uma subcategoria (ex: FITAS ADESIVAS)."],
            ["Subgrupo", "Filtra o nível mais específico (ex: FITA CETIM)."],
            ["Produto", "Busca por nome, código ou referência. **Atenção:** Se usar este campo, os outros filtros (Fabricante, Depto, etc.) são ignorados."]
        ])

        st.subheader("Como usar o campo Produto")
        st.markdown(
            "- Digite `CAIXA QUADRADA` (espaço) para achar produtos que tenham as DUAS palavras.\n"
            "- Digite `CAPA, CAPUZ` (vírgula) para achar produtos que tenham UMA OU OUTRA palavra.\n"
            "- Digite `CAIXA QUADRADA, CAPA` para combinar as regras."
        )

    # ---------------- ABA 4 - Dicionário de Parâmetros ----------------
    with tab4:
        st.header("Dicionário de Parâmetros (Tela de Parâmetros)")
        st.markdown("Ao clicar no botão **⚙️ Parâmetros**, você verá 11 campos. Veja o que cada um faz:")

        st.subheader("1. Período de Análise")
        st.markdown(
            "**O que é:** Janela de tempo que o sistema olha para trás para calcular a velocidade.\n"
            "**Padrão:** 1 ano atrás.\n"
            "**Por que importa:** Se você escolher '30 dias atrás', o sistema só vai olhar o que vendeu no mês passado. "
            "Se o produto vendeu muito no Natal, mas você está em Fevereiro, a velocidade vai parecer baixa. "
            "Use 1 ano para ter a média real."
        )

        st.subheader("2. Filial")
        st.markdown(
            "**O que é:** Apenas visual. Filtra quais abas vão aparecer.\n"
            "**Por que importa:** Se você escolher 'Alecrim', o sistema mostra apenas a aba do Alecrim. "
            "Mas o motor internamente analisa todas as 5 filiais para saber de onde tirar o produto."
        )

        st.subheader("3. Cobertura de Vendas")
        st.markdown(
            "**O que é:** Quantos dias de venda você quer ter de estoque. É a sua 'reserva'.\n"
            "**Padrão:** 30 dias.\n"
            "**Impacto:** Se aumentar para 60 dias, o Estoque Ideal dobra. A loja vai pedir mais transferências e compras. "
            "Se diminuir para 15 dias, o Ideal cai e a loja fica com menos estoque."
        )

        st.subheader("4. Tempo de Transporte")
        st.markdown(
            "**O que é:** Quantos dias o caminhão demora para sair de uma loja/Atacado e chegar na outra.\n"
            "**Padrão:** 10 dias.\n"
            "**Impacto:** Se o caminhão demora 20 dias, o sistema vai colocar mais 20 dias de estoque no Ideal. "
            "Se você mentir e colocar 5 dias, a loja vai zerar antes do produto chegar."
        )

        st.subheader("5. Piso Exposição")
        st.markdown(
            "**O que é:** A quantidade mínima que deve ficar na prateleira, mesmo que o produto venda pouco.\n"
            "**Padrão:** 0.\n"
            "**Impacto:** Se for 0, produtos de baixo giro podem ter Ideal = 0 e a prateleira fica vazia. "
            "Se for 5, a loja sempre terá pelo menos 5 unidades para o cliente ver."
        )

        st.subheader("6. Reserva Origem (%)")
        st.markdown(
            "**O que é:** A '%' que a filial doadora guarda para ela mesma. É uma 'gordura'.\n"
            "**Padrão:** 25%.\n"
            "**Impacto:** Se a loja tem 100 de excesso e a Reserva é 25%, ela doa só 75. Se for 0%, ela doa tudo. "
            "Se for 100%, ela não doa nada."
        )

        st.subheader("7 e 8. Atacado tem Piso / Reserva?")
        st.markdown(
            "**O que é:** O Atacado é um centro de distribuição (Hub). Ele não tem prateleira de loja.\n"
            "**Padrão:** Não.\n"
            "**Impacto:** Deixe 'Não' para o Atacado doar mais produtos e não travar estoque."
        )

        st.subheader("9. Reposição Recente (Anti-gangorra)")
        st.markdown(
            "**O que é:** Uma quarentena. Se a loja recebeu produto nos últimos N dias, ela não pode pedir de novo.\n"
            "**Padrão:** 15 dias.\n"
            "**Impacto:** Evita que a loja peça 10 hoje, 10 amanhã, 10 depois. O caminhão já está na estrada. "
            "Se você colocar 5 dias, a quarentena é mais curta (mais ágil, mas mais risco de duplicidade)."
        )

        st.subheader("10. Dias em Trânsito")
        st.markdown(
            "**O que é:** A janela de dias que o sistema verifica o que já foi enviado.\n"
            "**Padrão:** 10 dias.\n"
            "**Impacto:** Se um envio foi feito há 2 dias, o sistema conta como 'Em Trânsito'. "
            "Se foi há 15 dias, ele assume que já chegou e não conta mais."
        )

        st.subheader("11. Atacado tem Mínimo p/ Compra?")
        st.markdown(
            "**O que é:** Uma regra de compra. Se for 'Sim', o Atacado só compra se a quantidade for maior ou igual ao Piso Exposição.\n"
            "**Padrão:** Não.\n"
            "**Impacto:** Evita comprar volumes irrisórios (ex: comprar 2 unidades do fornecedor)."
        )

    # ---------------- ABA 5 - Lendo os Resultados ----------------
    with tab5:
        st.header("Entendendo a Tela de Resultados")
        st.markdown(
            "Após consultar, você verá **5 cards** no topo (Enviar, Receber, Liquidar, Desc. e Comprar). "
            "Cada card mostra o total de **Itens** (linhas) e de **Unidades** (soma)."
        )

        st.subheader("As Colunas das Tabelas")
        render_tabela(["Coluna", "O que significa"], [
            ["Prioridade", "Crítica (ação hoje), Alta (esta semana), Normal (fluxo regular)."],
            ["Qtd Transf.", "A quantidade sugerida para transferir ou comprar."],
            ["Em Trânsito", "O que já está no caminhão a caminho. O sistema já conta isso."],
            ["Reserva", "O que a origem vai guardar para ela."],
            ["Dias p/ Zerar", "Projeção de quantos dias faltam para o estoque acabar (Prioridade)."],
            ["Qtd Ideal", "O tamanho da 'caixa d'água' para aquela loja."],
            ["Motivo", "A explicação do porquê o sistema sugeriu aquilo (ver aba 6)."]
        ])

        st.subheader("As 5 Seções")
        st.markdown(
            "- **📤 ENVIAR:** A filial tem demais e vai doar.\n"
            "- **📥 RECEBER:** A filial tem falta e vai receber.\n"
            "- **🛒 COMPRAR:** Ninguém na rede tem. Precisa comprar do fornecedor.\n"
            "- **⏸️ DESCONTINUAR:** Produto de giro baixo (vende 1 a cada 12 dias). Deve sair do mix.\n"
            "- **🔥 LIQUIDAR:** Produto zerado de venda. Deve ser promovido ou devolvido."
        )

    # ---------------- ABA 6 - O Livro dos Motivos ----------------
    with tab6:
        st.header("O que cada 'Motivo' significa?")
        st.markdown("O Motivo é o coração do sistema. Ele te diz exatamente o que está acontecendo.")

        motivos = {
            "SEM ESTOQUE": "A loja está zerada e **não há nada no caminhão**. É um alarme vermelho. Precisa de ação imediata.",
            "AGUARDANDO TRANSFERENCIA": "A loja está com falta, **MAS** já tem um caminhão cheio de produto indo para lá. O sistema avisa para você não mandar de novo.",
            "RECEBIDO RECENTEMENTE": "A loja recebeu produto há poucos dias. Ela está de 'castigo' (quarentena) para não pedir duplicado. Verifique se a prateleira está abastecida.",
            "URGENTE - zera hoje": "O estoque acaba em menos de 24 horas. Ação imediata.",
            "URGENTE - zera em N dias": "Vai acabar logo. Você tem alguns dias para agir.",
            "Origem parada, destino vendendo": "A loja doadora quase não vende esse produto, mas a receptora vende muito. O sistema está movendo o produto para onde ele gira.",
            "Alta rotacao no destino": "A loja receptora vende o dobro da doadora.",
            "Maior giro no destino": "A loja receptora vende 1.5x mais que a doadora.",
            "Reposicao de ciclo": "Fluxo normal. Nada de errado, apenas mantendo a prateleira cheia.",
            "ESTOQUE COMPLEMENTAR": "**Motivo de compra.** A rede tem um pouco do produto, mas não o suficiente para o Ideal. Compre só o que falta.",
            "ESTOQUE PARADO": "**Liquidar.** O produto tem estoque, mas a velocidade de venda é zero. Ninguém quer.",
            "FIM DE CICLO": "**Descontinuar.** O produto vende muito pouco (abaixo de 0.1/dia). Venda o estoque e tire do mix."
        }
        for k, v in motivos.items():
            st.markdown(f"**{k}:** {v}")

    # ---------------- ABA 7 - Cenários Reais ----------------
    with tab7:
        st.header("Cenários Reais (O que fazer?)")
        
        with st.expander("Cenário 1: O produto está em falta crítica (RECEBER)"):
            st.markdown(
                "**Tela:** Aba Alecrim (RECEBER).\n"
                "**O que vejo:** Fita Adesiva, 85 un, Prioridade Crítica, Motivo: `URGENTE - zera hoje`.\n"
                "**O que faço:** 1. Vejo o Motivo. 2. Confirmo a Origem (Atacado). 3. Clico em Gerar PDF. "
                "4. Crio a ordem de transferência no ERP."
            )

        with st.expander("Cenário 2: A rede inteira está sem estoque (COMPRAR)"):
            st.markdown(
                "**Tela:** Aba ATACADO (COMPRAR).\n"
                "**O que vejo:** Fita Crepe, Qtd Ideal 50, Sugestão de Compra 50, Motivo: `SEM ESTOQUE`.\n"
                "**O que faço:** Nenhuma loja tem o produto. Envio a lista para o time de Compras fazer o pedido ao fornecedor."
            )

        with st.expander("Cenário 3: O produto já está a caminho (AGUARDANDO)"):
            st.markdown(
                "**Tela:** Aba Zona Sul (RECEBER).\n"
                "**O que vejo:** Papel Kraft, Em Trânsito: 20 un, Motivo: `AGUARDANDO TRANSFERENCIA`.\n"
                "**O que faço:** O caminhão já saiu. Não faço nada, apenas aguardo a entrega. Se demorar, ligo para a transportadora."
            )

        with st.expander("Cenário 4: O produto está encalhado (LIQUIDAR)"):
            st.markdown(
                "**Tela:** Aba Zona Norte (LIQUIDAR).\n"
                "**O que vejo:** Squeeze Halloween, 15 un, Motivo: `ESTOQUE PARADO`.\n"
                "**O que faço:** O sistema NÃO vai transferir para outras lojas. Ação comercial: promoção local, kit, ou devolver ao fornecedor."
            )

        with st.expander("Cenário 5: O produto tem giro baixo (DESCONTINUAR)"):
            st.markdown(
                "**Tela:** Aba Alecrim (DESCONTINUAR).\n"
                "**O que vejo:** Fita Cetim Vermelha, 8 un, Motivo: `FIM DE CICLO`.\n"
                "**O que faço:** Vender até o fim do estoque. Não comprar mais."
            )

    # ---------------- ABA 8 - FAQ ----------------
    with tab8:
        st.header("Perguntas Frequentes e Ajustes")
        
        with st.expander("A sugestão parece errada. O que eu faço?"):
            st.markdown("1. Leia o **Motivo**.\n2. Confira o **Saldo** e o **Em Trânsito**.\n3. Verifique se o produto teve movimentações estranhas (devoluções, cancelamentos).\n4. Se nada explicar, acione o TI.")

        with st.expander("O sistema sugere menos de 5 unidades?"):
            st.markdown("Não. O motor tem uma regra de **MOQ (Minimum Order Quantity)**. Transferências ou compras abaixo de 5 unidades são ignoradas, pois o custo do frete é maior que o benefício.")

        with st.expander("Como ajustar se estiver sugerindo MUITO?"):
            st.markdown("- Aumente a **Reposição Recente** (de 15 para 30) para bloquear mais.\n- Aumente a **Reserva Origem** (de 25% para 40%) para a origem doar menos.\n- Diminua a **Cobertura** (de 30 para 15) para o Ideal ser menor.")

        with st.expander("Como ajustar se estiver sugerindo POUCO?"):
            st.markdown("- Diminua a **Reposição Recente** (de 15 para 7).\n- Diminua a **Reserva Origem** (de 25% para 15%).\n- Aumente a **Cobertura** (de 30 para 45).")

        with st.expander("O Atacado compra para ele mesmo?"):
            st.markdown("Sim. O Atacado também tem um Estoque Ideal. Se ele estiver abaixo do Ideal, a aba COMPRAR dele vai sugerir a compra para repor a própria prateleira do CD.")

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")