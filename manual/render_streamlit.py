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



def render_manual() -> None:
    """Renderiza o manual do gestor."""

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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏁 Introdução",
        "🧠 Como Pensa",
        "🎛️ Filtros & Parâmetros",
        "📊 Resultado",
        "📅 Rotina",
        "❓ FAQ",
    ])

    # ---------------- ABA 1 ----------------
    with tab1:
        st.header("Por que este sistema existe")

        st.markdown(
            "Imagine o dia a dia de uma rede com **5 filiais** e "
            "**milhares de produtos**. Todos os dias você precisa responder:"
        )

        st.markdown(
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

        st.subheader("O que o sistema faz")
        st.markdown(
            "✅ **1. Analisa** histórico de vendas\n\n"
            "✅ **2. Calcula** o estoque ideal de cada filial\n\n"
            "✅ **3. Identifica** excesso (doador) e falta (receptor)\n\n"
            "✅ **4. Sugere** qual filial envia, para quem, e quanto\n\n"
            "✅ **5. Prioriza** por urgência\n\n"
            "✅ **6. Gera** relatórios em PDF por filial"
        )

        st.subheader("O que o sistema NÃO faz")
        st.markdown(
            "- ❌ **Não substitui sua decisão** — ele sugere, você aprova\n"
            "- ❌ **Não executa transferências** — você cria a ordem no ERP\n"
            "- ❌ **Não altera dados** no banco — é somente leitura\n"
            "- ❌ **Não substitui o bom senso** — sempre confira o Motivo antes de aprovar"
        )

        st.subheader("Em 1 parágrafo")
        st.success(
            "O sistema olha os últimos **365 dias** de cada produto, calcula o "
            "**ritmo de venda** de cada filial, define **quanto cada uma precisa "
            "ter em estoque** para cobrir **30 dias** de venda + **10 dias** de "
            "transporte, e cruza tudo: quem tem demais é sugerido como **doador**, "
            "quem tem de menos é sugerido como **receptor**. O **Atacado** entra "
            "como hub principal, e as **lojas próximas** se ajudam quando faz sentido."
        )

        st.subheader("De onde vem a inteligência")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🏛️ DRP")
            st.caption("Distribution Requirements Planning")
            st.markdown("Planejamento baseado no **consumo real**.")
            st.caption("Walmart, Carrefour, Pão de Açúcar")
        with col2:
            st.markdown("### 🔄 IST")
            st.caption("Inter-Store Transfers")
            st.markdown("Transferências entre lojas.")
            st.caption("Zara, H&M, Best Buy")
        with col3:
            st.markdown("### 🌐 MEIO")
            st.caption("Multi-Echelon Optimization")
            st.markdown("Otimização com **hub central**.")
            st.caption("Amazon, Coca-Cola, P&G")

    # ---------------- ABA 2 ----------------
    with tab2:
        st.header("Como o sistema pensa")

        st.subheader("A metáfora da caixa d'água")
        st.markdown(
            "Imagine que cada filial é uma **caixa d'água**. "
            "O sistema tenta manter cada caixa no nível ideal:"
        )

        st.markdown(
            "| Nível | Estado |\n"
            "|-------|--------|\n"
            "| **100% (Ideal)** | Tudo perfeito |\n"
            "| **80%** | Atenção |\n"
            "| **40%** | Crítico |\n"
            "| **0% (Ruptura)** | Urgente |"
        )

        st.subheader("Estoque Ideal (fórmula)")
        st.code("Estoque Ideal = Velocidade x (Cobertura + Tempo de Transporte)", language="text")

        st.markdown(
            "**Exemplo — Fita Adesiva 3M**\n\n"
            "- Vendas nos últimos 365 dias: 1.825 un\n"
            "- Velocidade: 1.825 / 365 = **5 un/dia**\n"
            "- Cobertura: **30 dias**\n"
            "- Tempo de Transporte: **10 dias**\n"
            "- Soma: **40 dias**\n"
            "- **Estoque Ideal = 5 x 40 = 200 un**"
        )

        st.info(
            "A loja deveria ter **200 un** para cobrir 30 dias de venda + "
            "10 dias de transporte."
        )

        st.subheader("Excesso e Falta")
        st.code(
            "Excesso = Saldo - Ideal   (quando positivo)\n"
            "Falta   = Ideal - Saldo   (quando positivo)",
            language="text"
        )

        st.markdown("**Exemplo com 5 filiais**")
        st.markdown(
            "| Filial | Saldo | Ideal | Excesso | Falta |\n"
            "|--------|-------|-------|---------|-------|\n"
            "| Atacado | 500 | 100 | **400** | 0 |\n"
            "| Alecrim | 30 | 50 | 0 | **20** |\n"
            "| Via Direta | 80 | 40 | **40** | 0 |\n"
            "| Zona Sul | 15 | 60 | 0 | **45** |\n"
            "| Zona Norte | 70 | 55 | **15** | 0 |"
        )

        st.markdown(
            "**Leitura:**\n\n"
            "- 🔵 **Atacado** tem 400 un de excesso → doador principal\n"
            "- 🟠 **Zona Sul** tem 45 un de falta → receptor urgente\n"
            "- 🟠 **Alecrim** tem 20 un de falta → receptor\n"
            "- 🔵 **Via Direta** tem 40 un de excesso → doador secundário"
        )

        st.subheader("Matriz de proximidade")
        st.markdown(
            "| Destino | Doadores em ordem de prioridade |\n"
            "|---------|--------------------------------|\n"
            "| **Alecrim** | Atacado → Via Direta → Zona Sul → Zona Norte |\n"
            "| **Via Direta** | Atacado → Alecrim → Zona Sul |\n"
            "| **Zona Sul** | Atacado → Alecrim → Via Direta |\n"
            "| **Zona Norte** | Atacado → Alecrim |\n"
            "| **Atacado** | Nunca recebe |"
        )

    # ---------------- ABA 3 ----------------
    with tab3:
        st.header("Filtros e Parâmetros")

        st.subheader("⭐ 4.1 Perfil de Análise")

        st.info(
            "O **Perfil de Análise** é o primeiro campo no topo da tela. Ele é a ferramenta "
            "de produtividade mais importante para o gestor, pois configura **9 parâmetros de uma só vez**."
        )

        st.markdown("**Onde se aplica e qual a sua importância:**")
        st.markdown(
            "- Evita erros manuais ao configurar 9 campos separadamente todos os dias.\n"
            "- Padroniza a análise: toda a equipe usa a mesma régua para o mesmo tipo de produto.\n"
            "- Agiliza a rotina: em 1 clique você muda a estratégia de 'Padrão' para 'Sazonal', por exemplo."
        )

        st.markdown("**Como ele interage com os Parâmetros?**")
        st.markdown(
            "Ao trocar o Perfil, o sistema sobrescreve os 9 parâmetros no painel de Parâmetros. "
            "Se você mudar manualmente um parâmetro (ex: mudar a Cobertura de 30 para 45 dias), "
            "o sistema respeitará a sua alteração manual e o nome do perfil continuará o mesmo. "
            "Se quiser voltar tudo ao padrão do sistema, basta clicar no botão **Limpar (🧹)**."
        )

        st.markdown(
            "| Perfil | Quando usar | Principais diferenças |\n"
            "|--------|-------------|----------------------|\n"
            "| **Padrão** | Uso geral | 1 ano de histórico, cobertura 30d, reserva 25%, quarentena 15d |\n"
            "| **Sazonal** | Carnaval, São João, Natal | 30 dias de histórico, piso 3, reserva 10%, quarentena 7d |\n"
            "| **Alto Giro** | Produtos que vendem muito rápido | 3 meses de histórico, cobertura 15d, lead 7d, piso 5 |\n"
            "| **Baixo Giro** | Produtos lentos, pouca saída | 1 ano de histórico, piso 3, reserva 30%, quarentena 20d |\n"
            "| **Liquidação** | Fim de ciclo / queima de estoque | 6 meses de histórico, cobertura 7d, reserva 0% |"
        )

        st.info(
            "💡 **Nota:** Cada perfil sobrescreve todos os 9 parâmetros. Se você alterar um deles manualmente, "
            "o perfil continua aplicado nos demais."
        )

        st.subheader("4.2 Filtros do topo")

        st.markdown("### 🔍 Busca Avançada")

        st.info(
            "O campo **Produto** aceita buscas mais espertas com **E** e **OU** — "
            "e ainda pode ignorar os outros filtros quando você quer focar num produto específico."
        )

        st.markdown(
            "**Sintaxe de busca**\n\n"
            "| Você digita | O que o sistema faz |\n"
            "|-------------|---------------------|\n"
            "| `CAIXA QUADRADA` | Acha produtos que tenham **CAIXA E QUADRADA** |\n"
            "| `CAPA, CAPUZ` | Acha produtos com **CAPA OU CAPUZ** |\n"
            "| `CAIXA QUADRADA, CAPA` | Acha **(CAIXA E QUADRADA) OU CAPA** |"
        )

        st.markdown(
            "**Regra especial — Produto é exclusivo**\n\n"
            "Quando você digita algo em **Produto**, o sistema **ignora** "
            "Fabricante, Departamento, Grupo, Subgrupo e **Filial**. "
            "Ele busca o produto em **toda a rede** — todas as 5 filiais, todos os fabricantes.\n\n"
            "Um **aviso azul** aparece abaixo dos filtros avisando que isso está ativo."
        )

        st.warning(
            "**Cuidado**: essa regra vale para a busca por **Produto**. "
            "Se você quer filtrar por Fabricante e ver o resultado em todas as filiais, "
            "**deixe o campo Produto em branco**."
        )

        st.subheader("Parâmetros")

        st.markdown("### Linha 1 — Janela de Análise")
        st.markdown(
            "| Parâmetro | O que é | Padrão |\n"
            "|-----------|---------|--------|\n"
            "| Período de Análise | Janela histórica | 1 ano atrás |\n"
            "| Filial | Filtrar uma filial | (todas) |\n"
            "| Cobertura de Vendas | Dias de estoque | Para 30 dias |\n"
            "| Tempo de Transporte | Dias entre envio e entrega | 10 dias |"
        )

        st.markdown("### Linha 2 — Proteção das Origens")
        st.markdown(
            "| Parâmetro | O que é | Padrão |\n"
            "|-----------|---------|--------|\n"
            "| Piso Exposição (un) | Mínimo na prateleira | 0 |\n"
            "| Reserva Origem (%) | % que fica na origem | 25% |\n"
            "| Atacado tem Piso? | Atacado respeita piso | Não |\n"
            "| Atacado tem Reserva? | Atacado guarda reserva | Não |"
        )

        st.markdown("### Linha 3 — Travas de Segurança")
        st.markdown(
            "| Parâmetro | O que é | Padrão |\n"
            "|-----------|---------|--------|\n"
            "| Reposição Recente (dias) | Quarentena pós-recebimento | 15 |\n"
            "| Dias em Trânsito | Janela de envio a caminho | 10 |"
        )

        with st.expander("Detalhamento — Cobertura de Vendas"):
            st.markdown(
                "| Opção | Dias | Quando usar |\n"
                "|-------|------|-------------|\n"
                "| Para 7 dias | 7 | Produtos perecíveis |\n"
                "| Para 15 dias | 15 | Alto giro |\n"
                "| **Para 30 dias** | **30** | **Padrão** |\n"
                "| Para 2 meses | 60 | Giro médio |\n"
                "| Para 3 meses | 90 | Giro baixo |\n"
                "| Para 6 meses | 180 | Sazonais |\n"
                "| Para 1 ano | 365 | Produtos específicos |"
            )

        with st.expander("Detalhamento — Reserva Origem"):
            st.code(
                "Exemplo com Reserva = 25%:\n\n"
                "Excesso = 400 un\n"
                "Reserva = 25% x 400 = 100 un\n"
                "Disponível para doar = 300 un",
                language="text"
            )

        with st.expander("Detalhamento — Reposição Recente"):
            st.markdown(
                "**O que é**: dias em que a filial fica bloqueada para receber "
                "depois de uma transferência.\n\n"
                "**Por que existe**: para evitar o efeito gangorra.\n\n"
                "Exemplo:\n"
                "- Dia 1: Zona Sul recebe 50 un\n"
                "- Dia 1-15: Bloqueado\n"
                "- Dia 16: Liberado"
            )

    # ---------------- ABA 4 ----------------
    with tab4:
        st.header("Como ler o resultado")

        st.subheader("Abas por filial")
        st.markdown(
            "Após consultar, você verá 5 abas: "
            "**ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE**.\n\n"
            "Cada uma mostra:\n\n"
            "- **ENVIAR** — o que essa filial precisa mandar\n"
            "- **RECEBER** — o que essa filial precisa receber"
        )

        st.subheader("Colunas essenciais")
        st.markdown(
            "| Coluna | Significado |\n"
            "|--------|-------------|\n"
            "| Prioridade | Crítica / Alta / Normal |\n"
            "| Cod | Código interno |\n"
            "| Produto | Descrição |\n"
            "| Destino / Origem | Filial parceira |\n"
            "| Qtd Transf. | Quanto transferir |\n"
            "| Reserva | Quanto a origem guarda |\n"
            "| Dias p/ Zerar | Dias até acabar |\n"
            "| Qtd Ideal | Estoque ideal |\n"
            "| Motivo | Por que foi sugerido |"
        )

        st.subheader("Prioridades")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.error("**Crítica**\n\nZera em < 7 dias\n\nTransferir HOJE")
        with col2:
            st.warning("**Alta**\n\nZera entre 7 e 15 dias\n\nEsta semana")
        with col3:
            st.info("**Normal**\n\nZera em > 15 dias\n\nFluxo regular")

        st.subheader("Motivos possíveis")
        st.markdown(
            "| Motivo | Significado |\n"
            "|--------|-------------|\n"
            "| SEM ESTOQUE | Já zerou — urgente |\n"
            "| AGUARDANDO TRANSFERENCIA | Já tem envio a caminho |\n"
            "| RECEBIDO RECENTEMENTE | Recebeu há pouco, em quarentena |\n"
            "| URGENTE - zera em N dias | Vai zerar em breve |\n"
            "| Origem parada, destino vendendo | Sai de onde não vende |\n"
            "| Alta rotacao no destino | Destino vende 2x mais |\n"
            "| Maior giro no destino | Destino vende 1,5x mais |\n"
            "| Reposicao de ciclo | Padrão — mantém fluxo |"
        )

    # ---------------- ABA 5 ----------------
    with tab5:
        st.header("Rotina semanal")

        st.subheader("Segunda-feira (10 min)")
        st.markdown(
            "1. Abra o app\n"
            "2. **Escolha o Perfil de Análise** no topo (Padrão, Sazonal, Alto Giro, Baixo Giro ou Liquidação)\n"
            "3. Escolha um Fabricante no topo\n"
            "4. Clique em 🔍\n"
            "5. Filtre por Prioridade = Crítica\n"
            "6. Se quiser refinar, clique em ⚙️ Parâmetros"
        )

        st.subheader("Terça a Quinta (ação)")
        st.markdown(
            "Para cada produto crítico:\n\n"
            "1. Veja o Motivo\n"
            "2. Confirme a Qtd Transf.\n"
            "3. Verifique a Origem\n"
            "4. Clique em 📄 Gerar PDF\n"
            "5. Crie a ordem no ERP"
        )

        st.subheader("Sexta-feira (10 min)")
        st.markdown(
            "1. Reabra o app\n"
            "2. Compare com a semana anterior\n"
            "3. Ajuste parâmetros se necessário"
        )

    # ---------------- ABA 6 ----------------
    with tab6:
        st.header("Perguntas frequentes")

        faq = [
            (
                "O sistema demora quanto para carregar?",
                "Com filtro de fabricante: 30-60 segundos. Sem filtro: pode demorar mais."
            ),
            (
                "Posso deixar em branco todos os filtros?",
                "Não. Escolha pelo menos um."
            ),
            (
                "Por que meu produto não aparece?",
                "Várias causas: não vendeu no período, está nos departamentos 09/10, "
                "não tem excesso nem falta, ou o filtro excluiu."
            ),
            (
                "A sugestão parece errada. O que faço?",
                "1. Verifique o Motivo. 2. Confira movimentações estranhas. "
                "3. Verifique o Período. 4. Se persistir, acione TI."
            ),
            (
                "Posso mudar os parâmetros toda hora?",
                "Não recomendo. Deixe padrão por 15 dias antes de mexer."
            ),
            (
                "Como sei se um produto é doador ou receptor?",
                "Doador: seção ENVIAR. Receptor: seção RECEBER."
            ),
            (
                "Preciso anotar tudo que o sistema sugere?",
                "Não. Sempre confira o Motivo antes de aprovar."
            ),
            (
                "O que é 'RECEBIDO RECENTEMENTE'?",
                "Filial recebeu nos últimos 15 dias. Está em quarentena."
            ),
            (
                "O que é 'AGUARDANDO TRANSFERENCIA'?",
                "Significa que o produto já tem algo a caminho. Não duplica."
            ),
            (
                "Como aciono o suporte?",
                "[Contato do responsável pelo projeto]"
            ),
        ]

        for i, (pergunta, resposta) in enumerate(faq, 1):
            with st.expander(f"{i}. {pergunta}"):
                st.markdown(resposta)

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")