"""Gera o PDF do Manual do Gestor - Reposicao de Produtos."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER


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
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1E293B"))
            self.drawString(2 * cm, h - 1.2 * cm, "Manual do Gestor - Reposicao de Produtos")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(2 * cm, h - 1.4 * cm, w - 2 * cm, h - 1.4 * cm)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(2 * cm, 1.2 * cm, "Uso interno - Reposicao de Produtos")
        self.drawRightString(w - 2 * cm, 1.2 * cm, f"Pagina {self._pageNumber} de {page_count}")


styles = getSampleStyleSheet()

ESTILO_CAPA_TITULO = ParagraphStyle("CapaTitulo", parent=styles["Title"], fontSize=32,
    leading=38, alignment=TA_CENTER, textColor=colors.HexColor("#1E293B"), spaceAfter=20)

ESTILO_CAPA_SUB = ParagraphStyle("CapaSub", parent=styles["Normal"], fontSize=14,
    leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#475569"), spaceAfter=10)

ESTILO_H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, leading=22,
    textColor=colors.HexColor("#0F172A"), spaceBefore=20, spaceAfter=12)

ESTILO_H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, leading=18,
    textColor=colors.HexColor("#1E293B"), spaceBefore=14, spaceAfter=8)

ESTILO_H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, leading=16,
    textColor=colors.HexColor("#334155"), spaceBefore=10, spaceAfter=6)

ESTILO_PARAGRAFO = ParagraphStyle("Paragrafo", parent=styles["BodyText"], fontSize=10,
    leading=14, alignment=TA_JUSTIFY, spaceAfter=8)

ESTILO_BULLET = ParagraphStyle("Bullet", parent=ESTILO_PARAGRAFO,
    leftIndent=15, bulletIndent=5, spaceAfter=4)

ESTILO_CODIGO = ParagraphStyle("Codigo", parent=styles["Code"], fontSize=9, leading=12,
    textColor=colors.HexColor("#0F172A"), backColor=colors.HexColor("#F1F5F9"),
    borderColor=colors.HexColor("#CBD5E1"), borderWidth=0.5, borderPadding=6, spaceAfter=8)

ESTILO_NOTA = ParagraphStyle("Nota", parent=styles["BodyText"], fontSize=9, leading=13,
    textColor=colors.HexColor("#475569"), backColor=colors.HexColor("#FEF3C7"),
    borderColor=colors.HexColor("#F59E0B"), borderWidth=0.5, borderPadding=6, spaceAfter=8)


def p(texto, estilo=ESTILO_PARAGRAFO):
    return Paragraph(texto, estilo)

def h1(texto):
    return Paragraph(texto, ESTILO_H1)

def h2(texto):
    return Paragraph(texto, ESTILO_H2)

def h3(texto):
    return Paragraph(texto, ESTILO_H3)

def bullet(texto):
    return Paragraph(f"&bull; {texto}", ESTILO_BULLET)

def nota(texto):
    return Paragraph(f"<b>Nota:</b> {texto}", ESTILO_NOTA)

def tabela(data, col_widths=None):
    est_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=9,
        leading=11, fontName='Helvetica-Bold', textColor=colors.white)
    est_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=9, leading=11)

    data_fmt = []
    for i, row in enumerate(data):
        row_fmt = []
        for cell in row:
            if isinstance(cell, Paragraph):
                row_fmt.append(cell)
            else:
                st = est_header if i == 0 else est_cell
                row_fmt.append(Paragraph(str(cell), st))
        data_fmt.append(row_fmt)

    t = Table(data_fmt, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    return t


def gerar(buffer=None):
    destino = buffer if buffer is not None else "Manual_Reposicao_Gestor.pdf"
    doc = SimpleDocTemplate(destino, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)

    conteudo = []

    # ---------- CAPA ----------
    conteudo.append(Spacer(1, 6 * cm))
    conteudo.append(p("Reposicao de Produtos", ESTILO_CAPA_TITULO))
    conteudo.append(Spacer(1, 0.5 * cm))
    conteudo.append(p("Manual do Gestor", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Sistema de sugestao de transferencias e compras", ESTILO_CAPA_SUB))
    conteudo.append(p("DRP - IST - MEIO", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Uso interno", ESTILO_CAPA_SUB))
    conteudo.append(PageBreak())

    # ---------- SUMARIO ----------
    conteudo.append(h1("Sumario"))
    conteudo.append(p("Este manual esta dividido em 10 partes:"))
    conteudo.append(Spacer(1, 0.3 * cm))
    for num, titulo in [
        ("Parte 1", "Introducao e o 'Porque'"),
        ("Parte 2", "Como o sistema pensa"),
        ("Parte 3", "Primeiro acesso"),
        ("Parte 4", "Filtros e Parametros"),
        ("Parte 5", "Como ler o resultado"),
        ("Parte 6", "Rotina semanal"),
        ("Parte 7", "Ajustes finos"),
        ("Parte 8", "Perguntas frequentes"),
        ("Parte 9", "Glossario"),
        ("Parte 10", "Casos praticos"),
    ]:
        conteudo.append(p(f"<b>{num}</b> - {titulo}"))
    conteudo.append(PageBreak())

    # ---------- PARTE 1 ----------
    conteudo.append(h1("Parte 1 - Introducao e o 'Porque'"))
    conteudo.append(h2("1.1 O problema que resolvemos"))
    conteudo.append(p(
        "Imagine o dia a dia de uma rede com <b>5 filiais</b> e <b>milhares de produtos</b>. "
        "Todos os dias voce precisa responder:"
    ))
    conteudo.append(bullet("<b>Quanto</b> mandar de cada produto para cada loja?"))
    conteudo.append(bullet("<b>Quando</b> mandar?"))
    conteudo.append(bullet("Se uma loja tem <b>excesso</b> e outra tem <b>falta</b>, como fazer essa troca?"))
    conteudo.append(bullet("E se <b>ninguem</b> na rede tiver o produto? Quando comprar?"))
    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(p(
        "Antes deste sistema, essas decisoes eram tomadas por telefone, planilhas e intuicao. "
        "Levava horas e gerava erros. <b>Com o sistema</b>, o motor faz essas perguntas para TODOS "
        "os produtos em segundos e prioriza os mais urgentes."
    ))

    conteudo.append(h2("1.2 O que o sistema faz e NAO faz"))
    conteudo.append(p("<b>O sistema FAZ:</b>"))
    conteudo.append(bullet("Analisa historico de vendas e movimentacoes"))
    conteudo.append(bullet("Calcula o estoque ideal de cada filial"))
    conteudo.append(bullet("Identifica excessos e faltas"))
    conteudo.append(bullet("Sugere transferencias e compras"))
    conteudo.append(bullet("Prioriza por urgencia e gera PDFs"))
    
    conteudo.append(p("<b>O sistema NAO FAZ:</b>"))
    conteudo.append(bullet("Nao substitui sua decisao - ele sugere, voce aprova"))
    conteudo.append(bullet("Nao executa transferencias - voce cria a ordem no ERP"))
    conteudo.append(bullet("Nao altera dados no banco - e somente leitura"))

    conteudo.append(h2("1.3 De onde vem a inteligencia"))
    conteudo.append(p("O motor foi construido com base em 3 praticas consolidadas no varejo mundial:"))
    conteudo.append(h3("DRP - Distribution Requirements Planning"))
    conteudo.append(p("Planejamento de reposicao baseado no <b>consumo real</b> de cada ponto de venda (Walmart, Carrefour)."))
    conteudo.append(h3("IST - Inter-Store Transfers"))
    conteudo.append(p("Transferencias entre lojas para corrigir desequilibrio enquanto a janela de venda esta aberta (Zara, H&M)."))
    conteudo.append(h3("MEIO - Multi-Echelon Inventory Optimization"))
    conteudo.append(p("Otimizacao de inventario em toda a rede, com <b>hub central</b> (Atacado) para consolidar estoque (Amazon, P&G)."))
    conteudo.append(PageBreak())

    # ---------- PARTE 2 ----------
    conteudo.append(h1("Parte 2 - Como o sistema pensa"))
    conteudo.append(h2("2.1 A metafora da caixa d'agua"))
    conteudo.append(p("Imagine que cada filial e uma <b>caixa d'agua</b>. O sistema tenta manter cada caixa no nivel ideal:"))
    caixa = [
        ["Nivel", "Estado"],
        ["100% (Ideal)", "Tudo perfeito"],
        ["80%", "Atencao"],
        ["40%", "Critico"],
        ["0% (Ruptura)", "Urgente"],
    ]
    conteudo.append(tabela(caixa, col_widths=[6 * cm, 8 * cm]))

    conteudo.append(h2("2.2 Calculando o Estoque Ideal"))
    conteudo.append(p("<b>Formula:</b>"))
    conteudo.append(p("Estoque Ideal = max(Piso Exposicao, Velocidade Periodo x (Cobertura + Tempo de Transporte))", ESTILO_CODIGO))
    conteudo.append(nota(
        "O <b>Piso Exposicao</b> garante um minimo na prateleira, mesmo que a velocidade seja baixa. "
        "A velocidade usada e a <b>Periodo</b> (vendas / dias corridos)."
    ))

    conteudo.append(h3("Exemplo pratico"))
    exemplo = [
        ["Variavel", "Valor"],
        ["Vendas nos ultimos 365 dias", "1.825 unidades"],
        ["Velocidade Periodo", "1.825 / 365 = 5 un/dia"],
        ["Cobertura + Transporte", "30 + 10 = 40 dias"],
        ["Estoque Ideal", "5 x 40 = 200 unidades"],
    ]
    conteudo.append(tabela(exemplo, col_widths=[7 * cm, 7 * cm]))

    conteudo.append(h2("2.3 Excesso, Falta e o Saldo Ajustado"))
    conteudo.append(p(
        "O sistema sempre usa o <b>Saldo Ajustado</b>, que e a soma do Saldo Fisico + o que ja esta <b>Em Transito</b>. "
        "Isso evita sugerir transferencias duplicadas (efeito chicote)."
    ))
    conteudo.append(p("Excesso = Saldo Ajustado - Estoque Ideal (quando positivo)", ESTILO_CODIGO))
    conteudo.append(p("Falta = Estoque Ideal - Saldo Ajustado (quando positivo)", ESTILO_CODIGO))

    conteudo.append(h2("2.4 A Regra de Compra (COMPRAR)"))
    conteudo.append(p(
        "Quando uma loja precisa de produto, o sistema primeiro tenta transferir do Atacado ou de outras lojas. "
        "Se ninguem na rede tiver o produto sobrando, o sistema cria uma sugestao de <b>COMPRA</b>."
    ))
    conteudo.append(nota(
        "A quantidade de compra sugerida e o Estoque Ideal menos o que a loja ja tem e o que ja vai receber. "
        "Se a loja ja recebeu transferencias e ainda falta, o sistema compra apenas o <b>ESTOQUE COMPLEMENTAR</b>."
    ))

    conteudo.append(h2("2.5 Regra do minimo de 5 unidades (MOQ)"))
    conteudo.append(p(
        "O motor ignora transferencias ou compras menores que 5 unidades. "
        "Abaixo desse volume, o custo logistico supera o ganho de disponibilidade."
    ))
    conteudo.append(PageBreak())

    # ---------- PARTE 3 ----------
    conteudo.append(h1("Parte 3 - Primeiro acesso"))
    conteudo.append(p("1. Abra o navegador e digite: https://pb-reposicao.streamlit.app"))
    conteudo.append(p("2. Se o app estiver 'dormindo', clique no botao 'Yes, get this app back up!'."))
    conteudo.append(p("3. A tela principal possui 6 filtros no topo, 5 botoes de acao e os resultados abaixo."))
    conteudo.append(PageBreak())

    # ---------- PARTE 4 ----------
    conteudo.append(h1("Parte 4 - Filtros e Parametros"))
    conteudo.append(h2("4.1 Perfil de Analise"))
    conteudo.append(p(
        "O Perfil configura automaticamente os 9 parametros do motor. Um mesmo produto pode ser analisado "
        "com perfis diferentes, dependendo do seu momento de vida (lancamento, alta temporada, fim de ciclo)."
    ))
    perfis_desc = [
        ["Perfil", "Quando usar", "Exemplo do Dia a Dia"],
        ["Padrao", "Uso geral", "Materiais continuos."],
        ["Lancamento", "Produto novo/colecao", "Nova colecao de tecidos."],
        ["Classe A", "Maior faturamento", "Fita adesiva basica."],
        ["Alto Giro", "Venda rapida constante", "Bexigas de aniversario."],
        ["Sazonal Longo", "Campanhas longas", "Artigos de Natal."],
        ["Sazonal Curto", "Pico explosivo", "Mascaras de Halloween."],
        ["Baixo Giro", "Produtos encalhados", "Tecido de seda."],
        ["Liquidacao", "Fim de ciclo", "Itens de Halloween em nov."],
    ]
    conteudo.append(tabela(perfis_desc, col_widths=[2.5 * cm, 4.5 * cm, 7 * cm]))
    conteudo.append(Spacer(1, 0.3 * cm))

    perfis_tec = [
        ["Parametro", "Padrao", "Lanc.", "Classe A", "Alto Giro", "Saz.Longo", "Saz.Curto", "Baixo Giro", "Liquid."],
        ["Periodo analise", "1 ano", "30d", "3m", "3m", "2m", "30d", "1 ano", "6m"],
        ["Cobertura", "30d", "30d", "15d", "15d", "30d", "15d", "30d", "7d"],
        ["Lead time", "10", "10", "7", "7", "10", "7", "10", "10"],
        ["Piso Exposicao", "0", "5", "10", "5", "5", "3", "3", "0"],
        ["Reserva Origem", "25%", "0%", "25%", "15%", "15%", "5%", "30%", "0%"],
        ["Atacado Piso?", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao"],
        ["Atacado Reserva?", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao"],
        ["Reposicao Recente", "15", "7", "7", "7", "7", "5", "20", "30"],
        ["Dias em Transito", "10", "10", "7", "7", "10", "7", "10", "10"],
        ["Min. Compra", "Nao", "Nao", "Sim", "Nao", "Sim", "Nao", "Nao", "Nao"],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=7, leading=9)
    for i, row in enumerate(perfis_tec):
        if i > 0:
            for j in range(1, len(row)):
                perfis_tec[i][j] = Paragraph(perfis_tec[i][j], est_tec)
    conteudo.append(tabela(perfis_tec, col_widths=[2.5 * cm, 1.7 * cm, 1.7 * cm, 1.8 * cm, 1.9 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 1.4 * cm]))

    conteudo.append(h2("4.2 Parametros em detalhe"))
    param1 = [
        ["Parametro", "O que e", "Padrao"],
        ["Periodo de Analise", "Janela historica", "1 ano atras"],
        ["Filial", "Filtrar uma filial (apenas visual)", "(todas)"],
        ["Cobertura de Vendas", "Dias de estoque", "Para 30 dias"],
        ["Tempo de Transporte", "Dias entre envio e entrega", "10 dias"],
        ["Piso Exposicao (un)", "Minimo na prateleira", "0"],
        ["Reserva Origem (%)", "% do excesso que fica na origem", "25%"],
        ["Reposicao Recente (dias)", "Bloqueio pos-recebimento", "15"],
        ["Dias em Transito", "Janela de envio a caminho", "10"],
        ["Min. Compra", "Usa Piso como qtd minima", "Nao"],
    ]
    conteudo.append(tabela(param1, col_widths=[4 * cm, 6 * cm, 4 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 5 ----------
    conteudo.append(h1("Parte 5 - Como ler o resultado"))
    conteudo.append(h2("5.1 Os Cards e as Abas"))
    conteudo.append(p(
        "Acima das tabelas, voce vera <b>5 cards</b>: Enviar, Receber, Liquidar, Desc. e Comprar. "
        "Cada card mostra o total de <b>Itens</b> e de <b>Unidades</b>."
    ))
    conteudo.append(p("As abas representam as filiais: ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE."))

    conteudo.append(h2("5.2 Motivos possiveis"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "Loja zerada e sem produto em transito. Precisa de acao imediata."],
        ["AGUARDANDO TRANSFERENCIA", "Ha falta, mas ja existe envio a caminho (caminhao na estrada)."],
        ["RECEBIDO RECENTEMENTE", "Recebeu nos ultimos N dias (quarentena anti-gangorra)."],
        ["URGENTE - zera hoje", "O produto acaba em menos de 1 dia."],
        ["URGENTE - zera em N dias", "O produto acaba em breve (1 a 6 dias)."],
        ["Origem parada, destino vendendo", "Origem com velocidade < 0.05 e destino >= 0.1"],
        ["Alta rotacao no destino", "Destino vende 2x mais que origem"],
        ["Maior giro no destino", "Destino vende 1.5x mais que origem"],
        ["Reposicao de ciclo", "Padrao - mantem fluxo"],
        ["ESTOQUE COMPLEMENTAR", "Motivo de compra. Ha estoque na rede, mas abaixo do ideal."],
    ]
    conteudo.append(tabela(motivos, col_widths=[6 * cm, 8 * cm]))

    conteudo.append(h2("5.3 Acoes de Fim de Linha (LIQUIDAR e DESCONTINUAR)"))
    conteudo.append(p(
        "Quando um produto nao vende em nenhuma filial, transferi-lo gera custo de frete e nao resolve a venda. "
        "O sistema cria duas secoes exclusivas de acao comercial."
    ))
    acoes_fim_linha = [
        ["Acao", "Quando acontece?", "O que o gestor deve fazer?"],
        ["LIQUIDAR", "Velocidade ZERO em toda a rede, mas ha estoque.", "Promocao, queima ou devolver ao fornecedor."],
        ["DESCONTINUAR", "Velocidade > 0 mas < 0.1 (fim de ciclo).", "Vender ate o fim do estoque. Nao repor."],
    ]
    conteudo.append(tabela(acoes_fim_linha, col_widths=[3 * cm, 6 * cm, 5 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 6 ----------
    conteudo.append(h1("Parte 6 - Rotina semanal"))
    conteudo.append(h2("6.1 Segunda-feira (10 min)"))
    conteudo.append(p("1. Abra o app. 2. Escolha o Perfil. 3. Escolha um Fabricante. 4. Clique em Consultar."))
    conteudo.append(h2("6.2 Terca a Quinta (acao)"))
    conteudo.append(p(
        "Para cada produto critico: leia o Motivo, confirme a Qtd, gere o PDF e crie a ordem no ERP. "
        "Se houver itens em COMPRAR, envie a lista para o time de Compras."
    ))
    conteudo.append(h2("6.3 Sexta-feira (10 min)"))
    conteudo.append(p("Reabra o app, compare com a semana anterior e ajuste parametros se necessario."))
    conteudo.append(PageBreak())

    # ---------- PARTE 7 ----------
    conteudo.append(h1("Parte 7 - Ajustes finos"))
    conteudo.append(p("Cenario A: Sugerindo transferencia demais. Aumente a Reposicao Recente ou a Reserva Origem."))
    conteudo.append(p("Cenario B: Sugerindo transferencia de menos. Diminua a Reposicao Recente ou a Reserva Origem."))
    conteudo.append(p("Cenario C: Produto sempre zerado. Aumente o Piso Exposicao ou a Cobertura."))
    conteudo.append(p("Cenario D: Duplicidade de envio. Aumente os Dias em Transito ou a Reposicao Recente."))
    conteudo.append(PageBreak())

    # ---------- PARTE 8 ----------
    conteudo.append(h1("Parte 8 - Perguntas frequentes (20)"))
    faq = [
        ("O sistema demora quanto para carregar?", "Com filtro de fabricante: 30-60 segundos. Sem filtro: pode demorar mais."),
        ("Posso deixar em branco todos os filtros?", "Nao. Escolha pelo menos um."),
        ("Por que meu produto nao aparece?", "Varias causas: nao vendeu no periodo, esta nos departamentos INATIVO/USO INTERNO, nao tem excesso nem falta, o filtro excluiu, ou o produto foi removido automaticamente."),
        ("Por que meu produto sumiu da analise automaticamente?", "Se o produto nao vendeu (velocidade < 0.1) em NENHUMA filial E nao tem saldo em NENHUMA, ele e removido. Volta a aparecer quando houver venda ou estoque."),
        ("A sugestao parece errada. O que faco?", "1. Verifique o Motivo. 2. Confira movimentacoes estranhas. 3. Verifique o Periodo. 4. Se persistir, acione TI."),
        ("Posso mudar os parametros toda hora?", "Nao recomendo. Deixe padrao por 15 dias antes de mexer."),
        ("O PDF pode ser editado?", "Nao, e um PDF padrao."),
        ("Como sei se um produto e doador ou receptor?", "Doador: secao ENVIAR. Receptor: secao RECEBER."),
        ("Preciso anotar tudo?", "Nao. Sempre confira o Motivo antes de aprovar."),
        ("Dois produtos competem pela mesma quantidade?", "O motor prioriza por urgencia (Critica -> Alta -> Normal)."),
        ("Como aciono o suporte?", "[Contato do responsavel pelo projeto]"),
        ("Consigo ver o historico de sugestoes?", "Hoje nao. Sugestao futura."),
        ("Posso exportar para Excel?", "So PDF hoje."),
        ("Por que o 'Reserva' varia?", "E o percentual (padrao 25%) sobre o Excesso, arredondado para cima. Quanto maior o Excesso, maior a Reserva."),
        ("O que e 'AGUARDANDO TRANSFERENCIA'?", "O saldo projetado esta <= 0 E ja existe envio a caminho. Nao duplica."),
        ("O que e 'RECEBIDO RECENTEMENTE'?", "Filial recebeu nos ultimos N dias (parametro Reposicao Recente). Esta em quarentena."),
        ("Posso transferir tudo que o sistema sugere?", "Nao. O programa nao substitui o bom senso. Sempre confira antes."),
        ("Quando o Ideal e 0?", "Produtos sem venda no periodo E sem Piso Exposicao configurado."),
        ("O sistema sugere menos de 5 unidades?", "Nao. O motor ignora transferencias < 5 un (MOQ interno para evitar custo logistico)."),
        ("Isso substitui o ERP?", "Nao. E uma ferramenta de decisao. A execucao continua no ERP."),
    ]
    for q, r in faq:
        conteudo.append(p(f"<b>P:</b> {q}", ESTILO_H3))
        conteudo.append(p(f"<b>R:</b> {r}"))
    conteudo.append(PageBreak())

    # ---------- PARTE 9 ----------
    conteudo.append(h1("Parte 9 - Glossario"))
    glossario = [
        ["Termo", "Definicao"],
        ["Base", "Consulta SQL que traz todos os produtos x filial"],
        ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir"],
        ["Dias em Transito", "Periodo entre envio e recebimento"],
        ["Estoque Ideal", "max(Piso, VelocPeriodo x (Cob + Lead))"],
        ["Excesso", "Saldo Ajustado acima do Ideal"],
        ["Falta", "Saldo Ajustado abaixo do Ideal"],
        ["Hub", "Filial central (Atacado)"],
        ["Matriz de Proximidade", "Regra de quem ajuda quem"],
        ["MOQ", "Minimum Order Quantity - minimo de 5 un"],
        ["Piso Exposicao", "Quantidade minima na prateleira"],
        ["Reposicao Recente", "Bloqueio parcial pos-recebimento"],
        ["Reserva Origem", "% do excesso que fica na origem"],
        ["Saldo Ajustado", "SaldoProvavel + QtdEmTransito"],
        ["Velocidade Ativa", "Vendas / dias com venda"],
        ["Velocidade Periodo", "Vendas / dias corridos"],
    ]
    conteudo.append(tabela(glossario, col_widths=[5 * cm, 9 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 10 ----------
    conteudo.append(h1("Parte 10 - Casos praticos"))
    
    conteudo.append(h2("Caso 1 - Produto em falta critica (RECEBER)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso1 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Motivo"],
        ["1", "Critica", "562351", "FITA ADESIVA", "Atacado", "85", "URGENTE - zera hoje"],
    ]
    conteudo.append(tabela(caso1, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 3.5 * cm]))
    conteudo.append(p("<b>Acao</b>: gerar PDF, enviar para o Atacado, criar ordem no ERP."))

    conteudo.append(h2("Caso 2 - Produto que precisa ser COMPRADO"))
    conteudo.append(p("Aba Alecrim (COMPRAR):"))
    caso2 = [
        ["#", "Cod", "Produto", "Velocidade", "Ideal", "Sugestao", "Motivo"],
        ["1", "563551", "FITA ADESIVA", "0.58", "23", "2", "ESTOQUE COMPLEMENTAR"],
        ["2", "627885", "FITA CREPE", "0.33", "13", "13", "SEM ESTOQUE"],
    ]
    conteudo.append(tabela(caso2, col_widths=[1 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 4 * cm]))
    conteudo.append(p("<b>Acao</b>: enviar a lista para o time de Compras do Atacado."))

    conteudo.append(h2("Caso 3 - Transferencia entre lojas (sem passar pelo Atacado)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso3 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Motivo"],
        ["5", "Alta", "612202", "SUSPENSORIO", "Via Direta", "20", "Reposicao de ciclo"],
    ]
    conteudo.append(tabela(caso3, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 3 * cm, 1.5 * cm, 3.5 * cm]))
    conteudo.append(p("<b>Acao</b>: confirmar com a Via Direta, gerar PDF, criar ordem no ERP."))

    conteudo.append(h2("Caso 4 - Aguardando Transferencia (Caminhao na estrada)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso4 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Em Transito", "Motivo"],
        ["3", "Alta", "889900", "PAPEL KRAFT", "Atacado", "40", "20", "AGUARDANDO TRANSFERENCIA"],
    ]
    conteudo.append(tabela(caso4, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 4 * cm]))
    conteudo.append(p("<b>Acao</b>: O produto ja esta a caminho. Verificar se o caminhao chegou."))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()