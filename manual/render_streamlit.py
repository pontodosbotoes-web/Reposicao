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
                "⬇️ Baixar PDF", data=pdf_bytes, file_name="Manual_Reposicao_Gestor.pdf",
                mime="application/pdf", use_container_width=True,
            )
        else:
            st.button("⬇️ Baixar PDF", disabled=True, use_container_width=True)

    st.markdown("# 📖 Manual do Gestor")
    st.markdown("**Reposição de Produtos** — Guia Completo de Operação")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Começando", "🧠 A Lógica", "🎛️ Parâmetros", "📊 Lendo a Tela", "📅 Rotina", "🛠️ Casos Práticos"
    ])

    # ---------------- ABA 1 - Começando ----------------
    with tab1:
        st.header("Bem-vindo ao Sistema de Reposição")
        st.markdown(
            "Se você acabou de entrar na empresa, imagine a seguinte situação: temos **5 lojas** e "
            "**milhares de produtos**. Todos os dias, alguém precisa decidir:\n\n"
            "1. **Quanto** mandar de produto para cada loja?\n"
            "2. **Quando** mandar?\n"
            "3. De **onde** tirar o produto (de qual loja ou do Atacado)?\n"
            "4. E se **ninguém** tiver o produto? Precisamos comprar?\n\n"
            "Fazer isso manualmente para 10.000 produtos levaria dias e geraria muitos erros. "
            "É exatamente isso que este sistema automatiza para você."
        )
        
        st.info(
            "💡 **O que o sistema faz:** Ele olha o histórico de vendas, calcula o que cada loja "
            "precisa, e sugere a ação: **Transferir** (se tem na rede) ou **Comprar** (se não tem).\n\n"
            "🛑 **O que ele NÃO faz:** Ele não executa as ordens. Ele apenas sugere. Você é o gestor "
            "e tem a palavra final. A transferência real é feita no ERP."
        )

        st.subheader("Os 4 Botões Principais")
        st.markdown(
            "- 🔵 **Consultar:** Faz o motor rodar e buscar as sugestões.\n"
            "- 🧹 **Limpar:** Zera todos os filtros e resultados.\n"
            "- ⚙️ **Parâmetros:** Abre o painel para ajustar as réguas de cálculo.\n"
            "- 📄 **Gerar PDF:** Cria um relatório imprimível da filial selecionada."
        )

    # ---------------- ABA 2 - A Lógica ----------------
    with tab2:
        st.header("Como o motor pensa?")
        st.markdown(
            "Imagine que cada filial é uma **caixa d'água**. O sistema tenta manter a água sempre no nível ideal. "
            "Para isso, ele segue 4 passos lógicos:"
        )

        st.subheader("Passo 1: O Tamanho da Caixa (Estoque Ideal)")
        st.markdown(
            "O sistema calcula quanto cada loja precisa para não faltar produto:\n"
            "**Fórmula:** `Velocidade de Venda × (Dias de Cobertura + Dias de Transporte)`\n\n"
            "*Exemplo:* Se a loja vende **5** unidades por dia, e o caminhão demora **10** dias para chegar, "
            "e eu quero cobrir **30** dias de venda: `5 × (30 + 10) = 200 unidades`."
        )

        st.subheader("Passo 2: Quem tem demais e quem tem de menos?")
        st.markdown(
            "- **Excesso:** A loja tem mais do que o Ideal. Ela pode **doar**.\n"
            "- **Falta:** A loja tem menos que o Ideal. Ela precisa **receber**."
        )

        st.subheader("Passo 3: A Matriz de Proximidade (Quem ajuda quem?)")
        st.markdown(
            "Se a Zona Sul precisa de produto, o sistema não vai mandar de qualquer lugar. "
            "Ele segue uma ordem de prioridade (ex: 1º Atacado, 2º Alecrim, 3º Via Direta). "
            "Assim ele economiza frete e tempo."
        )

        st.subheader("Passo 4: O que fazer se a rede inteira estiver vazia? (COMPRAR)")
        st.markdown(
            "Se nenhuma loja tem sobrando, o sistema não pode transferir. É aí que entra a aba **COMPRAR**. "
            "O sistema vai dizer: *'Chefe, a rede toda precisa de 50 unidades. Ninguém tem. Compre 50 do fornecedor.'*"
        )
        st.success(
            "🎯 **Regra de Ouro:** O sistema sempre tenta **transferir** primeiro. Só sugere **comprar** se for impossível resolver internamente."
        )

        st.subheader("E o 'Em Trânsito'?")
        st.markdown(
            "Se um caminhão já saiu da origem com 20 unidades, o sistema não manda transferir de novo. "
            "Ele conta essas 20 como 'Em Trânsito' e avisa: **AGUARDANDO TRANSFERENCIA**."
        )

    # ---------------- ABA 3 - Parâmetros ----------------
    with tab3:
        st.header("Controlando a Régua (Perfis e Parâmetros)")
        st.markdown(
            "O sistema não usa a mesma regra para todos os produtos. "
            "Uma fita adesiva básica (Classe A) não pode faltar nunca. Já um artigo de Halloween (Sazonal) "
            "tem um pico de venda e depois morre."
        )

        st.info(
            "💡 **O Perfil de Análise** preenche os 9 parâmetros automaticamente para você. "
            "Escolha o perfil que combina com o produto e clique em Consultar."
        )

        st.markdown("### Os 9 Parâmetros e o que eles fazem:")
        render_tabela(["Parâmetro", "O que significa na prática?"], [
            ["Período de Análise", "Janela de tempo para calcular a velocidade. 1 ano é o padrão."],
            ["Cobertura de Vendas", "Quantos dias de venda eu quero ter na prateleira. (Ex: 30 dias)"],
            ["Tempo de Transporte", "Quantos dias o caminhão demora para chegar do Atacado até a loja?"],
            ["Piso Exposição", "Quantidade mínima que deve ficar na prateleira, mesmo se vender pouco (para não ficar vazia)."],
            ["Reserva Origem", "Uma 'gordura' que a loja doadora guarda. Ex: Se tem 100 de sobra, doa só 75 e guarda 25."],
            ["Atacado tem Piso/Reserva?", "O Atacado é um centro de distribuição. Geralmente ele não precisa de piso de prateleira."],
            ["Reposição Recente", "Quarentena. Se a loja recebeu produto ontem, ela não pede de novo hoje."],
            ["Dias em Trânsito", "Janela de dias que o sistema olha para trás para ver o que já foi enviado."],
            ["Mínimo p/ Compra", "Evita comprar volumes muito pequenos (ex: comprar 2 unidades)."]
        ])

    # ---------------- ABA 4 - Lendo a Tela ----------------
    with tab4:
        st.header("Lendo os Resultados")
        st.markdown(
            "Após clicar em Consultar, você verá **5 cards** no topo (Enviar, Receber, Liquidar, Desc. e Comprar). "
            "Eles mostram a quantidade de **Itens** (linhas) e **Unidades** (soma)."
        )

        st.subheader("As Seções de cada Aba")
        st.markdown(
            "- **📤 ENVIAR:** O que a filial precisa mandar para as outras.\n"
            "- **📥 RECEBER:** O que a filial precisa receber de outras.\n"
            "- **🛒 COMPRAR:** O que falta na rede e precisa ser comprado do fornecedor.\n"
            "- **⏸️ DESCONTINUAR / 🔥 LIQUIDAR:** Produtos que não vendem e precisam sair do estoque."
        )

        st.subheader("Colunas Importantes")
        render_tabela(["Coluna", "O que significa"], [
            ["Qtd Transf.", "A quantidade que deve ser movimentada (ou comprada)."],
            ["Em Trânsito", "A quantidade que já está no caminhão."],
            ["Qtd Ideal", "O tamanho da 'caixa d'água' (estoque perfeito)."],
            ["Motivo", "O coração da decisão. Explica o porquê (veja abaixo)."]
        ])

        st.subheader("Os Motivos Explicados")
        render_tabela(["Motivo", "O que o sistema está te dizendo?"], [
            ["SEM ESTOQUE", "Urgente! A loja está zerada e não há nada a caminho. Precisa de ação imediata."],
            ["AGUARDANDO TRANSFERENCIA", "Relaxe, o produto já está no caminhão a caminho da loja."],
            ["URGENTE - zera hoje", "O estoque acaba em menos de 24 horas."],
            ["ESTOQUE COMPLEMENTAR", "Motivo de compra. A rede tem um pouco, mas não o suficiente. Compre só o que falta."],
            ["RECEBIDO RECENTEMENTE", "A loja acabou de receber. Está em quarentena (anti-gangorra) para não pedir duplicado."]
        ])

    # ---------------- ABA 5 - Rotina ----------------
    with tab5:
        st.header("Sua Rotina Semanal")
        st.markdown(
            "### 🗓️ Segunda-feira (10 min)\n"
            "1. Abra o app\n"
            "2. Escolha o Perfil de Análise\n"
            "3. Escolha o Fabricante no topo\n"
            "4. Clique em 🔍 Consultar\n"
            "5. Olhe os cards para ver o volume de trabalho.\n\n"
            "### 🗓️ Terça a Quinta (Ação)\n"
            "1. Filtre a tabela por **Prioridade Crítica**.\n"
            "2. Leia o Motivo e confirme a Quantidade.\n"
            "3. Vá para a aba do Atacado ou da origem.\n"
            "4. Clique em 📄 **Gerar PDF**.\n"
            "5. Crie a ordem de transferência no ERP.\n"
            "6. Se houver itens na aba **COMPRAR**, envie a lista para o time de Compras.\n\n"
            "### 🗓️ Sexta-feira (10 min)\n"
            "1. Reabra o app e compare com a semana anterior.\n"
            "2. Se algo parece errado, verifique os ajustes finos."
        )

    # ---------------- ABA 6 - Casos Práticos ----------------
    with tab6:
        st.header("Casos Práticos Reais")
        
        with st.expander("Caso 1: A loja está morrendo de vender (RECEBER)"):
            st.markdown(
                "**Cenário:** Você abre a aba Zona Sul e vê o produto 'Fita Adesiva' na seção **RECEBER**.\n"
                "- **Ideal:** 100 un\n"
                "- **Qtd Transf.:** 85 un\n"
                "- **Motivo:** `URGENTE - zera hoje`\n\n"
                "**O que fazer:** O produto acaba hoje. Gere o PDF, mande o Atacado separar 85 unidades e envie para a Zona Sul."
            )

        with st.expander("Caso 2: A rede inteira está vazia (COMPRAR)"):
            st.markdown(
                "**Cenário:** Você olha a aba **COMPRAR** do Atacado e vê 'Fita Cetim'.\n"
                "- **Ideal da Rede:** 50 un\n"
                "- **Sugestão de Compra:** 50 un\n"
                "- **Motivo:** `SEM ESTOQUE`\n\n"
                "**O que fazer:** Nenhuma loja tem o produto. É impossível transferir. Envie essa lista para o comprador e ele fará a ordem de compra com o fornecedor."
            )

        with st.expander("Caso 3: O produto está a caminho (AGUARDANDO)"):
            st.markdown(
                "**Cenário:** A Zona Sul precisa de 'Papel Kraft', mas o sistema mostra:\n"
                "- **Qtd Transf.:** 40 un\n"
                "- **Em Trânsito:** 20 un\n"
                "- **Motivo:** `AGUARDANDO TRANSFERENCIA`\n\n"
                "**O que fazer:** O Atacado já despachou 20 unidades anteriormente. O gestor não precisa fazer nada agora, apenas aguardar o caminhão chegar. O sistema avisa para você não mandar de novo e gerar o 'Efeito Chicote'."
            )

        with st.expander("Caso 4: O produto está encalhado (LIQUIDAR)"):
            st.markdown(
                "**Cenário:** A Zona Norte tem 15 unidades de 'Squeeze Halloween' no estoque, mas ninguém vendeu nada o ano todo.\n"
                "- **Motivo:** `ESTOQUE PARADO`\n\n"
                "**O que fazer:** O sistema **NÃO** vai sugerir transferir esse produto para a Zona Sul, porque a Zona Sul também não vende. A ação é comercial: fazer uma promoção local ou devolver ao fornecedor."
            )

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")