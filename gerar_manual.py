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
            self.drawString(2 * cm, h - 1.2 * cm, "Manual de Engenharia - Reposicao de Produtos")
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
    conteudo.append(p("Manual de Engenharia e Operação", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("A Ciencia e a Mecanica por tras do Sistema", ESTILO_CAPA_SUB))
    conteudo.append(p("DRP - IST - MEIO", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Uso interno", ESTILO_CAPA_SUB))
    conteudo.append(PageBreak())

    # ---------- SUMARIO ----------
    conteudo.append(h1("Sumario"))
    conteudo.append(p("Este manual foi escrito para transformar voce de operador em engenheiro do sistema. Ele esta dividido em 4 Modulos:"))
    conteudo.append(Spacer(1, 0.3 * cm))
    for num, titulo in [
        ("Modulo 1", "A Engenharia (O Porque Cientifico)"),
        ("Modulo 2", "A Mecanica (O Motor por Dentro)"),
        ("Modulo 3", "O Design do Painel (A Interface)"),
        ("Modulo 4", "Auditoria e Acao (O Gerenciamento)"),
    ]:
        conteudo.append(p(f"<b>{num}</b> - {titulo}"))
    conteudo.append(PageBreak())

    # ---------- MODULO 1 ----------
    conteudo.append(h1("Modulo 1 - A Engenharia (O Porque Cientifico)"))
    conteudo.append(p(
        "Para confiar no sistema, voce precisa saber que ele nao foi inventado. Ele aplica "
        "3 praticas consagradas no varejo mundial. Quem entende a origem, toma melhores decisoes."
    ))

    conteudo.append(h2("1.1 DRP (Distribution Requirements Planning)"))
    conteudo.append(p(
        "<b>O que e:</b> Planejamento de reposicao baseado no consumo real de cada ponto de venda.<br/>"
        "<b>Onde entra:</b> E a base do calculo do Estoque Ideal (Velocidade x Cobertura).<br/>"
        "<b>Quem usa:</b> Walmart, Carrefour, Pao de Acucar.<br/>"
        "<b>Literatura:</b> O DRP reduz faltas e melhora a pontualidade das entregas, alem de evitar "
        "sobreinventario e desabastecimento."
    ))

    conteudo.append(h2("1.2 IST (Inter-Store Transfers)"))
    conteudo.append(p(
        "<b>O que e:</b> Transferencias entre lojas para corrigir desequilibrio enquanto a janela de venda esta aberta.<br/>"
        "<b>Onde entra:</b> E a Matriz de Proximidade. Quando a Zona Sul precisa, o sistema tenta o Atacado, depois o Alecrim, etc.<br/>"
        "<b>Quem usa:</b> Zara, H&M, Best Buy.<br/>"
        "<b>Caso real (Zara):</b> A Zara usa dados de PDV em tempo real e cross-docking para um ciclo de design "
        "ate a loja de apenas 2 a 3 semanas. Transferir entre lojas e mais rapido e barato do que esperar o CD."
    ))

    conteudo.append(h2("1.3 MEIO (Multi-Echelon Inventory Optimization)"))
    conteudo.append(p(
        "<b>O que e:</b> Otimizacao de inventario em toda a rede, com um hub central (Atacado) para consolidar estoque.<br/>"
        "<b>Onde entra:</b> O Atacado e o primeiro doador e o consolidador de compras.<br/>"
        "<b>Quem usa:</b> Amazon, Coca-Cola, P&G.<br/>"
        "<b>Caso real (Amazon):</b> A otimizacao multi-echelon da Amazon reduziu o capital de giro imobilizado em "
        "14% a 27% e melhorou o nivel de servico em ate 3,2%, alem de reduzir faltas em 30% a 50%."
    ))

    conteudo.append(h2("1.4 O Efeito Chicote (e como o sistema o combate)"))
    conteudo.append(p(
        "A P&G descobriu que, mesmo com as vendas de fraldas Pampers estaveis no varejo, os pedidos dos supermercados "
        "flutuavam drasticamente. Isso inflava os custos de producao e estoque na cadeia inteira."
    ))
    conteudo.append(p(
        "O sistema resolve isso com o parametro <b>Reposicao Recente</b>. Se a loja recebeu produto ha poucos dias, "
        "o sistema bloqueia um novo pedido, mesmo que a falta ainda exista. Isso evita o pedido duplicado "
        "e quebra o ciclo."
    ))
    conteudo.append(PageBreak())

    # ---------- MODULO 2 ----------
    conteudo.append(h1("Modulo 2 - A Mecanica (O Motor por Dentro)"))
    
    conteudo.append(h2("2.1 A Matematica do Estoque Ideal"))
    conteudo.append(p(
        "Nao usamos medias simples. Usamos a <b>Velocidade Periodo</b>, que dilui dias de venda e dias parados.<br/><br/>"
        "<b>Formula:</b> Estoque Ideal = max(Piso, Velocidade Periodo x (Cobertura + Tempo de Transporte))"
    ))
    conteudo.append(nota(
        "Por que somar o Tempo de Transporte? Se a loja vende 5 fitas por dia e o caminhao demora 10 dias, "
        "quando as 50 fitas chegarem, a loja ja vendeu 50. Entao, o ideal e mandar 50 (para o caminhao) + 150 (para 30 dias) = 200."
    ))

    conteudo.append(h2("2.2 A Regra do Minimo de 5 unidades (MOQ)"))
    conteudo.append(p(
        "Baseado na Teoria dos Custos de Transacao (Coase, 1937). O custo de mover 3 unidades (frete, separacao, combustivel) "
        "e maior que o beneficio de ter essas 3 unidades na prateleira. O sistema simplesmente ignora transferencias abaixo de 5. "
        "A Amazon faz exatamente isso entre seus Fulfillment Centers."
    ))

    conteudo.append(h2("2.3 O Resgate de Saldos Negativos"))
    conteudo.append(p(
        "Voce vera sugestoes maiores que o Ideal (ex: Ideal 20, Transf 80). Isso acontece quando o sistema detecta "
        "que a loja tem um saldo fisico negativo (fruto de erro de inventario ou venda nao baixada). A formula de compra/transferencia "
        "e (Ideal - Saldo). Se o saldo e -60, ele manda 80. O sistema esta te ajudando a <b>resgatar</b> o estoque."
    ))
    conteudo.append(PageBreak())

    # ---------- MODULO 3 ----------
    conteudo.append(h1("Modulo 3 - O Design do Painel (A Interface)"))
    conteudo.append(p(
        "A tela foi desenhada com base em Ciencia Cognitiva para evitar sobrecarga. Voce deve olhar para ela como um diretor."
    ))

    conteudo.append(h2("3.1 Os 5 Cards Superiores"))
    conteudo.append(p(
        "Antes de ver a tabela gigante, os cards dao o Resumo Executivo. Se voce ve 'Enviar: 26 itens', ja sabe que tera trabalho. "
        "Se ve 'Comprar: 0', sabe que nao precisara ligar para o fornecedor. E o seu painel de aviao."
    ))

    conteudo.append(h2("3.2 A Psicologia das Cores e Prioridades"))
    prioridades = [
        ["Prioridade", "Criterio", "Acao"],
        ["Critica", "Zera em menos de 7 dias", "Transferir hoje"],
        ["Alta", "Zera de 7 a 14 dias", "Esta semana"],
        ["Normal", "Zera em 15 dias ou mais", "Fluxo regular"],
    ]
    conteudo.append(tabela(prioridades, col_widths=[3 * cm, 7 * cm, 4 * cm]))
    conteudo.append(PageBreak())

    # ---------- MODULO 4 ----------
    conteudo.append(h1("Modulo 4 - Auditoria e Acao (O Gerenciamento)"))
    
    conteudo.append(h2("4.1 Checklist de Auditoria de uma Sugestao"))
    conteudo.append(p(
        "Se a quantidade sugerida for estranha, use o metodo de auditoria:"
    ))
    conteudo.append(bullet("1. Verifique o Motivo: Ele explica o porque (ex: AGUARDANDO TRANSFERENCIA)."))
    conteudo.append(bullet("2. Verifique o Em Transito: O sistema ja esta contabilizando um caminhao na estrada?"))
    conteudo.append(bullet("3. Verifique o Saldo: E um resgate de saldo negativo?"))
    conteudo.append(bullet("4. Verifique o Perfil: O perfil escolhido esta correto para o ciclo de vida?"))

    conteudo.append(h2("4.2 O Livro dos Motivos (Auditoria Rapida)"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "A loja esta zerada e nao ha nada no caminhao."],
        ["AGUARDANDO TRANSFERENCIA", "A loja tem falta, MAS ja tem um caminhao cheio indo para la."],
        ["RECEBIDO RECENTEMENTE", "A loja recebeu produto ha poucos dias (quarentena anti-gangorra)."],
        ["ESTOQUE COMPLEMENTAR", "Motivo de compra. A rede tem um pouco, mas nao o suficiente."],
        ["ESTOQUE PARADO", "Liquidar. O produto tem estoque, mas a velocidade de venda e zero."],
        ["FIM DE CICLO", "Descontinuar. O produto vende muito pouco."],
    ]
    est_tec = ParagraphStyle('Tec3', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(motivos):
        if i > 0:
            for j in range(1, len(row)):
                motivos[i][j] = Paragraph(motivos[i][j], est_tec)
    conteudo.append(tabela(motivos, col_widths=[4 * cm, 10 * cm]))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()