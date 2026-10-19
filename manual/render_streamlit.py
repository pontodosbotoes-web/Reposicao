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
        # Substitui quebras de linha por espaços para não quebrar a tabela markdown
        row_clean = [str(cell).replace("\n", " ") for cell in row]
        md += "| " + " | ".join(row_clean) + " |\n"
    st.markdown(md)


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
        render_tabela(["Nível", "Estado"], [
            ["100% (Ideal)", "Tudo perfeito"],
            ["80%", "Atenção"],
            ["40%", "Crítico"],
            ["0% (Ruptura)", "Urgente"]
        ])

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
        render_tabela(["Filial", "Saldo", "Ideal", "Excesso", "Falta"], [
            ["Atacado", "500", "100", "400", "0"],
            ["Alecrim", "30", "50", "0", "20"],
            ["Via Direta", "80", "40", "40", "0"],
            ["Zona Sul", "15", "60", "0", "45"],
            ["Zona Norte", "70", "55", "15", "0"]
        ])

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
        render_tabela(["Área", "O que tem"], [
            ["Topo", "Título 'Reposição de Produtos'"],
            ["Linha 1", "6 filtros: Perfil, Fabricante, Depto, Grupo, Subgrupo, Produto"],
            ["Botões", "Consultar, Limpar, Parâmetros e Manual"],
            ["Aviso", "Faixa azul quando o Produto está preenchido"],
            ["Parâmetros", "Aparece ao clicar em Parâmetros (3 linhas)"],
            ["Resultados", "Aparece após consultar (5 abas por filial)"]
        ])

        st.header("3.3 Problemas comuns")
        render_tabela(["Problema", "Solução"], [
            ["App 'dormindo'", "Clicar em 'Yes, get this app back up!'"],
            ["Tela em branco", "Atualizar navegador"],
            ["Erro de conexão", "Testar em outra rede"],
            ["Consulta não retorna", "Aguardar 5 min e tentar"]
        ])

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
                ["Reserva Origem", "25%", "0%", "40%", "15%", "15%", "5%", "30%", "0%"],
                ["Atacado tem Piso?", "Não", "Não", "Não", "Não", "Não", "Não", "Não", "Não"],
                ["Atacado tem Reserva?", "Não", "Não", "Não", "Não", "Não", "Não", "Não", "Não"],
                ["Reposição Recente", "15", "7", "7", "7", "7", "5", "20", "30"],
                ["Dias em Trânsito", "10", "10", "7", "7", "10", "7", "10", "10"]
            ]
        )

        st.header("4.2 Busca Avançada de Produto")
        st.markdown("O campo **Produto** varre **4 fontes**: código interno, referência do fabricante, nome/descrição e código de barras (GTIN).")
        render_tabela(["Você digita", "O que o sistema faz"], [
            ["CAIXA QUADRADA", "Acha produtos que tenham CAIXA E QUADRADA"],
            ["CAPA, CAPUZ", "Acha produtos com CAPA OU CAPUZ"],
            ["CAIXA QUADRADA, CAPA", "Acha (CAIXA E QUADRADA) OU CAPA"]
        ])
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
        render_tabela(["Prioridade", "Critério", "Ação"], [
            ["Crítica", "Zera em menos de 7 dias", "Transferir hoje"],
            ["Alta", "Zera de 7 a 14 dias", "Esta semana"],
            ["Normal", "Zera em 15 dias ou mais (ou sem projeção)", "Fluxo regular"]
        ])
        st.caption("💡 *Dias p/ Zerar usa a Velocidade Ativa (dias em que efetivamente vendeu).*")

        st.header("5.3 Motivos possíveis")
        render_tabela(["Motivo", "Significado"], [
            ["SEM ESTOQUE", "Já zerou — urgente"],
            ["AGUARDANDO TRANSFERENCIA", "Saldo Provável <= 0 E tem envio a caminho"],
            ["RECEBIDO RECENTEMENTE", "Recebeu nos últimos N dias (parâmetro Reposição Recente)"],
            ["URGENTE - zera em N dias", "Vai zerar em breve"],
            ["Origem parada, destino vendendo", "Origem com velocidade < 0.05 e destino >= 0.1"],
            ["Alta rotação no destino", "Destino vende 2x mais que origem"],
            ["Maior giro no destino", "Destino vende 1.5x mais que origem"],
            ["Reposição de ciclo", "Padrão — mantém fluxo"]
        ])

        st.header("5.4 Ações de Fim de Linha (Liquidar e Descontinuar)")
        st.markdown(
            "Quando um produto não vende em nenhuma filial, transferi-lo gera custo de frete "
            "e não resolve a venda. O sistema cria duas seções exclusivas:"
        )
        render_tabela(["Ação", "Quando acontece?", "O que o gestor deve fazer?"], [
            ["LIQUIDAR", "Velocidade exata ZERO em toda a rede, mas há estoque.", "Não transferir. Promoção, queima ou devolver ao fornecedor."],
            ["DESCONTINUAR", "Velocidade > 0 mas < 0.1 (fim de ciclo), com estoque.", "Vender até o fim do estoque. Não repor e retirar do mix."]
        ])
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
        render_tabela(["Ajuste", "Efeito"], [
            ["Aumentar Reposição Recente (15 -> 30)", "Bloqueia por mais tempo"],
            ["Aumentar Reserva Origem (25% -> 40%)", "Origem doa menos"],
            ["Diminuir Cobertura (30 -> 15)", "Ideal menor"]
        ])

        st.subheader("Cenário B — Sugerindo transferência de menos")
        render_tabela(["Ajuste", "Efeito"], [
            ["Diminuir Reposição Recente (15 -> 7)", "Bloqueia menos"],
            ["Diminuir Reserva Origem (25% -> 15%)", "Origem doa mais"],
            ["Aumentar Cobertura (30 -> 45)", "Ideal maior"]
        ])

        st.subheader("Cenário C — Produto sempre zerado")
        render_tabela(["Ajuste", "Efeito"], [
            ["Aumentar Piso Exposição (0 -> 5)", "Mínimo maior na prateleira"],
            ["Aumentar Cobertura", "Ideal maior"],
            ["Verificar Tempo de Transporte", "Corrigir se subestimado"]
        ])

        st.subheader("Cenário D — Duplicidade de envio")
        render_tabela(["Ajuste", "Efeito"], [
            ["Aumentar Dias em Trânsito (10 -> 15)", "Cobre mais tempo"],
            ["Aumentar Reposição Recente (15 -> 25)", "Quarentena maior"]
        ])
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
        render_tabela(["Termo", "Definição"], [
            ["Base", "Consulta SQL que traz todos os produtos x filial"],
            ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir"],
            ["Dias em Trânsito", "Período entre envio e recebimento"],
            ["Estoque Ideal", "max(Piso, VelocPeriodo x (Cob + Lead))"],
            ["Excesso", "Saldo Ajustado acima do Ideal"],
            ["Falta", "Saldo Ajustado abaixo do Ideal"],
            ["Hub", "Filial central (Atacado)"],
            ["Matriz de Proximidade", "Regra de quem ajuda quem"],
            ["MOQ", "Minimum Order Quantity - mínimo de 5 un por transferência"],
            ["Piso Exposição", "Quantidade mínima na prateleira"],
            ["Reposição Recente", "Bloqueio parcial pós-recebimento"],
            ["Reserva Origem", "% do excesso que fica na origem (ceil)"],
            ["Saldo Ajustado", "SaldoProvavel + QtdEmTransito"],
            ["Saldo Provável", "Estoque calculado (compras + recebidas - enviadas - vendidas)"],
            ["Tempo de Transporte", "Dias entre envio e entrega"],
            ["Velocidade Ativa", "Vendas / dias com venda (usada em Dias p/ Zerar)"],
            ["Velocidade Período", "Vendas / dias corridos (usada no Estoque Ideal)"]
        ])

    # ---------------- ABA 10 - Casos Práticos ----------------
    with tab10:
        st.header("Casos Práticos")
        st.markdown("Estes casos mostram situações reais do dia a dia e como o sistema reage a cada uma.")

        with st.expander("Caso 1 — Produto em falta crítica (RECEBER)"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias", "Motivo"], [
                ["1", "Crítica", "562351", "FITA ADESIVA", "Atacado", "85", "3", "URGENTE"]
            ])
            st.markdown("**Ação:** gerar PDF, enviar para o Atacado, criar ordem no ERP.")

        with st.expander("Caso 2 — Produto com excesso (ENVIAR)"):
            st.markdown("**Aba Atacado (ENVIAR):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Destino", "Qtd", "Reserva"], [
                ["1", "Normal", "627893", "FITA PAPEL", "Alecrim", "50", "20"],
                ["2", "Normal", "627893", "FITA PAPEL", "Via Direta", "30", "20"]
            ])
            st.markdown("**Ação:** confirmar rota, gerar PDF, criar 2 ordens (uma por destino).")

        with st.expander("Caso 3 — Transferência entre lojas (sem passar pelo Atacado)"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias"], [
                ["5", "Alta", "612202", "SUSPENSORIO", "Via Direta", "20", "10"]
            ])
            st.markdown("**Ação:** confirmar com a Via Direta, gerar PDF, criar ordem no ERP.")

        with st.expander("Caso 4 — Nenhuma sugestão encontrada"):
            st.markdown("**Mensagem:** 'Nenhuma sugestão encontrada'")
            st.markdown("O que fazer:")
            st.markdown("- Confirmar se os produtos estão equilibrados\n- Tentar afrouxar a Cobertura (ex.: 15 dias)\n- Tentar outro período de análise (ex.: 6 meses)\n- Verificar se o filtro de Fabricante não está muito restritivo")

        with st.expander("Caso 5 — Produto parado: LIQUIDAR"):
            st.markdown("**Aba Zona Norte (LIQUIDAR):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Liq.", "Motivo"], [
                ["1", "Normal", "771234", "SQUEEZE HALLOWEEN", "UN", "CASA FESTA", "15", "ESTOQUE PARADO"]
            ])
            st.markdown("**Por que caiu aqui?** O produto não teve NENHUMA venda (velocidade zero) nos últimos 365 dias em toda a rede, mas a Zona Norte tem 15 unidades no estoque.")
            st.markdown("**O que o sistema faz:** Não sugere transferir para outras lojas. Transferir um produto que não vende só gasta frete e não gera receita.")
            st.markdown("**Ação:** Criar uma promoção local, fazer um kit com outro produto, ou devolver ao fornecedor.")

        with st.expander("Caso 6 — Produto de fim de ciclo: DESCONTINUAR"):
            st.markdown("**Aba Alecrim (DESCONTINUAR):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Desc.", "Motivo"], [
                ["1", "Normal", "554433", "FITA CETIM VERMELHA", "UN", "ADERE", "8", "FIM DE CICLO"]
            ])
            st.markdown("**Por que caiu aqui?** O produto tem uma velocidade de venda muito baixa (ex: 0.08 un/dia, ou seja, 1 unidade a cada 12 dias) na rede inteira. O ciclo de vida dele acabou.")
            st.markdown("**O que o sistema faz:** Não sugere reposição. Você deve vender o que tem e não comprar mais.")
            st.markdown("**Ação:** Vender até o fim do estoque atual. Não fazer novas compras e retirar o item do mix da loja quando zerar.")

        with st.expander("Caso 7 — Produto recém-recebido: AGUARDANDO QUARENTENA"):
            st.markdown("**Aba Zona Sul (RECEBER):**")
            render_tabela(["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias", "Motivo"], [
                ["3", "Alta", "889900", "PAPEL KRAFT", "Atacado", "40", "5", "RECEBIDO RECENTEMENTE"]
            ])
            st.markdown("**Por que caiu aqui?** A Zona Sul ainda tem uma falta projetada, mas recebeu uma transferência deste produto nos últimos 15 dias (parâmetro Reposição Recente).")
            st.markdown("**O que o sistema faz:** Mostra o alerta para você saber que a falta existe, mas a origem já mandou algo recentemente. Ele evita mandar de novo (efeito gangorra).")
            st.markdown("**Ação:** Verificar fisicamente na loja. Se a transferência anterior já cobre a falta, não fazer nada. Se não chegou, acionar a transportadora.")

        with st.expander("Caso 8 — Falta pequena: A REGRA DO MÍNIMO DE 5"):
            st.markdown("Você consulta e nota que o produto 'Fita Refletiva' tem falta de 3 unidades na Zona Norte, mas ele **não aparece** no sistema.")
            st.markdown("**Por que não aparece?** O motor ignora transferências menores que 5 unidades em todas as regras. É o MOQ (Minimum Order Quantity).")
            st.markdown("**O que fazer:** O custo logístico (frete, separação, embalagem) para mover 3 unidades é maior que o benefício. Deixe o produto seguir o fluxo natural ou aguarde acumular uma falta maior.")

    st.markdown("---")
    st.caption("Manual do Gestor — Reposição de Produtos | Uso interno")