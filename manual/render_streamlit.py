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

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "🏁 Introdução",
        "🧠 Como Pensa",
        "🚪 Primeiro Acesso",
        "🎛️ Filtros & Parâmetros",
        "📊 Resultado",
        "📅 Rotina",
        "🔧 Ajustes",
        "❓ FAQ",
        "📚 Glossário",
        "🛠️ Casos Práticos",
    ])

    # ---------------- ABA 1 - Introdução ----------------
    with tab1:
        st.header("1.1 Por que este sistema existe")
        st.markdown(
            "Imagine o dia a dia de uma rede com **5 filiais** e **milhares de produtos**. "
            "Todos os dias você precisa responder:"
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

        st.subheader("1.2 O que o sistema faz")
        st.markdown(
            "✅ **1. Analisa** histórico de vendas\n\n"
            "✅ **2. Calcula** o estoque ideal de cada filial\n\n"
            "✅ **3. Identifica** excesso (doador) e falta (receptor)\n\n"
            "✅ **4. Sugere** qual filial envia, para quem, e quanto\n\n"
            "✅ **5. Prioriza** por urgência\n\n"
            "✅ **6. Gera** relatórios em PDF por filial"
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
            "quem tem de menos é sugerido como **receptor**. O **Atacado** entra "
            "como hub principal, e as **lojas próximas** se ajudam quando faz sentido."
        )

        st.subheader("1.5 De onde vem a inteligência")
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

    # ---------------- ABA 2 - Como Pensa ----------------
    with tab2:
        st.header("2.1 A metáfora da caixa d'água")
        st.markdown("Imagine que cada filial é uma **caixa d'água**. O sistema tenta manter cada caixa no nível ideal:")
        st.table({
            "Nível": ["100% (Ideal)", "80%", "40%", "0% (Ruptura)"],
            "Estado": ["Tudo perfeito", "Atenção", "Crítico", "Urgente"]
        })

        st.header("2.2 Estoque Ideal")
        st.code("Estoque Ideal = max(Piso Exposição, Velocidade Período x (Cobertura + Tempo de Transporte))", language="text")
        st.warning(
            "**Atenção:** O **Piso Exposição** garante um mínimo na prateleira, mesmo que a velocidade seja baixa. "
            "E a velocidade usada é a **Período** (vendas / dias corridos), não a Ativa."
        )

        st.markdown("**Exemplo Prático (Fita Adesiva 3M):**")
        st.markdown(
            "- Vendas nos últimos 365 dias: 1.825 un\n"
            "- Velocidade: 1.825 / 365 = **5 un/dia**\n"
            "- Cobertura: **30 dias** | Tempo de Transporte: **10 dias** | Soma: **40 dias**\n"
            "- **Estoque Ideal = 5 x 40 = 200 unidades**"
        )

        st.header("2.3 Excesso e Falta")
        st.code("Excesso = Saldo Ajustado - Estoque Ideal\nFalta   = Estoque Ideal - Saldo Ajustado", language="text")
        st.info(
            "**Saldo Ajustado** = Saldo Provável + Qtd Em Trânsito. O sistema **sempre** usa o "
            "Saldo Ajustado — nunca o saldo puro — para não sugerir transferência duplicada."
        )

        st.markdown("**Exemplo com 5 filiais:**")
        st.table({
            "Filial": ["Atacado", "Alecrim", "Via Direta", "Zona Sul", "Zona Norte"],
            "Saldo": [500, 30, 80, 15, 70],
            "Ideal": [100, 50, 40, 60, 55],
            "Excesso": [400, 0, 40, 0, 15],
            "Falta": [0, 20, 0, 45, 0]
        })

        st.header("2.4 A Matriz de Proximidade")
        st.markdown("Quem ajuda quem:")
        st.table({
            "Destino": ["Alecrim", "Via Direta", "Zona Sul", "Zona Norte", "Atacado"],
            "Ordem de prioridade dos doadores": [
                "1º Atacado, 2º Via Direta, 3º Zona Sul, 4º Zona Norte",
                "1º Atacado, 2º Alecrim, 3º Zona Sul",
                "1º Atacado, 2º Alecrim, 3º Via Direta",
                "1º Atacado, 2º Alecrim",
                "Nunca recebe"
            ]
        })

        st.header("2.5 Regra do Mínimo de 5 unidades (MOQ)")
        st.markdown(
            "O motor **ignora transferências menores que 5 unidades** em todas as regras: "
            "só sugere se a Falta for >= 5 e se o Excesso Transferível for >= 5. "
            "Esse é um **MOQ interno** (Minimum Order Quantity): abaixo desse volume, "
            "o custo logístico da transferência supera o ganho de disponibilidade."
        )
        st.caption("💡 *Amazon usa o mesmo princípio para transferências entre centros de distribuição.*")

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
        st.table({
            "Área": ["Topo", "Linha 1", "Botões", "Aviso", "Parâmetros", "Resultados"],
            "O que tem": [
                "Título 'Reposição de Produtos'",
                "6 filtros: Perfil, Fabricante, Depto, Grupo, Subgrupo, Produto",
                "Consultar, Limpar, Parâmetros e Manual",
                "Faixa azul quando o Produto está preenchido",
                "Aparece ao clicar em Parâmetros (3 linhas)",
                "Aparece após consultar (5 abas por filial)"
            ]
        })

        st.header("3.3 Problemas comuns")
        st.table({
            "Problema": ["App 'dormindo'", "Tela em branco", "Erro de conexão", "Consulta não retorna"],
            "Solução": ["Clicar em 'Yes, get this app back up!'", "Atualizar navegador", "Testar em outra rede", "Aguardar 5 min e tentar"]
        })

    # ---------------- ABA 4 - Filtros e Parâmetros ----------------
    with tab4:
        st.header("4.1 Perfil de Análise")
        st.markdown(
            "O **Perfil de Análise** configura automaticamente os 9 parâmetros do motor. "
            "Um mesmo produto pode ser analisado com perfis diferentes, dependendo do seu momento de vida."
        )
        st.info(
            "**Como ele interage com os Parâmetros?** Ao trocar o Perfil, o sistema sobrescreve "
            "os 9 parâmetros no painel. Se você mudar manualmente um parâmetro, o sistema respeitará "
            "sua alteração. Para voltar ao padrão, clique em **Limpar** (🧹)."
        )

        st.table({
            "Perfil": ["Padrão", "Lançamento", "Classe A", "Alto Giro", "Sazonal Longo", "Sazonal Curto", "Baixo Giro", "Liquidação"],
            "Quando usar": ["Uso geral", "Produto novo/coleção", "Maior faturamento", "Venda rápida constante", "Campanhas longas", "Pico explosivo", "Produtos encalhados", "Fim de ciclo / queima"],
            "Exemplo do Dia a Dia": ["Materiais contínuos", "Nova coleção de tecidos", "Fita adesiva básica, papel kraft", "Bexigas de aniversário", "Artigos de Natal em novembro", "Máscaras de Halloween", "Tecido de seda (1 rolo/mês)", "Itens de Halloween na 1ª sem. nov"]
        })

        st.subheader("Os 9 parâmetros de cada perfil (tabela técnica)")
        st.table({
            "Parâmetro": ["Período análise", "Cobertura", "Lead time", "Piso Exposição", "Reserva Origem", "Atacado tem Piso?", "Atacado tem Reserva?", "Reposição Recente", "Dias em Trânsito"],
            "Padrão": ["1 ano", "30d", "10", "0", "25%", "Não", "Não", "15", "10"],
            "Lanç.": ["30d", "30d", "10", "5", "0%", "Não", "Não", "7", "10"],
            "Classe A": ["3m", "15d", "7", "10", "40%", "Não", "Não", "7", "7"],
            "Alto Giro": ["3m", "15d", "7", "5", "15%", "Não", "Não", "7", "7"],
            "Saz.Longo": ["2m", "30d", "10", "5", "15%", "Não", "Não", "7", "10"],
            "Saz.Curto": ["30d", "15d", "7", "3", "5%", "Não", "Não", "5", "7"],
            "Baixo Giro": ["1 ano", "30d", "10", "3", "30%", "Não", "Não", "20", "10"],
            "Liquid.": ["6m", "7d", "10", "0", "0%", "Não", "Não", "30", "10"]
        })

        st.header("4.2 Busca Avançada de Produto")
        st.markdown("O campo **Produto** varre **4 fontes**: código interno, referência do fabricante, nome/descrição e código de barras (GTIN).")
        st.table({
            "Você digita": ["CAIXA QUADRADA", "CAPA, CAPUZ", "CAIXA QUADRADA, CAPA"],
            "O que o sistema faz": ["Acha produtos que tenham CAIXA E QUADRADA", "Acha produtos com CAPA OU CAPUZ", "Acha (CAIXA E QUADRADA) OU CAPA"]
        })
        st.warning(
            "**Regra especial — Produto é exclusivo:** Quando você digita algo em Produto, "
            "o sistema **ignora** Fabricante, Departamento, Grupo, Subgrupo e Filial. Busca em toda a rede."
        )

    # ---------------- ABA 5 - Resultado ----------------
    with tab5:
        st.header("5.1 Como ler o resultado")
        st.markdown(
            "Após consultar, você verá 5 abas (ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE). "
            "Cada uma mostra: **ENVIAR**, **RECEBER**, **DESCONTINUAR** e **LIQUIDAR**."
        )

        st.header("5.2 Prioridades")
        st.table({
            "Prioridade": ["Crítica", "Alta", "Normal"],
            "Critério": ["Zera em menos de 7 dias", "Zera de 7 a 14 dias", "Zera em 15 dias ou mais (ou sem projeção)"],
            "Ação": ["Transferir hoje", "Esta semana", "Fluxo regular"]
        })
        st.caption("💡 *Dias p/ Zerar usa a Velocidade Ativa (dias em que efetivamente vendeu).*")

        st.header("5.3 Motivos possíveis")
        st.table({
            "Motivo": ["SEM ESTOQUE", "AGUARDANDO TRANSFERENCIA", "RECEBIDO RECENTEMENTE", "URGENTE - zera em N dias", "Origem parada, destino vendendo", "Alta rotação no destino", "Maior giro no destino", "Reposição de ciclo"],
            "Significado": ["Já zerou — urgente", "Saldo Provável <= 0 E tem envio a caminho", "Recebeu nos últimos N dias", "Vai zerar em breve", "Origem com velocidade < 0.05 e destino >= 0.1", "Destino vende 2x mais que origem", "Destino vende 1.5x mais que origem", "Padrão — mantém fluxo"]
        })

        st.header("5.4 Ações de Fim de Linha (Liquidar e Descontinuar)")
        st.markdown(
            "Quando um produto não vende em nenhuma filial, transferi-lo gera custo de frete "
            "e não resolve a venda. O sistema cria duas seções exclusivas:"
        )
        st.table({
            "Ação": ["LIQUIDAR", "DESCONTINUAR"],
            "Quando acontece?": ["Velocidade exata ZERO em toda a rede, mas há estoque.", "Velocidade > 0 mas < 0.1 (fim de ciclo), com estoque."],
            "O que o gestor deve fazer?": ["Não transferir. Promoção, queima ou devolver ao fornecedor.", "Vender até o fim do estoque. Não repor e retirar do mix."]
        })
        st.info("**O Atacado nunca entra em LIQUIDAR/DESCONTINUAR** - apenas as lojas (filiais 1 a 4).")

        st.header("5.5 Reposição Recente (Anti-gangorra)")
        st.markdown(
            "A **Reposição Recente** não bloqueia cegamente toda nova transferência. "
            "Ela bloqueia apenas quando o que já foi recebido **cobre ou supera** a falta atual. "
            "Se recebeu 20 un e a falta continua em 50 un, o produto **volta a ser elegível**."
        )
        st.caption("💡 *Esse comportamento evita o Efeito Chicote (estudo clássico da P&G com fraldas Pampers).*")

        st.header("5.6 Reserva Origem")
        st.markdown("A Reserva é calculada como **ceil** (arredonda para cima) do percentual sobre o Excesso. Ex.: Excesso 45, Reserva 25% -> 12 un (11.25 arredondado).")

    # ---------------- ABA 6 - Rotina ----------------
    with tab6:
        st.header("6.1 Segunda-feira (10 min)")
        st.markdown(
            "1. Abra o app\n"
            "2. Clique em Parâmetros e confira os padrões (Período='1 ano', Cobertura='30 dias', Tempo Transp=10)\n"
            "3. Escolha um Fabricante no topo\n"
            "4. Clique em Consultar (🔍)\n"
            "5. Filtre por Prioridade = Crítica"
        )
        st.header("6.2 Terça a Quinta (ação)")
        st.markdown(
            "Para cada produto crítico:\n"
            "1. Veja o **Motivo**\n"
            "2. Confirme a **Qtd Transf.**\n"
            "3. Verifique a **Origem**\n"
            "4. Clique em **Gerar PDF** (📄)\n"
            "5. Crie a ordem no ERP"
        )
        st.header("6.3 Sexta-feira (10 min)")
        st.markdown("1. Reabra o app\n2. Compare com a semana anterior\n3. Ajuste parâmetros se necessário")

    # ---------------- ABA 7 - Ajustes ----------------
    with tab7:
        st.header("Cenários e Soluções")
        
        st.subheader("Cenário A — Sugerindo transferência demais")
        st.table({
            "Ajuste": ["Aumentar Reposição Recente (15 -> 30)", "Aumentar Reserva Origem (25% -> 40%)", "Diminuir Cobertura (30 -> 15)"],
            "Efeito": ["Bloqueia por mais tempo", "Origem doa menos", "Ideal menor"]
        })

        st.subheader("Cenário B — Sugerindo transferência de menos")
        st.table({
            "Ajuste": ["Diminuir Reposição Recente (15 -> 7)", "Diminuir Reserva Origem (25% -> 15%)", "Aumentar Cobertura (30 -> 45)"],
            "Efeito": ["Bloqueia menos", "Origem doa mais", "Ideal maior"]
        })

        st.subheader("Cenário C — Produto sempre zerado")
        st.table({
            "Ajuste": ["Aumentar Piso Exposição (0 -> 5)", "Aumentar Cobertura", "Verificar Tempo de Transporte"],
            "Efeito": ["Mínimo maior na prateleira", "Ideal maior", "Corrigir se subestimado"]
        })

        st.subheader("Cenário D — Duplicidade de envio")
        st.table({
            "Ajuste": ["Aumentar Dias em Trânsito (10 -> 15)", "Aumentar Reposição Recente (15 -> 25)"],
            "Efeito": ["Cobre mais tempo", "Quarentena maior"]
        })
        st.warning("**Nota:** Nunca mude 2 parâmetros ao mesmo tempo. Assim você não sabe qual causou o efeito.")

    # ---------------- ABA 8 - FAQ ----------------
    with tab8:
        st.header("Perguntas frequentes (20)")
        faq = [
            ("O sistema demora quanto para carregar?", "Com filtro de fabricante: 30-60 segundos. Sem filtro: pode demorar mais."),
            ("Posso deixar em branco todos os filtros?", "Não. Escolha pelo menos um."),
            ("Por que meu produto não aparece?", "Várias causas: não vendeu no período, está nos departamentos INATIVO/USO INTERNO, não tem excesso nem falta, o filtro excluiu, ou o produto foi removido automaticamente (ver próxima pergunta)."),
            ("Por que meu produto sumiu da análise automaticamente?", "Se o produto não vendeu (velocidade < 0.1) em NENHUMA filial E não tem saldo em NENHUMA, ele é removido. Volta a aparecer quando houver venda ou estoque."),
            ("A sugestão parece errada. O que faço?", "1. Verifique o Motivo. 2. Confira movimentações estranhas. 3. Verifique o Período. 4. Se persistir, acione TI."),
            ("Posso mudar os parâmetros toda hora?", "Não recomendo. Deixe padrão por 15 dias antes de mexer."),
            ("O PDF pode ser editado?", "Não, é um PDF padrão."),
            ("Como sei se um produto é doador ou receptor?", "Doador: seção ENVIAR. Receptor: seção RECEBER."),
            ("Preciso anotar tudo?", "Não. Sempre confira o Motivo antes de aprovar."),
            ("Dois produtos competem pela mesma quantidade?", "O motor prioriza por urgência (Crítica -> Alta -> Normal)."),
            ("Como aciono o suporte?", "[Contato do responsável pelo projeto]"),
            ("Consigo ver o histórico de sugestões?", "Hoje não. Sugestão futura."),
            ("Posso exportar para Excel?", "Só PDF hoje."),
            ("Por que o 'Reserva' varia?", "É o percentual (padrão 25%) sobre o Excesso, arredondado para cima. Quanto maior o Excesso, maior a Reserva."),
            ("O que é 'AGUARDANDO TRANSFERENCIA'?", "O saldo projetado está <= 0 E já existe envio a caminho. Não duplica."),
            ("O que é 'RECEBIDO RECENTEMENTE'?", "Filial recebeu nos últimos N dias (parâmetro Reposição Recente). Está em quarentena."),
            ("Posso transferir tudo que o sistema sugere?", "Não. O programa não substitui o bom senso. Sempre confira antes."),
            ("Quando o Ideal é 0?", "Produtos sem venda no período E sem Piso Exposição configurado."),
            ("O sistema sugere menos de 5 unidades?", "Não. O motor ignora transferências < 5 un (MOQ interno para evitar custo logístico)."),
            ("Isso substitui o ERP?", "Não. É uma ferramenta de decisão. A execução continua no ERP."),
        ]
        for i, (pergunta, resposta) in enumerate(faq, 1):
            with st.expander(f"{i}. {pergunta}"):
                st.markdown(resposta)

    # ---------------- ABA 9 - Glossário ----------------
    with tab9:
        st.header("Glossário")
        st.table({
            "Termo": ["Base", "Cobertura de Vendas", "Dias em Trânsito", "Estoque Ideal", "Excesso", "Falta", "Hub", "Matriz de Proximidade", "MOQ", "Piso Exposição", "Reposição Recente", "Reserva Origem", "Saldo Ajustado", "Saldo Provável", "Tempo de Transporte", "Velocidade Ativa", "Velocidade Período"],
            "Definição": [
                "Consulta SQL que traz todos os produtos x filial",
                "Dias de venda que o produto deve cobrir",
                "Período entre envio e recebimento",
                "max(Piso, VelocPeriodo x (Cob + Lead))",
                "Saldo Ajustado acima do Ideal",
                "Saldo Ajustado abaixo do Ideal",
                "Filial central (Atacado)",
                "Regra de quem ajuda quem",
                "Minimum Order Quantity - mínimo de 5 un por transferência",
                "Quantidade mínima na prateleira",
                "Bloqueio parcial pós-recebimento",
                "% do excesso que fica na origem (ceil)",
                "SaldoProvavel + QtdEmTransito",
                "Estoque calculado (compras + recebidas - enviadas - vendidas)",
                "Dias entre envio e entrega",
                "Vendas / dias com venda (usada em Dias p/ Zerar)",
                "Vendas / dias corridos (usada no Estoque Ideal)"
            ]
        })

    # ---------------- ABA 10 - Casos Práticos ----------------
    with tab10:
        st.header("Casos Práticos")
        st.markdown("Estes casos mostram situações reais do dia a dia e como o sistema reage a cada uma.")

        with st.expander("Caso 1 — Produto em falta crítica (RECEBER)"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            st.table({
                "#": [1], "Prior.": ["Crítica"], "Cod": ["562351"], "Produto": ["FITA ADESIVA"], 
                "Origem": ["Atacado"], "Qtd": [85], "Dias": [3], "Motivo": ["URGENTE"]
            })
            st.markdown("**Ação:** gerar PDF, enviar para o Atacado, criar ordem no ERP.")

        with st.expander("Caso 2 — Produto com excesso (ENVIAR)"):
            st.markdown("**Aba Atacado (ENVIAR):**")
            st.table({
                "#": [1, 2], "Prior.": ["Normal", "Normal"], "Cod": ["627893", "627893"], 
                "Produto": ["FITA PAPEL", "FITA PAPEL"], "Destino": ["Alecrim", "Via Direta"], 
                "Qtd": [50, 30], "Reserva": [20, 20]
            })
            st.markdown("**Ação:** confirmar rota, gerar PDF, criar 2 ordens (uma por destino).")

        with st.expander("Caso 3 — Transferência entre lojas (sem passar pelo Atacado)"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            st.table({
                "#": [5], "Prior.": ["Alta"], "Cod": ["612202"], "Produto": ["SUSPENSORIO"], 
                "Origem": ["Via Direta"], "Qtd": [20], "Dias": [10]
            })
            st.markdown("**Ação:** confirmar com a Via Direta, gerar PDF, criar ordem no ERP.")

        with st.expander("Caso 4 — Nenhuma sugestão encontrada"):
            st.markdown("**Mensagem:** 'Nenhuma sugestão encontrada'")
            st.markdown("O que fazer:")
            st.markdown("- Confirmar se os produtos estão equilibrados\n- Tentar afrouxar a Cobertura (ex.: 15 dias)\n- Tentar outro período de análise (ex.: 6 meses)\n- Verificar se o filtro de Fabricante não está muito restritivo")

        with st.expander("Caso 5 — Produto parado: LIQUIDAR"):
            st.markdown("**Aba Zona Norte (LIQUIDAR):**")
            st.table({
                "#": [1], "Prior.": ["Normal"], "Cod": ["771234"], "Produto": ["SQUEEZE HALLOWEEN"], 
                "Emb.": ["UN"], "Fabricante": ["CASA FESTA"], "Qtd p/ Liq.": [15], "Motivo": ["ESTOQUE PARADO"]
            })
            st.markdown("**Por que caiu aqui?** O produto não teve NENHUMA venda (velocidade zero) nos últimos 365 dias em toda a rede, mas a Zona Norte tem 15 unidades no estoque.")
            st.markdown("**O que o sistema faz:** Não sugere transferir para outras lojas. Transferir um produto que não vende só gasta frete e não gera receita.")
            st.markdown("**Ação:** Criar uma promoção local, fazer um kit com outro produto, ou devolver ao fornecedor.")

        with st.expander("Caso 6 — Produto de fim de ciclo: DESCONTINUAR"):
            st.markdown("**Aba Alecrim (DESCONTINUAR):**")
            st.table({
                "#": [1], "Prior.": ["Normal"], "Cod": ["554433"], "Produto": ["FITA CETIM VERMELHA"], 
                "Emb.": ["UN"], "Fabricante": ["ADERE"], "Qtd p/ Desc.": [8], "Motivo": ["FIM DE CICLO"]
            })
            st.markdown("**Por que caiu aqui?** O produto tem uma velocidade de venda muito baixa (ex: 0.08 un/dia, ou seja, 1 unidade a cada 12 dias) na rede inteira. O ciclo de vida dele acabou.")
            st.markdown("**O que o sistema faz:** Não sugere reposição. Você deve vender o que tem e não comprar mais.")
            st.markdown("**Ação:** Vender até o fim do estoque atual. Não fazer novas compras e retirar o item do mix da loja quando zerar.")

        with st.expander("Caso 7 — Produto recém-recebido: AGUARDANDO QUARENTENA"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            st.table({
                "#": [3], "Prior.": ["Alta"], "Cod": ["889900"], "Produto": ["PAPEL KRAFT"], 
                "Origem": ["Atacado"], "Qtd": [40], "Dias": [5], "Motivo": ["RECEBIDO RECENTEMENTE"]
            })
            st.markdown("**Por que caiu aqui?** A Zona Sul ainda tem uma falta projetada, mas recebeu uma transferência deste produto nos últimos 15 dias (parâmetro Reposição Recente).")
            st.markdown("**O que o sistema faz:** Mostra o alerta para você saber que a falta existe, mas a origem já mandou algo recentemente. Ele evita mandar de novo (efeito gangorra).")
            st.markdown("**Ação:** Verificar fisicamente na loja. Se a transferência anterior já cobre a falta, não fazer nada. Se não chegou, acionar a transportadora.")

        with st.expander("Caso 8 — Falta pequena: A REGRA DO MÍNIMO DE 5"):
            st.markdown("Você consulta e nota que o produto 'Fita Refletiva' tem falta de 3 unidades na Zona Norte, mas ele **não aparece** no sistema.")
            st.markdown("**Por que não aparece?** O motor ignora transferências menores que 5 unidades em todas as regras. É o MOQ (Minimum Order Quantity).")
            st.markdown("**O que fazer:** O custo logístico (frete, separação, embalagem) para mover 3 unidades é maior que o benefício. Deixe o produto seguir o fluxo natural ou aguarde acumular uma falta maior.")

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")