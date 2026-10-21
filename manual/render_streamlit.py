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
    st.markdown("**Reposição de Produtos** — A ciência por trás da operação.")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. O Problema (A Dor)", "2. A Ciência (A Solução)", "3. As Ferramentas", 
        "4. A Inteligência (Lendo a Tela)", "5. O Protocolo (O Dia a Dia)"
    ])

    # ---------------- ABA 1 - O Problema ----------------
    with tab1:
        st.header("Módulo 1: O Problema que Justifica o Sistema")
        st.markdown(
            "Antes de aprender a usar a ferramenta, você precisa entender **por que ela existe**. "
            "Sem isso, você apenas aperta botões sem saber o impacto real no negócio."
        )

        st.subheader("O Custo da Ruptura (Prateleira Vazia)")
        render_box(
            "<b>O que é?</b> Quando o cliente quer comprar e não encontra o produto na prateleira.<br><br>"
            "<b>Impacto no Negócio:</b> No varejo brasileiro, falhas de abastecimento são responsáveis por até <b>42% das perdas de vendas</b>[reference:9]. No setor de moda, a perda chega a <b>30%</b>[reference:10].<br><br>"
            "<b>O que o sistema faz?</b> O motor calcula o Estoque Ideal para que a prateleira nunca fique vazia, sugerindo transferências antes que o produto zere.",
            cor_borda="#EF4444" # Vermelho
        )

        st.subheader("O Custo do Excesso (Dinheiro Parado)")
        render_box(
            "<b>O que é?</b> Ter mais produto do que a loja consegue vender.<br><br>"
            "<b>Impacto no Negócio:</b> Dinheiro imobilizado, perda por validade/obsolescência e custo de armazenagem.<br><br>"
            "<b>O que o sistema faz?</b> Identifica quem tem excesso (doador) e move o produto para onde ele está vendendo, reduzindo o capital parado.",
            cor_borda="#F59E0B" # Laranja
        )

        st.subheader("Como era a rotina manual (e por que falhava)")
        st.markdown(
            "Antes deste sistema, o gestor fazia:\n"
            "1. **4 a 6 horas por semana** montando planilhas e ligando para as filiais.\n"
            "2. Decisões baseadas em **intuição** e não em dados de velocidade de venda.\n"
            "3. Erros frequentes: **esquecer produtos**, calcular a quantidade errada ou mandar de uma loja que também estava precisando.\n\n"
            "**Com o sistema:** O motor faz o cálculo para milhares de produtos em segundos, e o gestor foca apenas em aprovar as ações críticas."
        )

    # ---------------- ABA 2 - A Ciência ----------------
    with tab2:
        st.header("Módulo 2: A Ciência por trás do Motor")
        st.markdown(
            "O sistema não foi inventado do zero. Ele aplica **3 práticas consolidadas** no varejo mundial. "
            "Entender isso é o que diferencia um gestor estratégico de um operador."
        )

        st.subheader("1. DRP (Distribution Requirements Planning)")
        st.markdown(
            "**O que é:** Planejamento de reposição baseado no **consumo real** de cada ponto de venda.\n\n"
            "**Onde entra no sistema:** É a base do cálculo do **Estoque Ideal** (Velocidade de Venda × Cobertura).\n\n"
            "**Quem usa:** Walmart, Carrefour, Pão de Açúcar.\n\n"
            "**Literatura:** O DRP reduz faltas e melhora a pontualidade das entregas[reference:11], além de evitar sobreinventário e desabastecimento[reference:12]."
        )

        st.subheader("2. IST (Inter-Store Transfers)")
        st.markdown(
            "**O que é:** Transferências entre lojas para corrigir desequilíbrio enquanto a janela de venda está aberta.\n\n"
            "**Onde entra no sistema:** É a **Matriz de Proximidade**. Quando a Zona Sul precisa, o sistema tenta o Atacado, depois o Alecrim, e assim por diante.\n\n"
            "**Quem usa:** Zara, H&M, Best Buy.\n\n"
            "**Caso real (Zara):** A Zara usa dados de PDV em tempo real e *cross-docking* para um ciclo de design até a loja de apenas **2 a 3 semanas**[reference:13]. Transferir entre lojas é mais rápido e barato do que esperar o centro de distribuição."
        )

        st.subheader("3. MEIO (Multi-Echelon Inventory Optimization)")
        st.markdown(
            "**O que é:** Otimização de inventário em toda a rede, com um **hub central** (Atacado) para consolidar estoque.\n\n"
            "**Onde entra no sistema:** O **Atacado** é o primeiro doador e o consolidador de compras.\n\n"
            "**Quem usa:** Amazon, Coca-Cola, P&G.\n\n"
            "**Caso real (Amazon):** A otimização multi-echelon da Amazon reduziu o capital de giro imobilizado em **14% a 27%** e melhorou o nível de serviço em até **3,2%**[reference:14], além de reduzir faltas em **30% a 50%**[reference:15]."
        )

        st.subheader("O que é o Efeito Chicote (e como o sistema o combate)")
        st.markdown(
            "**A História:** A P&G descobriu que, mesmo com as vendas de fraldas Pampers estáveis no varejo, os pedidos dos supermercados flutuavam drasticamente. Isso inflava os custos de produção e estoque na cadeia inteira[reference:16].\n\n"
            "**Por que acontece:** Cada elo da cadeia pede um pouco a mais por medo de faltar, e essa distorção se amplifica.\n\n"
            "**Como o sistema resolve:** O parâmetro **Reposição Recente** funciona como uma quarentena. Se a loja recebeu produto há poucos dias, o sistema bloqueia um novo pedido, mesmo que a falta ainda exista. Isso evita o pedido duplicado e quebra o ciclo."
        )

    # ---------------- ABA 3 - As Ferramentas ----------------
    with tab3:
        st.header("Módulo 3: Desmistificando as Ferramentas")
        st.markdown(
            "Aqui explicamos o **'Porquê'** de cada ferramenta e o risco de usá-la de forma errada."
        )

        st.subheader("O Perfil de Análise (O Atalho Inteligente)")
        st.markdown(
            "O Perfil configura os 9 parâmetros automaticamente. Escolher o perfil errado pode custar caro. Veja:"
        )
        
        with st.expander("Guia Rápido: Qual perfil escolher? (MUITO IMPORTANTE)"):
            render_tabela(["Perfil", "Quando usar (O MOTIVO)", "O que acontece se errar?"], [
                ["Padrão", "Produtos normais, que vendem o ano todo.", "Se usar em um sazonal, vai acumular estoque fora de época."],
                ["Lançamento", "Produto novo, sem histórico de venda.", "Se usar Padrão, o sistema acha que vende zero e não manda nada (prateleira vazia)."],
                ["Classe A", "Campeões de venda. O carro-chefe.", "Se usar Baixo Giro, o sistema vai deixar faltar o produto mais importante."],
                ["Alto Giro", "Venda rápida e constante.", "Se usar Padrão, a loja zera antes do caminhão chegar."],
                ["Sazonal Longo", "Natal, Carnaval. Vende muito por semanas.", "Se usar Sazonal Curto, o estoque acaba no meio da campanha."],
                ["Sazonal Curto", "Páscoa, Halloween. Pico de 1 semana.", "Se usar Sazonal Longo, sobra estoque após a data (prejuízo)."],
                ["Baixo Giro", "Produtos encalhados. Vende 1 por mês.", "Se usar Classe A, compra uma montanha de produto que ninguém quer."],
                ["Liquidação", "Fim de ciclo. Não vende mais.", "Se usar Padrão, o sistema fica transferindo produto morto (gasta frete)."],
            ])

        st.subheader("Os 11 Parâmetros (O que cada um resolve?)")
        st.markdown("Se você quiser ajustar manualmente, entenda o impacto de cada campo:")
        
        with st.expander("Ver detalhes dos parâmetros"):
            st.markdown(
                "**1. Período de Análise:** Janela de tempo para calcular a velocidade. Se usar 30 dias, ignora sazonalidade. Use 1 ano para média real.\n\n"
                "**2. Filial:** Apenas visual (filtra abas). O motor analisa todas as 5 lojas.\n\n"
                "**3. Cobertura de Vendas:** Dias de estoque desejados. Aumentar = Ideal maior = mais pedidos.\n\n"
                "**4. Tempo de Transporte:** Dias de viagem. Se subestimar, a loja zera antes do produto chegar.\n\n"
                "**5. Piso Exposição:** Mínimo na prateleira. Evita que produtos de baixo giro deixem a prateleira vazia.\n\n"
                "**6. Reserva Origem:** '%' que a origem guarda. Evita que a origem fique sem estoque após doar.\n\n"
                "**7 e 8. Atacado tem Piso/Reserva:** O Atacado é hub, não tem prateleira. Deixe 'Não'.\n\n"
                "**9. Reposição Recente:** Quarentena anti-gangorra. Bloqueia novos pedidos se já recebeu recentemente.\n\n"
                "**10. Dias em Trânsito:** Janela do que já foi enviado. Considera como 'em trânsito'.\n\n"
                "**11. Atacado tem Mínimo p/ Compra?:** Usa Piso como quantidade mínima de compra. Evita comprar volumes irrisórios."
            )

    # ---------------- ABA 4 - A Inteligência ----------------
    with tab4:
        st.header("Módulo 4: Lendo a Tela (A Inteligência do Motor)")
        st.markdown(
            "A tela de resultados não é apenas uma lista. Ela conta uma história. Veja como interpretar."
        )

        st.subheader("Ideal vs. Quantidade de Transferência")
        st.markdown(
            "Essa é a maior dúvida:\n"
            "- **Qtd Ideal:** É o tamanho do buraco (a meta).\n"
            "- **Qtd Transf.:** É a ação de hoje. O que falta para tapar o buraco.\n\n"
            "*Exemplo:* Ideal 100, Saldo 40. Transfere 60. O Ideal é a meta, a transferência é o passo."
        )

        st.subheader("O Livro dos Motivos (O que cada um significa?)")
        motivos = {
            "SEM ESTOQUE": "A loja está zerada e **não há nada no caminhão**. Alarme vermelho. Ação imediata.",
            "AGUARDANDO TRANSFERENCIA": "A loja tem falta, **MAS** já tem um caminhão cheio de produto indo para lá. Não mande de novo.",
            "RECEBIDO RECENTEMENTE": "A loja recebeu produto há poucos dias. Está de 'castigo' (quarentena) para não pedir duplicado.",
            "URGENTE - zera hoje": "O estoque acaba em menos de 24 horas. Ação imediata.",
            "URGENTE - zera em N dias": "Vai acabar logo. Você tem alguns dias para agir.",
            "Origem parada, destino vendendo": "A loja doadora quase não vende, mas a receptora vende muito. O sistema move o produto para onde ele gira.",
            "Alta rotacao no destino": "A loja receptora vende o dobro da doadora.",
            "Maior giro no destino": "A loja receptora vende 1.5x mais que a doadora.",
            "Reposicao de ciclo": "Fluxo normal. Nada de errado.",
            "ESTOQUE COMPLEMENTAR": "**Motivo de compra.** A rede tem um pouco do produto, mas não o suficiente. Compre só o que falta.",
            "ESTOQUE PARADO": "**Liquidar.** O produto tem estoque, mas a velocidade de venda é zero.",
            "FIM DE CICLO": "**Descontinuar.** O produto vende muito pouco. Venda o estoque e tire do mix."
        }
        for k, v in motivos.items():
            st.markdown(f"**{k}:** {v}")

    # ---------------- ABA 5 - O Protocolo ----------------
    with tab5:
        st.header("Módulo 5: O Protocolo de Ação (O Dia a Dia)")
        st.markdown(
            "Como transformar os dados em ação na sua rotina."
        )

        st.subheader("Sua Rotina Semanal")
        st.markdown(
            "**Segunda-feira (10 min):**\n"
            "1. Abra o app.\n"
            "2. Escolha o Perfil de Análise.\n"
            "3. Escolha o Fabricante.\n"
            "4. Clique em Consultar.\n"
            "5. Filtre por Prioridade Crítica.\n\n"
            "**Terça a Quinta (Ação):**\n"
            "1. Leia o Motivo.\n"
            "2. Confirme a Qtd.\n"
            "3. Gere o PDF.\n"
            "4. Crie a ordem no ERP.\n"
            "5. Se houver itens em COMPRAR, envie a lista para o time de Compras.\n\n"
            "**Sexta-feira (10 min):**\n"
            "1. Reabra o app.\n"
            "2. Compare com a semana anterior.\n"
            "3. Ajuste parâmetros se necessário."
        )

        st.subheader("Cenários Reais (O que fazer?)")
        with st.expander("Cenário 1: Produto em falta crítica (RECEBER)"):
            st.markdown(
                "**O que vejo:** Fita Adesiva, 85 un, Motivo: `URGENTE - zera hoje`.\n"
                "**Ação:** Gere o PDF, envie para o Atacado, crie a ordem no ERP."
            )

        with st.expander("Cenário 2: A rede inteira está sem estoque (COMPRAR)"):
            st.markdown(
                "**O que vejo:** Fita Crepe na aba COMPRAR do Atacado, Sugestão 50.\n"
                "**Ação:** Nenhuma loja tem. Envie a lista para o time de Compras."
            )

        with st.expander("Cenário 3: O produto já está a caminho (AGUARDANDO)"):
            st.markdown(
                "**O que vejo:** Papel Kraft, Em Trânsito: 20 un.\n"
                "**Ação:** O caminhão já saiu. Apenas aguarde a entrega."
            )

        with st.expander("Cenário 4: O produto está encalhado (LIQUIDAR)"):
            st.markdown(
                "**O que vejo:** Squeeze Halloween, Motivo: `ESTOQUE PARADO`.\n"
                "**Ação:** O sistema NÃO vai transferir. Ação comercial: promoção local ou devolução."
            )

        with st.expander("Cenário 5: O produto tem giro baixo (DESCONTINUAR)"):
            st.markdown(
                "**O que vejo:** Fita Cetim Vermelha, Motivo: `FIM DE CICLO`.\n"
                "**Ação:** Vender até o fim do estoque. Não comprar mais."
            )

        st.subheader("Ajustes Frequentes")
        with st.expander("A sugestão parece errada. O que faço?"):
            st.markdown("1. Leia o Motivo.\n2. Confira o Saldo e o Em Trânsito.\n3. Verifique movimentações estranhas.\n4. Se nada explicar, acione o TI.")

        with st.expander("Como ajustar se estiver sugerindo MUITO?"):
            st.markdown("- Aumente a Reposição Recente (15 -> 30).\n- Aumente a Reserva Origem (25% -> 40%).\n- Diminua a Cobertura (30 -> 15).")

        with st.expander("Como ajustar se estiver sugerindo POUCO?"):
            st.markdown("- Diminua a Reposição Recente (15 -> 7).\n- Diminua a Reserva Origem (25% -> 15%).\n- Aumente a Cobertura (30 -> 45).")

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")