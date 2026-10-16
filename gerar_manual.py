"""
Gera o PDF do Manual do Gestor - Reposição de Produtos.

Uso:
    python gerar_manual.py

Saída:
    Manual_Reposicao_Gestor.pdf (na pasta atual)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT


# ============================================================
# CANVAS COM CABEÇALHO E RODAPÉ
# ============================================================
class ManualCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        w, h = A4

        # Cabeçalho (a partir da 2ª página)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1E293B"))
            self.drawString(2 * cm, h - 1.2 * cm, "Manual do Gestor — Reposição de Produtos")

            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(2 * cm, h - 1.4 * cm, w - 2 * cm, h - 1.4 * cm)

        # Rodapé
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(2 * cm, 1.2 * cm, "Uso interno — Reposição de Produtos")
        self.drawRightString(w - 2 * cm, 1.2 * cm, f"Página {self._pageNumber} de {page_count}")


# ============================================================
# ESTILOS
# ============================================================
styles = getSampleStyleSheet()

ESTILO_CAPA_TITULO = ParagraphStyle(
    "CapaTitulo",
    parent=styles["Title"],
    fontSize=32,
    leading=38,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#1E293B"),
    spaceAfter=20,
)

ESTILO_CAPA_SUB = ParagraphStyle(
    "CapaSub",
    parent=styles["Normal"],
    fontSize=14,
    leading=20,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#475569"),
    spaceAfter=10,
)

ESTILO_H1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#0F172A"),
    spaceBefore=20,
    spaceAfter=12,
    borderColor=colors.HexColor("#1E293B"),
    borderWidth=0,
    borderPadding=0,
)

ESTILO_H2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#1E293B"),
    spaceBefore=14,
    spaceAfter=8,
)

ESTILO_H3 = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#334155"),
    spaceBefore=10,
    spaceAfter=6,
)

ESTILO_PARAGRAFO = ParagraphStyle(
    "Paragrafo",
    parent=styles["BodyText"],
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
)

ESTILO_BULLET = ParagraphStyle(
    "Bullet",
    parent=ESTILO_PARAGRAFO,
    leftIndent=15,
    bulletIndent=5,
    spaceAfter=4,
)

ESTILO_CODIGO = ParagraphStyle(
    "Codigo",
    parent=styles["Code"],
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#0F172A"),
    backColor=colors.HexColor("#F1F5F9"),
    borderColor=colors.HexColor("#CBD5E1"),
    borderWidth=0.5,
    borderPadding=6,
    spaceAfter=8,
)

ESTILO_NOTA = ParagraphStyle(
    "Nota",
    parent=styles["BodyText"],
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#475569"),
    backColor=colors.HexColor("#FEF3C7"),
    borderColor=colors.HexColor("#F59E0B"),
    borderWidth=0.5,
    borderPadding=6,
    spaceAfter=8,
)


# ============================================================
# HELPERS
# ============================================================
def p(texto, estilo=ESTILO_PARAGRAFO):
    return Paragraph(texto, estilo)


def h1(texto):
    return Paragraph(texto, ESTILO_H1)


def h2(texto):
    return Paragraph(texto, ESTILO_H2)


def h3(texto):
    return Paragraph(texto, ESTILO_H3)


def bullet(texto):
    return Paragraph(f"• {texto}", ESTILO_BULLET)


def nota(texto):
    return Paragraph(f"💡 <b>Nota:</b> {texto}", ESTILO_NOTA)


def tabela(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    return t


# ============================================================
# CONSTRUÇÃO DO PDF
# ============================================================
def gerar(buffer=None):
    destino = buffer if buffer is not None else "Manual_Reposicao_Gestor.pdf"
    doc = SimpleDocTemplate(
        destino,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    conteudo = []

    # ============================================================
    # CAPA
    # ============================================================
    conteudo.append(Spacer(1, 6 * cm))
    conteudo.append(p("Reposição de Produtos", ESTILO_CAPA_TITULO))
    conteudo.append(Spacer(1, 0.5 * cm))
    conteudo.append(p("Manual do Gestor", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Sistema de sugestão de transferências entre filiais", ESTILO_CAPA_SUB))
    conteudo.append(p("DRP · IST · MEIO", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Uso interno", ESTILO_CAPA_SUB))
    conteudo.append(PageBreak())

    # ============================================================
    # SUMÁRIO
    # ============================================================
    conteudo.append(h1("Sumário"))
    conteudo.append(p("Este manual está dividido em 10 partes:"))
    conteudo.append(Spacer(1, 0.3 * cm))

    itens_sumario = [
        ("Parte 1", "Introdução ao projeto"),
        ("Parte 2", "Como o sistema pensa"),
        ("Parte 3", "Primeiro acesso"),
        ("Parte 4", "Filtros e Parâmetros"),
        ("Parte 5", "Como ler o resultado"),
        ("Parte 6", "Rotina semanal"),
        ("Parte 7", "Ajustes finos"),
        ("Parte 8", "Perguntas frequentes"),
        ("Parte 9", "Glossário"),
        ("Parte 10", "Casos práticos"),
    ]
    for num, titulo in itens_sumario:
        conteudo.append(p(f"<b>{num}</b> — {titulo}"))
    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 1 — INTRODUÇÃO
    # ============================================================
    conteudo.append(h1("Parte 1 — Introdução ao projeto"))

    conteudo.append(h2("1.1 Por que este sistema existe"))
    conteudo.append(p(
        "Imagine o dia a dia de uma rede com <b>5 filiais</b> e <b>milhares de produtos</b>. "
        "Todos os dias você precisa responder:"
    ))
    conteudo.append(bullet("<b>Quanto</b> mandar de cada produto para cada loja?"))
    conteudo.append(bullet("<b>Quando</b> mandar?"))
    conteudo.append(bullet("Se uma loja tem <b>excesso</b> e outra tem <b>falta</b>, como fazer essa troca?"))
    conteudo.append(bullet("Como evitar que o Atacado mande produto demais para uma loja e de menos para outra?"))
    conteudo.append(bullet("Como não deixar prateleiras vazias sem inflar o estoque?"))
    conteudo.append(Spacer(1, 0.3 * cm))

    conteudo.append(p(
        "Antes deste sistema, essas decisões eram tomadas manualmente: telefonemas, planilhas, "
        "cálculos por intuição. Levava horas por semana e gerava erros frequentes. "
        "Com este sistema, o motor de reposição faz essas perguntas para <b>todos os produtos</b> "
        "em segundos, e ainda <b>prioriza</b> os mais urgentes."
    ))

    conteudo.append(h2("1.2 O que o sistema faz"))
    conteudo.append(p("<b>1. Analisa</b> o histórico de vendas e movimentações de todas as filiais"))
    conteudo.append(p("<b>2. Calcula</b> o estoque ideal que cada filial deveria ter"))
    conteudo.append(p("<b>3. Identifica</b> quem tem <b>excesso</b> (pode doar) e quem tem <b>falta</b> (precisa receber)"))
    conteudo.append(p("<b>4. Sugere</b> qual filial deve enviar, para qual filial, e em qual quantidade"))
    conteudo.append(p("<b>5. Prioriza</b> por urgência (o que zera primeiro vem no topo)"))
    conteudo.append(p("<b>6. Gera</b> relatórios em PDF por filial para o time executar"))

    conteudo.append(h2("1.3 O que o sistema NÃO faz"))
    conteudo.append(p("Para evitar confusão desde o início:"))
    conteudo.append(bullet("❌ <b>Não substitui sua decisão</b> — ele sugere, você aprova"))
    conteudo.append(bullet("❌ <b>Não executa transferências</b> — você cria a ordem no ERP"))
    conteudo.append(bullet("❌ <b>Não altera dados</b> no banco — é somente leitura"))
    conteudo.append(bullet("❌ <b>Não substitui o bom senso</b> — sempre confira o motivo antes de aprovar"))

    conteudo.append(h2("1.4 Em 1 parágrafo"))
    conteudo.append(nota(
        "O sistema olha os últimos <b>365 dias</b> de cada produto, calcula o <b>ritmo de venda</b> "
        "de cada filial, define <b>quanto cada uma precisa ter em estoque</b> para cobrir <b>30 dias</b> "
        "de venda + <b>10 dias</b> de transporte, e cruza tudo: quem tem demais é sugerido como "
        "<b>doador</b>, quem tem de menos é sugerido como <b>receptor</b>. O <b>Atacado</b> entra como "
        "hub principal, e as <b>lojas próximas</b> se ajudam quando faz sentido."
    ))

    conteudo.append(h2("1.5 De onde vem a inteligência"))
    conteudo.append(p("O motor foi construído com base em 3 práticas consolidadas no varejo mundial:"))

    conteudo.append(h3("🏛️ DRP — Distribution Requirements Planning"))
    conteudo.append(p("Planejamento de reposição baseado no <b>consumo real</b> de cada ponto de venda."))
    conteudo.append(p("<i>Empresas que usam: Walmart, Carrefour, Pão de Açúcar.</i>"))

    conteudo.append(h3("🔄 IST — Inter-Store Transfers"))
    conteudo.append(p("Transferências entre lojas para corrigir desequilíbrio enquanto a janela de venda está aberta."))
    conteudo.append(p("<i>Empresas que usam: Zara, H&M, Best Buy.</i>"))

    conteudo.append(h3("🌐 MEIO — Multi-Echelon Inventory Optimization"))
    conteudo.append(p("Otimização de inventário em toda a rede, com <b>hub central</b> para consolidar estoque."))
    conteudo.append(p("<i>Empresas que usam: Amazon, Coca-Cola, P&G.</i>"))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 2 — COMO O SISTEMA PENSA
    # ============================================================
    conteudo.append(h1("Parte 2 — Como o sistema pensa"))

    conteudo.append(h2("2.1 A metáfora da caixa d'água"))
    conteudo.append(p("Imagine que cada filial é uma <b>caixa d'água</b>. O sistema tenta manter cada caixa no nível ideal:"))
    conteudo.append(Spacer(1, 0.2 * cm))

    caixa = [
        ["Nível", "Estado"],
        ["100% (Ideal)", "Tudo perfeito"],
        ["80%", "Atenção"],
        ["40%", "Crítico"],
        ["0% (Ruptura)", "Urgente"],
    ]
    conteudo.append(tabela(caixa, col_widths=[6 * cm, 8 * cm]))
    conteudo.append(Spacer(1, 0.3 * cm))

    conteudo.append(h2("2.2 Como se calcula o tamanho da caixa (Estoque Ideal)"))
    conteudo.append(p("<b>Fórmula:</b>"))
    conteudo.append(p(
        "Estoque Ideal = Velocidade × (Cobertura de Vendas + Tempo de Transporte)",
        ESTILO_CODIGO
    ))

    conteudo.append(h3("Exemplo prático"))
    conteudo.append(p("Produto: Fita Adesiva 3M"))

    exemplo = [
        ["Variável", "Valor"],
        ["Vendas nos últimos 365 dias", "1.825 unidades"],
        ["Velocidade Período", "1.825 ÷ 365 = 5 un/dia"],
        ["Cobertura de Vendas", "30 dias"],
        ["Tempo de Transporte", "10 dias"],
        ["Soma", "40 dias"],
        ["Estoque Ideal", "5 × 40 = 200 unidades"],
    ]
    conteudo.append(tabela(exemplo, col_widths=[7 * cm, 7 * cm]))

    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(nota(
        "A loja deveria ter 200 unidades de Fita Adesiva para cobrir 30 dias de venda + "
        "10 dias de transporte. Se ela tem menos, precisa receber. Se tem mais, pode doar."
    ))

    conteudo.append(h2("2.3 Como se calculam Excesso e Falta"))
    conteudo.append(p("<b>Fórmulas:</b>"))
    conteudo.append(p("Excesso = Saldo Provável − Estoque Ideal   (quando positivo)", ESTILO_CODIGO))
    conteudo.append(p("Falta   = Estoque Ideal − Saldo Provável   (quando positivo)", ESTILO_CODIGO))

    conteudo.append(h3("Exemplo com 5 filiais"))

    exemplo2 = [
        ["Filial", "Saldo", "Ideal", "Excesso", "Falta"],
        ["Atacado", "500", "100", "400", "0"],
        ["Alecrim", "30", "50", "0", "20"],
        ["Via Direta", "80", "40", "40", "0"],
        ["Zona Sul", "15", "60", "0", "45"],
        ["Zona Norte", "70", "55", "15", "0"],
    ]
    conteudo.append(tabela(exemplo2, col_widths=[3.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm]))

    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(p("<b>Leitura</b>:"))
    conteudo.append(bullet("<b>Atacado</b> tem 400 un de excesso → doador principal"))
    conteudo.append(bullet("<b>Zona Sul</b> tem 45 un de falta → receptor urgente"))
    conteudo.append(bullet("<b>Alecrim</b> tem 20 un de falta → receptor"))
    conteudo.append(bullet("<b>Via Direta</b> tem 40 un de excesso → doador secundário"))

    conteudo.append(h2("2.4 Os 3 tipos de transferência que o motor faz"))

    conteudo.append(h3("🥇 Tipo 1 — Atacado → Loja (a mais comum)"))
    conteudo.append(p("O Atacado é o <b>hub central</b>. Ele sempre aparece como primeiro doador."))

    conteudo.append(h3("🥈 Tipo 2 — Loja → Loja (proximidade)"))
    conteudo.append(p("Quando o Atacado não tem excesso suficiente, as lojas próximas se ajudam."))

    conteudo.append(h3("🥉 Tipo 3 — Múltiplas origens"))
    conteudo.append(p("O motor combina origens para cobrir a falta total de uma filial."))

    conteudo.append(h2("2.5 A matriz de proximidade"))
    conteudo.append(p("Quem ajuda quem:"))
    conteudo.append(Spacer(1, 0.2 * cm))

    matriz = [
        ["Destino", "Ordem de prioridade dos doadores"],
        ["Alecrim", "1º Atacado, 2º Via Direta, 3º Zona Sul, 4º Zona Norte"],
        ["Via Direta", "1º Atacado, 2º Alecrim, 3º Zona Sul"],
        ["Zona Sul", "1º Atacado, 2º Alecrim, 3º Via Direta"],
        ["Zona Norte", "1º Atacado, 2º Alecrim"],
        ["Atacado", "🚫 Nunca recebe"],
    ]
    conteudo.append(tabela(matriz, col_widths=[4 * cm, 10 * cm]))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 3 — PRIMEIRO ACESSO
    # ============================================================
    conteudo.append(h1("Parte 3 — Primeiro acesso"))

    conteudo.append(h2("3.1 Como abrir"))
    conteudo.append(p("<b>Passo a passo:</b>"))
    conteudo.append(p("1. Abra o navegador (Chrome, Edge ou Firefox)"))
    conteudo.append(p("2. Digite na barra de endereço:"))
    conteudo.append(p("https://pb-reposicao.streamlit.app", ESTILO_CODIGO))
    conteudo.append(p("3. Pressione <b>Enter</b>"))

    conteudo.append(h3("Primeira vez do dia"))
    conteudo.append(p(
        "Se o app estiver 'dormindo', você verá um botão "
        "<b>'Yes, get this app back up!'</b>. Clique e aguarde ~30 segundos."
    ))

    conteudo.append(h2("3.2 Mapa visual da tela"))
    conteudo.append(p("Ao carregar, você verá:"))

    layout = [
        ["Área", "O que tem"],
        ["Topo", "Título 'Reposição de Produtos'"],
        ["Linha 1", "6 filtros: Perfil, Fabricante, Departamento, Grupo, Subgrupo e Produto"],
        ["Botões", "🔍 Consultar · 🧹 Limpar · ⚙️ Parâmetros · 📖 Manual"],
        ["Aviso", "Faixa azul aparece quando o Produto está preenchido"],
        ["Parâmetros", "Aparece ao clicar em ⚙️ (3 linhas agrupadas)"],
        ["Resultados", "Aparece após consultar (5 abas por filial)"],
    ]
    conteudo.append(tabela(layout, col_widths=[3.5 * cm, 10.5 * cm]))

    conteudo.append(h2("3.3 Problemas comuns"))
    problemas = [
        ["Problema", "Solução"],
        ["App 'dormindo'", "Clicar em 'Yes, get this app back up!'"],
        ["Tela em branco", "Atualizar navegador"],
        ["Erro de conexão", "Testar em outra rede"],
        ["Consulta não retorna", "Aguardar 5 min e tentar"],
    ]
    conteudo.append(tabela(problemas, col_widths=[5 * cm, 9 * cm]))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 4 — FILTROS E PARÂMETROS
    # ============================================================
    conteudo.append(h1("Parte 4 — Filtros e Parâmetros"))

    conteudo.append(h2("4.1 Perfil de Análise"))

    conteudo.append(p(
        "O <b>Perfil de Análise</b> ajusta automaticamente os 9 parâmetros do motor. "
        "Escolha um perfil no topo da tela e o sistema preenche tudo — depois você "
        "pode refinar individualmente no painel ⚙️ Parâmetros."
    ))

    perfis = [
        ["Perfil", "Quando usar", "Principais diferenças"],
        ["Padrão", "Uso geral", "1 ano de histórico, cobertura 30d, reserva 25%, quarentena 15d"],
        ["Sazonal", "Carnaval, São João, Natal", "30 dias de histórico, piso 3, reserva 10%, quarentena 7d"],
        ["Alto Giro", "Produtos que vendem muito rápido", "3 meses de histórico, cobertura 15d, lead 7d, piso 5"],
        ["Baixo Giro", "Produtos lentos, pouca saída", "1 ano de histórico, piso 3, reserva 30%, quarentena 20d"],
        ["Liquidação", "Fim de ciclo / queima de estoque", "6 meses de histórico, cobertura 7d, reserva 0%"],
    ]
    conteudo.append(tabela(perfis, col_widths=[2.5 * cm, 5 * cm, 6.5 * cm]))

    conteudo.append(nota(
        "Cada perfil sobrescreve todos os 9 parâmetros. Se você alterar um deles manualmente, "
        "o perfil continua aplicado nos demais."
    ))

    conteudo.append(Spacer(1, 0.3 * cm))


    conteudo.append(h2("4.2 Filtros do topo"))
    filtros = [
        ["Filtro", "O que faz"],
        ["Fabricante", "Nome do fabricante"],
        ["Departamento", "Categoria macro"],
        ["Grupo", "Subdivisão da categoria"],
        ["Subgrupo", "Nível mais específico"],
        ["Produto", "Busca por código, referência, nome ou código de barras. Aceita E / OU (veja Busca Avançada)"],
    ]
    conteudo.append(tabela(filtros, col_widths=[4 * cm, 10 * cm]))

    conteudo.append(nota("Escolha pelo menos 1 filtro antes de consultar."))

    conteudo.append(h2("4.3 Busca Avançada de Produto"))

    conteudo.append(p(
        "O campo <b>Produto</b> aceita buscas mais espertas com <b>E</b> e <b>OU</b>, "
        "e ainda pode <b>ignorar os outros filtros</b> quando você quer focar num produto específico."
    ))

    conteudo.append(h3("Sintaxe de busca"))
    sintaxe = [
        ["Você digita", "O que o sistema faz"],
        ["CAIXA QUADRADA", "Acha produtos que tenham CAIXA E QUADRADA"],
        ["CAPA, CAPUZ", "Acha produtos com CAPA OU CAPUZ"],
        ["CAIXA QUADRADA, CAPA", "Acha (CAIXA E QUADRADA) OU CAPA"],
    ]
    conteudo.append(tabela(sintaxe, col_widths=[5 * cm, 9 * cm]))

    conteudo.append(h3("Regra especial — Produto é exclusivo"))
    conteudo.append(p(
        "Quando você digita algo em <b>Produto</b>, o sistema <b>ignora</b> "
        "Fabricante, Departamento, Grupo, Subgrupo e <b>Filial</b>. "
        "Ele busca o produto em <b>toda a rede</b> — todas as 5 filiais, todos os fabricantes."
    ))
    conteudo.append(p(
        "Um <b>aviso azul</b> aparece abaixo dos filtros avisando que essa regra está ativa."
    ))

    conteudo.append(nota(
        "Se você quer filtrar por Fabricante e ver o resultado em todas as filiais, "
        "<b>deixe o campo Produto em branco</b>."
    ))

    conteudo.append(h2("4.4 Parâmetros"))

    conteudo.append(h3("🟦 Linha 1 — Janela de Análise"))
    param1 = [
        ["Parâmetro", "O que é", "Padrão"],
        ["Período de Análise", "Janela histórica", "1 ano atrás"],
        ["Filial", "Filtrar uma filial", "(todas)"],
        ["Cobertura de Vendas", "Dias de estoque", "Para 30 dias"],
        ["Tempo de Transporte", "Dias entre envio e entrega", "10 dias"],
    ]
    conteudo.append(tabela(param1, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(h3("🟦 Linha 2 — Proteção das Origens"))
    param2 = [
        ["Parâmetro", "O que é", "Padrão"],
        ["Piso Exposição (un)", "Mínimo na prateleira", "0"],
        ["Reserva Origem (%)", "% que fica na origem", "25%"],
        ["Atacado tem Piso?", "Atacado respeita piso", "Não"],
        ["Atacado tem Reserva?", "Atacado guarda reserva", "Não"],
    ]
    conteudo.append(tabela(param2, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(h3("🟦 Linha 3 — Travas de Segurança"))
    param3 = [
        ["Parâmetro", "O que é", "Padrão"],
        ["Reposição Recente (dias)", "Quarentena pós-recebimento", "15"],
        ["Dias em Trânsito", "Janela de envio a caminho", "10"],
    ]
    conteudo.append(tabela(param3, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 5 — COMO LER O RESULTADO
    # ============================================================
    conteudo.append(h1("Parte 5 — Como ler o resultado"))

    conteudo.append(h2("5.1 Abas por filial"))
    conteudo.append(p("Após consultar, você verá 5 abas: ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE."))
    conteudo.append(bullet("<b>📤 ENVIAR</b> — o que essa filial precisa mandar"))
    conteudo.append(bullet("<b>📥 RECEBER</b> — o que essa filial precisa receber"))

    conteudo.append(h2("5.2 As colunas essenciais"))
    colunas = [
        ["Coluna", "Significado"],
        ["Prioridade", "🔴 Crítica / 🟠 Alta / 🟡 Normal"],
        ["Cod", "Código interno do produto"],
        ["Produto", "Descrição do produto"],
        ["Destino / Origem", "Filial parceira"],
        ["Qtd Transf.", "Quanto transferir"],
        ["Reserva", "Quanto a origem guarda"],
        ["Dias p/ Zerar", "Dias até acabar"],
        ["Qtd Ideal", "Estoque ideal da filial"],
        ["Motivo", "Por que foi sugerido"],
    ]
    conteudo.append(tabela(colunas, col_widths=[4 * cm, 10 * cm]))

    conteudo.append(h2("5.3 Prioridades"))
    prioridades = [
        ["Prioridade", "Critério", "Ação"],
        ["🔴 Crítica", "Zera em menos de 7 dias", "Transferir hoje"],
        ["🟠 Alta", "Zera entre 7 e 15 dias", "Esta semana"],
        ["🟡 Normal", "Zera em mais de 15 dias", "Fluxo regular"],
    ]
    conteudo.append(tabela(prioridades, col_widths=[3 * cm, 6 * cm, 5 * cm]))

    conteudo.append(h2("5.4 Motivos possíveis"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "Já zerou — urgente"],
        ["AGUARDANDO TRANSFERENCIA", "Já tem envio a caminho"],
        ["RECEBIDO RECENTEMENTE", "Recebeu há pouco, em quarentena"],
        ["URGENTE - zera em N dias", "Vai zerar em breve"],
        ["Origem parada, destino vendendo", "Sai de onde não vende"],
        ["Alta rotacao no destino", "Destino vende 2x mais"],
        ["Maior giro no destino", "Destino vende 1,5x mais"],
        ["Reposicao de ciclo", "Padrão — mantém fluxo"],
    ]
    conteudo.append(tabela(motivos, col_widths=[6 * cm, 8 * cm]))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 6 — ROTINA SEMANAL
    # ============================================================
    conteudo.append(h1("Parte 6 — Rotina semanal"))

    conteudo.append(h2("6.1 Segunda-feira (10 min)"))
    conteudo.append(p("1. Abra o app"))
    conteudo.append(p("2. Clique em ⚙️ Parâmetros"))
    conteudo.append(p("3. Confira os padrões:"))
    conteudo.append(bullet("Período = '1 ano atrás'"))
    conteudo.append(bullet("Cobertura = 'Para 30 dias'"))
    conteudo.append(bullet("Tempo de Transporte = 10"))
    conteudo.append(p("4. Escolha um Fabricante no topo"))
    conteudo.append(p("5. Clique em 🔍"))
    conteudo.append(p("6. Filtre por Prioridade = Crítica"))

    conteudo.append(h2("6.2 Terça a Quinta (ação)"))
    conteudo.append(p("Para cada produto crítico:"))
    conteudo.append(p("1. Veja o <b>Motivo</b>"))
    conteudo.append(p("2. Confirme a <b>Qtd Transf.</b>"))
    conteudo.append(p("3. Verifique a <b>Origem</b>"))
    conteudo.append(p("4. Clique em <b>📄 Gerar PDF</b>"))
    conteudo.append(p("5. Crie a ordem no ERP"))

    conteudo.append(h2("6.3 Sexta-feira (10 min)"))
    conteudo.append(p("1. Reabra o app"))
    conteudo.append(p("2. Compare com a semana anterior"))
    conteudo.append(p("3. Ajuste parâmetros se necessário"))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 7 — AJUSTES FINOS
    # ============================================================
    conteudo.append(h1("Parte 7 — Ajustes finos"))

    conteudo.append(h2("Cenário A — Sugerindo transferência demais"))
    ajuste_a = [
        ["Ajuste", "Efeito"],
        ["Aumentar Reposição Recente (15 → 30)", "Bloqueia por mais tempo"],
        ["Aumentar Reserva Origem (25% → 40%)", "Origem doa menos"],
        ["Diminuir Cobertura de Vendas (30 → 15)", "Ideal menor"],
    ]
    conteudo.append(tabela(ajuste_a, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenário B — Sugerindo transferência de menos"))
    ajuste_b = [
        ["Ajuste", "Efeito"],
        ["Diminuir Reposição Recente (15 → 7)", "Bloqueia menos"],
        ["Diminuir Reserva Origem (25% → 15%)", "Origem doa mais"],
        ["Aumentar Cobertura de Vendas (30 → 45)", "Ideal maior"],
    ]
    conteudo.append(tabela(ajuste_b, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenário C — Produto sempre zerado"))
    ajuste_c = [
        ["Ajuste", "Efeito"],
        ["Aumentar Piso Exposição (0 → 5)", "Mínimo maior"],
        ["Aumentar Cobertura de Vendas", "Ideal maior"],
        ["Verificar Tempo de Transporte", "Corrigir se subestimado"],
    ]
    conteudo.append(tabela(ajuste_c, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenário D — Duplicidade de envio"))
    ajuste_d = [
        ["Ajuste", "Efeito"],
        ["Aumentar Dias em Trânsito (10 → 15)", "Cobre mais tempo"],
        ["Aumentar Reposição Recente (15 → 25)", "Quarentena maior"],
    ]
    conteudo.append(tabela(ajuste_d, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(nota(
        "Nunca mude 2 parâmetros ao mesmo tempo. Assim você não sabe qual causou o efeito."
    ))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 8 — FAQ
    # ============================================================
    conteudo.append(h1("Parte 8 — Perguntas frequentes"))

    faq = [
        ("O sistema demora quanto para carregar?",
         "Com filtro de fabricante: 30-60 segundos. Sem filtro: pode demorar mais."),
        ("Posso deixar em branco todos os filtros?",
         "Não. Escolha pelo menos um."),
        ("Por que meu produto não aparece?",
         "Várias causas: não vendeu no período, está nos departamentos 09/10, "
         "não tem excesso nem falta, ou o filtro excluiu."),
        ("A sugestão parece errada. O que faço?",
         "1. Verifique o Motivo. 2. Confira movimentações estranhas. "
         "3. Verifique o Período. 4. Se persistir, acione TI."),
        ("Posso mudar os parâmetros toda hora?",
         "Não recomendo. Deixe padrão por 15 dias antes de mexer."),
        ("O PDF pode ser editado?",
         "Não, é um PDF padrão fechado para edição."),
        ("Como sei se um produto é doador ou receptor?",
         "Doador: seção ENVIAR. Receptor: seção RECEBER."),
        ("Preciso anotar tudo que o sistema sugere?",
         "Não. Sempre confira o Motivo antes de aprovar."),
        ("Dois produtos competem pela mesma quantidade?",
         "O motor prioriza por urgência."),
        ("Como aciono o suporte?",
         "[Contato do responsável pelo projeto]"),
        ("Consigo ver o histórico de sugestões?",
         "Hoje não. Sugestão futura."),
        ("Posso exportar para Excel?",
         "Só PDF hoje. Export para Excel é sugestão futura."),
        ("Por que o 'Reserva' varia?",
         "É 25% do Excesso. Quanto maior o Excesso, maior a Reserva."),
        ("O que é 'AGUARDANDO TRANSFERENCIA'?",
         "Significa que o produto já tem algo a caminho. Não duplica."),
        ("O que é 'RECEBIDO RECENTEMENTE'?",
         "Filial recebeu nos últimos 15 dias. Está em quarentena."),
    ]
    for pergunta, resposta in faq:
        conteudo.append(p(f"<b>P:</b> {pergunta}", ESTILO_H3))
        conteudo.append(p(f"<b>R:</b> {resposta}"))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 9 — GLOSSÁRIO
    # ============================================================
    conteudo.append(h1("Parte 9 — Glossário"))

    glossario = [
        ["Termo", "Definição"],
        ["Base", "Consulta SQL que traz todos os produtos × filial"],
        ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir"],
        ["Dias em Trânsito", "Período entre envio e recebimento"],
        ["Estoque Ideal", "Quantidade que a filial deveria ter"],
        ["Excesso", "Saldo acima do Ideal"],
        ["Falta", "Saldo abaixo do Ideal"],
        ["Hub", "Filial central (Atacado)"],
        ["Matriz de Proximidade", "Regra de quem ajuda quem"],
        ["Piso Exposição", "Quantidade mínima na prateleira"],
        ["Reposição Recente", "Bloqueio pós-recebimento"],
        ["Reserva Origem", "% que a origem retém"],
        ["Saldo Provável", "Estoque calculado"],
        ["Tempo de Transporte", "Dias entre envio e entrega"],
        ["Velocidade Ativa", "Ritmo de venda por dias ativos"],
        ["Velocidade Período", "Ritmo de venda por dias corridos"],
    ]
    conteudo.append(tabela(glossario, col_widths=[5 * cm, 9 * cm]))

    conteudo.append(PageBreak())

    # ============================================================
    # PARTE 10 — CASOS PRÁTICOS
    # ============================================================
    conteudo.append(h1("Parte 10 — Casos práticos"))

    conteudo.append(h2("Caso 1 — Produto em falta crítica"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))

    caso1 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias", "Motivo"],
        ["1", "Crítica", "562351", "FITA ADESIVA", "Atacado", "85", "3", "URGENTE"],
    ]
    conteudo.append(tabela(caso1, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm]))

    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Ação</b>: gerar PDF, enviar para o Atacado, criar ordem no ERP."))

    conteudo.append(h2("Caso 2 — Produto com excesso"))
    conteudo.append(p("Aba Atacado (ENVIAR):"))

    caso2 = [
        ["#", "Prior.", "Cod", "Produto", "Destino", "Qtd", "Reserva"],
        ["1", "Normal", "627893", "FITA PAPEL", "Alecrim", "50", "20"],
        ["2", "Normal", "627893", "FITA PAPEL", "Via Direta", "30", "20"],
    ]
    conteudo.append(tabela(caso2, colWidths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 3 * cm, 1.5 * cm, 2 * cm]))

    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Ação</b>: confirmar rota, gerar PDF, criar 2 ordens (uma por destino)."))

    conteudo.append(h2("Caso 3 — Transferência entre lojas"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))

    caso3 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias"],
        ["5", "Alta", "612202", "SUSPENSORIO", "Via Direta", "20", "10"],
    ]
    conteudo.append(tabela(caso3, colWidths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 3 * cm, 1.5 * cm, 2 * cm]))

    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Ação</b>: confirmar com a Via Direta, gerar PDF, criar ordem no ERP."))

    conteudo.append(h2("Caso 4 — Nenhuma sugestão"))
    conteudo.append(p("Mensagem: <b>'Nenhuma sugestão encontrada'</b>"))
    conteudo.append(p("Significa que nenhum produto atendeu aos critérios. O que fazer:"))
    conteudo.append(bullet("Confirmar se os produtos estão equilibrados"))
    conteudo.append(bullet("Tentar afrouxar a Cobertura (ex.: 15 dias)"))
    conteudo.append(bullet("Tentar outro período de análise (ex.: 6 meses)"))

    # ============================================================
    # GERAR
    # ============================================================
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("✅ PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()