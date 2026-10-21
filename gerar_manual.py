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
    conteudo.append(p("Sistema de sugestao de transferencias entre filiais", ESTILO_CAPA_SUB))
    conteudo.append(p("DRP - IST - MEIO", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Uso interno", ESTILO_CAPA_SUB))
    conteudo.append(PageBreak())

    # ---------- SUMARIO ----------
    conteudo.append(h1("Sumario"))
    conteudo.append(p("Este manual esta dividido em 10 partes:"))
    conteudo.append(Spacer(1, 0.3 * cm))
    for num, titulo in [
        ("Parte 1", "Introducao ao projeto"),
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
    conteudo.append(h1("Parte 1 - Introducao ao projeto"))
    conteudo.append(h2("1.1 Por que este sistema existe"))
    conteudo.append(p(
        "Imagine o dia a dia de uma rede com <b>5 filiais</b> e <b>milhares de produtos</b>. "
        "Todos os dias voce precisa responder:"
    ))
    conteudo.append(bullet("<b>Quanto</b> mandar de cada produto para cada loja?"))
    conteudo.append(bullet("<b>Quando</b> mandar?"))
    conteudo.append(bullet("Se uma loja tem <b>excesso</b> e outra tem <b>falta</b>, como fazer essa troca?"))
    conteudo.append(bullet("Como evitar que o Atacado mande produto demais para uma loja e de menos para outra?"))
    conteudo.append(bullet("Como nao deixar prateleiras vazias sem inflar o estoque?"))
    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(p(
        "Antes deste sistema, essas decisoes eram tomadas manualmente. Levava horas por semana e gerava erros frequentes. "
        "Com este sistema, o motor faz essas perguntas para <b>todos os produtos</b> em segundos "
        "e prioriza os mais urgentes."
    ))

    conteudo.append(h2("1.2 O que o sistema faz"))
    conteudo.append(p("<b>1. Analisa</b> o historico de vendas e movimentacoes de todas as filiais"))
    conteudo.append(p("<b>2. Calcula</b> o estoque ideal que cada filial deveria ter"))
    conteudo.append(p("<b>3. Identifica</b> quem tem <b>excesso</b> e quem tem <b>falta</b>"))
    conteudo.append(p("<b>4. Sugere</b> qual filial envia, para quem, e em qual quantidade"))
    conteudo.append(p("<b>5. Sugere Compras</b> caso o produto falte na rede inteira"))
    conteudo.append(p("<b>6. Prioriza</b> por urgencia e <b>7. Gera</b> relatorios em PDF"))

    conteudo.append(h2("1.3 O que o sistema NAO faz"))
    conteudo.append(bullet("<b>Nao substitui sua decisao</b> - ele sugere, voce aprova"))
    conteudo.append(bullet("<b>Nao executa transferencias</b> - voce cria a ordem no ERP"))
    conteudo.append(bullet("<b>Nao altera dados</b> no banco - e somente leitura"))

    conteudo.append(PageBreak())

    # ---------- PARTE 2 ----------
    conteudo.append(h1("Parte 2 - Como o sistema pensa"))
    conteudo.append(h2("2.1 Estoque Ideal e Saldo Ajustado"))
    conteudo.append(p(
        "O sistema calcula o <b>Estoque Ideal</b> de cada filial usando a formula:"
    ))
    conteudo.append(p("Estoque Ideal = max(Piso Exposicao, Velocidade Periodo x (Cobertura + Tempo de Transporte))", ESTILO_CODIGO))
    conteudo.append(p(
        "Para tomar decisoes, ele sempre usa o <b>Saldo Ajustado</b>, que e a soma do "
        "Saldo Fisico + o que ja esta <b>Em Transito</b>. Isso evita sugerir transferencias duplicadas."
    ))

    conteudo.append(h2("2.2 Como o sistema decide a Compra (COMPRAR)"))
    conteudo.append(p(
        "Quando uma loja precisa de produto, o sistema primeiro tenta transferir do Atacado ou de outras lojas. "
        "Se ninguem na rede tiver o produto sobrando, o sistema cria uma sugestao de <b>COMPRA</b>."
    ))
    conteudo.append(nota(
        "A quantidade de compra sugerida e o Estoque Ideal menos o que a loja ja tem e o que ja vai receber. "
        "Se a loja ja recebeu transferencias e ainda falta, o sistema compra apenas o <b>ESTOQUE COMPLEMENTAR</b>."
    ))

    conteudo.append(h2("2.3 Motivos (Entendendo o Alarme)"))
    conteudo.append(bullet("<b>SEM ESTOQUE:</b> A loja esta zerada e nao ha nada em transito (Alarme Vermelho)."))
    conteudo.append(bullet("<b>AGUARDANDO TRANSFERENCIA:</b> A loja esta com falta, mas ja tem produto no caminhao (Em Transito)."))
    conteudo.append(bullet("<b>ESTOQUE COMPLEMENTAR:</b> Motivo de compra. A rede tem um pouco, mas nao o suficiente."))

    conteudo.append(PageBreak())

    # ---------- PARTE 3 ----------
    conteudo.append(h1("Parte 3 - Filtros e Parametros"))
    conteudo.append(h2("3.1 Perfil de Analise"))
    conteudo.append(p(
        "O <b>Perfil de Analise</b> configura automaticamente os 9 parametros do motor. "
        "Escolha o perfil que melhor se adapta ao momento do produto."
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
    conteudo.append(h2("3.2 Os 9 parametros de cada perfil"))
    
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
            # CORREÇÃO AQUI: Usa o tamanho real da linha para evitar IndexError
            for j in range(1, len(row)):
                perfis_tec[i][j] = Paragraph(perfis_tec[i][j], est_tec)
                
    conteudo.append(tabela(perfis_tec, col_widths=[2.5 * cm, 1.7 * cm, 1.7 * cm, 1.8 * cm, 1.9 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 1.4 * cm]))

    conteudo.append(PageBreak())

    # ---------- PARTE 4 ----------
    conteudo.append(h1("Parte 4 - Como ler o resultado"))
    conteudo.append(h2("4.1 Os Cards e as Abas"))
    conteudo.append(p(
        "Acima das tabelas, voce vera <b>5 cards</b>: Enviar, Receber, Liquidar, Desc. e Comprar. "
        "Cada card mostra o total de <b>Itens</b> e de <b>Unidades</b>."
    ))
    conteudo.append(p(
        "As abas representam as filiais. A aba do Atacado consolida todas as compras da rede. "
        "As abas das lojas mostram a realidade individual de cada uma."
    ))

    conteudo.append(h2("4.2 A coluna Em Transito"))
    conteudo.append(p(
        "A coluna <b>Em Transito</b> mostra a quantidade que ja foi despachada e esta a caminho da filial. "
        "Ela serve para o gestor saber que o problema ja esta sendo resolvido (o caminhao esta na estrada)."
    ))

    conteudo.append(h2("4.3 Motivos"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "Loja zerada e sem produto em transito. Precisa de acao imediata."],
        ["AGUARDANDO TRANSFERENCIA", "Ha falta, mas ja existe envio a caminho (caminhao na estrada)."],
        ["RECEBIDO RECENTEMENTE", "Recebeu nos ultimos N dias (quarentena anti-gangorra)."],
        ["URGENTE - zera hoje", "O produto acaba em menos de 1 dia."],
        ["URGENTE - zera em N dias", "O produto acaba em breve (1 a 6 dias)."],
        ["ESTOQUE COMPLEMENTAR", "Motivo de compra. Ha estoque na rede, mas abaixo do ideal."],
    ]
    conteudo.append(tabela(motivos, col_widths=[6 * cm, 8 * cm]))

    conteudo.append(PageBreak())

    # ---------- PARTE 5 ----------
    conteudo.append(h1("Parte 5 - Casos praticos"))
    conteudo.append(h2("Caso 1 - Produto em falta critica (RECEBER)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso1 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Motivo"],
        ["1", "Critica", "562351", "FITA ADESIVA", "Atacado", "85", "URGENTE - zera hoje"],
    ]
    conteudo.append(tabela(caso1, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 3.5 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: gerar PDF, enviar para o Atacado, criar ordem no ERP."))

    conteudo.append(h2("Caso 2 - Produto que precisa ser COMPRADO"))
    conteudo.append(p("Aba Alecrim (COMPRAR):"))
    caso2 = [
        ["#", "Cod", "Produto", "Velocidade", "Ideal", "Sugestao", "Motivo"],
        ["1", "563551", "FITA ADESIVA", "0.58", "23", "2", "ESTOQUE COMPLEMENTAR"],
        ["2", "627885", "FITA CREPE", "0.33", "13", "13", "SEM ESTOQUE"],
    ]
    conteudo.append(tabela(caso2, col_widths=[1 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 4 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: enviar a lista para o time de Compras do Atacado."))

    conteudo.append(h2("Caso 3 - Transferencia entre lojas (sem passar pelo Atacado)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso3 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Motivo"],
        ["5", "Alta", "612202", "SUSPENSORIO", "Via Direta", "20", "Reposicao de ciclo"],
    ]
    conteudo.append(tabela(caso3, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 3 * cm, 1.5 * cm, 3.5 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: confirmar com a Via Direta, gerar PDF, criar ordem no ERP."))

    conteudo.append(h2("Caso 4 - Aguardando Transferencia (Caminhao na estrada)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso4 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Em Transito", "Motivo"],
        ["3", "Alta", "889900", "PAPEL KRAFT", "Atacado", "40", "20", "AGUARDANDO TRANSFERENCIA"],
    ]
    conteudo.append(tabela(caso4, col_widths=[1 * cm, 2 * cm, 2 * cm, 4 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 4 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: O produto ja esta a caminho. Verificar se o caminhao chegou. Nao fazer nada se ja estiver em transito."))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()