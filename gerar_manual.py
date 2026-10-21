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
    conteudo.append(p("A Ciencia por tras da operacao", ESTILO_CAPA_SUB))
    conteudo.append(p("DRP - IST - MEIO", ESTILO_CAPA_SUB))
    conteudo.append(Spacer(1, 3 * cm))
    conteudo.append(p("Uso interno", ESTILO_CAPA_SUB))
    conteudo.append(PageBreak())

    # ---------- SUMARIO ----------
    conteudo.append(h1("Sumario"))
    conteudo.append(p("Este manual esta dividido em 5 Modulos de Imersao:"))
    conteudo.append(Spacer(1, 0.3 * cm))
    for num, titulo in [
        ("Modulo 1", "O Problema (A Dor)"),
        ("Modulo 2", "A Ciencia (A Solucao)"),
        ("Modulo 3", "As Ferramentas (O Que e e Para Que Serve)"),
        ("Modulo 4", "A Inteligencia (Lendo a Tela)"),
        ("Modulo 5", "O Protocolo (O Dia a Dia)"),
    ]:
        conteudo.append(p(f"<b>{num}</b> - {titulo}"))
    conteudo.append(PageBreak())

    # ---------- MODULO 1 ----------
    conteudo.append(h1("Modulo 1 - O Problema (A Dor)"))
    conteudo.append(h2("1.1 O Custo da Ruptura (Prateleira Vazia)"))
    conteudo.append(p(
        "Quando o cliente quer comprar e nao encontra o produto, a venda e perdida. "
        "No varejo brasileiro, falhas de abastecimento sao responsaveis por ate <b>42% das perdas de vendas</b>. "
        "No setor de moda, a perda chega a <b>30%</b>."
    ))
    conteudo.append(nota(
        "O sistema resolve isso calculando o Estoque Ideal para que a prateleira nunca fique vazia."
    ))

    conteudo.append(h2("1.2 O Custo do Excesso (Dinheiro Parado)"))
    conteudo.append(p(
        "Ter mais produto do que a loja consegue vender imobiliza capital, gera custo de armazenagem "
        "e leva a perdas por validade ou obsolescencia."
    ))
    conteudo.append(nota(
        "O sistema identifica quem tem excesso (doador) e move o produto para onde ele esta vendendo."
    ))

    conteudo.append(h2("1.3 A Rotina Manual vs. O Sistema"))
    conteudo.append(p(
        "Antes: <b>4 a 6 horas por semana</b> montando planilhas, ligando para filiais e decidindo por intuicao. "
        "Erros frequentes: esquecer produtos, calcular quantidade errada ou mandar de uma loja que tambem estava precisando."
    ))
    conteudo.append(p(
        "Com o sistema: O motor faz o calculo para milhares de produtos em segundos. "
        "O gestor foca apenas em aprovar as acoes criticas."
    ))
    conteudo.append(PageBreak())

    # ---------- MODULO 2 ----------
    conteudo.append(h1("Modulo 2 - A Ciencia (A Solucao)"))
    conteudo.append(p(
        "O sistema aplica 3 praticas consolidadas no varejo mundial. Entender isso e o que diferencia "
        "um gestor estrategico de um operador de tela."
    ))

    conteudo.append(h2("2.1 DRP (Distribution Requirements Planning)"))
    conteudo.append(p(
        "<b>O que e:</b> Planejamento de reposicao baseado no consumo real de cada ponto de venda.<br>"
        "<b>Onde entra:</b> E a base do calculo do Estoque Ideal (Velocidade x Cobertura).<br>"
        "<b>Quem usa:</b> Walmart, Carrefour, Pao de Acucar.<br>"
        "<b>Literatura:</b> O DRP reduz faltas e melhora a pontualidade das entregas, alem de evitar "
        "sobreinventario e desabastecimento."
    ))

    conteudo.append(h2("2.2 IST (Inter-Store Transfers)"))
    conteudo.append(p(
        "<b>O que e:</b> Transferencias entre lojas para corrigir desequilibrio enquanto a janela de venda esta aberta.<br>"
        "<b>Onde entra:</b> E a Matriz de Proximidade. Quando a Zona Sul precisa, o sistema tenta o Atacado, depois o Alecrim, etc.<br>"
        "<b>Quem usa:</b> Zara, H&M, Best Buy.<br>"
        "<b>Caso real (Zara):</b> A Zara usa dados de PDV em tempo real e cross-docking para um ciclo de design "
        "ate a loja de apenas 2 a 3 semanas. Transferir entre lojas e mais rapido e barato do que esperar o CD."
    ))

    conteudo.append(h2("2.3 MEIO (Multi-Echelon Inventory Optimization)"))
    conteudo.append(p(
        "<b>O que e:</b> Otimizacao de inventario em toda a rede, com um hub central (Atacado) para consolidar estoque.<br>"
        "<b>Onde entra:</b> O Atacado e o primeiro doador e o consolidador de compras.<br>"
        "<b>Quem usa:</b> Amazon, Coca-Cola, P&G.<br>"
        "<b>Caso real (Amazon):</b> A otimizacao multi-echelon da Amazon reduziu o capital de giro imobilizado em "
        "14% a 27% e melhorou o nivel de servico em ate 3,2%, alem de reduzir faltas em 30% a 50%."
    ))

    conteudo.append(h2("2.4 O Efeito Chicote (e como o sistema o combate)"))
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

    # ---------- MODULO 3 ----------
    conteudo.append(h1("Modulo 3 - As Ferramentas (O Que e e Para Que Serve)"))
    conteudo.append(p(
        "Aqui explicamos o 'Porque' de cada ferramenta e o risco de usa-la de forma errada."
    ))

    conteudo.append(h2("3.1 O Perfil de Analise (O Atalho Inteligente)"))
    conteudo.append(p(
        "O Perfil configura os 9 parametros automaticamente. Escolher o perfil errado pode custar caro. Veja:"
    ))
    
    perfis_tec = [
        ["Perfil", "Quando usar (O MOTIVO)", "O que acontece se errar?"],
        ["Padrao", "Produtos normais, que vendem o ano todo.", "Se usar em um sazonal, vai acumular estoque fora de epoca."],
        ["Lancamento", "Produto novo, sem historico de venda.", "Se usar Padrao, o sistema acha que vende zero e nao manda nada (prateleira vazia)."],
        ["Classe A", "Campeoes de venda. O carro-chefe.", "Se usar Baixo Giro, o sistema vai deixar faltar o produto mais importante."],
        ["Alto Giro", "Venda rapida e constante.", "Se usar Padrao, a loja zera antes do caminhao chegar."],
        ["Sazonal Longo", "Natal, Carnaval. Vende muito por semanas.", "Se usar Sazonal Curto, o estoque acaba no meio da campanha."],
        ["Sazonal Curto", "Pascoa, Halloween. Pico de 1 semana.", "Se usar Sazonal Longo, sobra estoque apos a data (prejuizo)."],
        ["Baixo Giro", "Produtos encalhados. Vende 1 por mes.", "Se usar Classe A, compra uma montanha de produto que ninguem quer."],
        ["Liquidacao", "Fim de ciclo. Nao vende mais.", "Se usar Padrao, o sistema fica transferindo produto morto (gasta frete)."],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(perfis_tec):
        if i > 0:
            for j in range(1, len(row)):
                perfis_tec[i][j] = Paragraph(perfis_tec[i][j], est_tec)
    conteudo.append(tabela(perfis_tec, col_widths=[3 * cm, 5 * cm, 6 * cm]))

    conteudo.append(h2("3.2 Os 11 Parametros (O que cada um resolve?)"))
    param1 = [
        ["Parametro", "O que e", "Impacto se aumentar"],
        ["Periodo de Analise", "Janela historica de vendas.", "Olha mais para tras (mais estavel)."],
        ["Filial", "Apenas visual (filtra abas).", "Nao altera o calculo, so a exibicao."],
        ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir.", "Ideal maior. Loja pede mais."],
        ["Tempo de Transporte", "Dias entre envio e entrega.", "Ideal maior. Mais seguranca."],
        ["Piso Exposicao", "Minimo na prateleira.", "Garante que a prateleira nao fique vazia."],
        ["Reserva Origem (%)", "% do excesso que fica na origem.", "Origem doa menos (conservadora)."],
        ["Atacado tem Piso?", "Se atacado respeita piso.", "Atacado segura mais produto."],
        ["Atacado tem Reserva?", "Se atacado guarda reserva.", "Atacado doa menos."],
        ["Reposicao Recente", "Quarentena pos-recebimento.", "Bloqueia por mais tempo (evita gangorra)."],
        ["Dias em Transito", "Janela do que esta a caminho.", "Considera envios mais antigos como em transito."],
        ["Minimo p/ Compra?", "Usa Piso como qtd minima de compra.", "Evita comprar volumes muito pequenos."],
    ]
    est_tec = ParagraphStyle('Tec2', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(param1):
        if i > 0:
            for j in range(1, len(row)):
                param1[i][j] = Paragraph(param1[i][j], est_tec)
    conteudo.append(tabela(param1, col_widths=[3.5 * cm, 6.5 * cm, 4 * cm]))
    conteudo.append(PageBreak())

    # ---------- MODULO 4 ----------
    conteudo.append(h1("Modulo 4 - A Inteligencia (Lendo a Tela)"))
    conteudo.append(h2("4.1 Ideal vs. Quantidade de Transferencia"))
    conteudo.append(p(
        "Essa e a maior duvida dos gestores:\n"
        "<b>Qtd Ideal:</b> E o tamanho do buraco (a meta).\n"
        "<b>Qtd Transf.:</b> E a acao de hoje. O que falta para tapar o buraco.\n"
        "Exemplo: Ideal 100, Saldo 40. Transfere 60. O Ideal e a meta, a transferencia e o passo."
    ))

    conteudo.append(h2("4.2 O Livro dos Motivos"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "A loja esta zerada e nao ha nada no caminhao. Alarme vermelho. Acao imediata."],
        ["AGUARDANDO TRANSFERENCIA", "A loja tem falta, MAS ja tem um caminhao cheio de produto indo para la. Nao mande de novo."],
        ["RECEBIDO RECENTEMENTE", "A loja recebeu produto ha poucos dias. Esta de 'castigo' (quarentena) para nao pedir duplicado."],
        ["URGENTE - zera hoje", "O estoque acaba em menos de 24 horas."],
        ["URGENTE - zera em N dias", "Vai acabar logo. Voce tem alguns dias para agir."],
        ["Origem parada, destino vendendo", "A loja doadora quase nao vende, mas a receptora vende muito. O sistema move o produto para onde ele gira."],
        ["Alta rotacao no destino", "A loja receptora vende o dobro da doadora."],
        ["Maior giro no destino", "A loja receptora vende 1.5x mais que a doadora."],
        ["Reposicao de ciclo", "Fluxo normal. Nada de errado."],
        ["ESTOQUE COMPLEMENTAR", "Motivo de compra. A rede tem um pouco do produto, mas nao o suficiente. Compre so o que falta."],
        ["ESTOQUE PARADO", "Liquidar. O produto tem estoque, mas a velocidade de venda e zero."],
        ["FIM DE CICLO", "Descontinuar. O produto vende muito pouco. Venda o estoque e tire do mix."],
    ]
    est_tec = ParagraphStyle('Tec3', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(motivos):
        if i > 0:
            for j in range(1, len(row)):
                motivos[i][j] = Paragraph(motivos[i][j], est_tec)
    conteudo.append(tabela(motivos, col_widths=[4 * cm, 10 * cm]))
    conteudo.append(PageBreak())

    # ---------- MODULO 5 ----------
    conteudo.append(h1("Modulo 5 - O Protocolo (O Dia a Dia)"))
    conteudo.append(h2("5.1 Sua Rotina Semanal"))
    conteudo.append(p(
        "<b>Segunda-feira (10 min):</b><br>"
        "1. Abra o app.<br>"
        "2. Escolha o Perfil de Analise.<br>"
        "3. Escolha o Fabricante.<br>"
        "4. Clique em Consultar.<br>"
        "5. Filtre por Prioridade Critica.<br><br>"
        "<b>Terca a Quinta (Acao):</b><br>"
        "1. Leia o Motivo.<br>"
        "2. Confirme a Qtd.<br>"
        "3. Gere o PDF.<br>"
        "4. Crie a ordem no ERP.<br>"
        "5. Se houver itens em COMPRAR, envie a lista para o time de Compras.<br><br>"
        "<b>Sexta-feira (10 min):</b><br>"
        "1. Reabra o app.<br>"
        "2. Compare com a semana anterior.<br>"
        "3. Ajuste parametros se necessario."
    ))

    conteudo.append(h2("5.2 Cenarios Reais (O que fazer?)"))
    conteudo.append(p("<b>Cenario 1: Produto em falta critica (RECEBER)</b>"))
    conteudo.append(p(
        "O que vejo: Fita Adesiva, 85 un, Motivo: 'URGENTE - zera hoje'.\n"
        "Acao: Gere o PDF, envie para o Atacado, crie a ordem no ERP."
    ))
    
    conteudo.append(p("<b>Cenario 2: A rede inteira esta sem estoque (COMPRAR)</b>"))
    conteudo.append(p(
        "O que vejo: Fita Crepe na aba COMPRAR do Atacado, Sugestao 50.\n"
        "Acao: Nenhuma loja tem. Envie a lista para o time de Compras."
    ))
    
    conteudo.append(p("<b>Cenario 3: O produto ja esta a caminho (AGUARDANDO)</b>"))
    conteudo.append(p(
        "O que vejo: Papel Kraft, Em Transito: 20 un.\n"
        "Acao: O caminhao ja saiu. Apenas aguarde a entrega."
    ))
    
    conteudo.append(p("<b>Cenario 4: O produto esta encalhado (LIQUIDAR)</b>"))
    conteudo.append(p(
        "O que vejo: Squeeze Halloween, Motivo: 'ESTOQUE PARADO'.\n"
        "Acao: O sistema NAO vai transferir. Acao comercial: promocao local ou devolucao."
    ))
    
    conteudo.append(p("<b>Cenario 5: O produto tem giro baixo (DESCONTINUAR)</b>"))
    conteudo.append(p(
        "O que vejo: Fita Cetim Vermelha, Motivo: 'FIM DE CICLO'.\n"
        "Acao: Vender ate o fim do estoque. Nao comprar mais."
    ))

    conteudo.append(h2("5.3 Ajustes Frequentes"))
    conteudo.append(p("<b>A sugestao parece errada. O que faco?</b>"))
    conteudo.append(bullet("1. Leia o Motivo. 2. Confira o Saldo e o Em Transito. 3. Verifique movimentacoes estranhas. 4. Se nada explicar, acione o TI."))
    
    conteudo.append(p("<b>Como ajustar se estiver sugerindo MUITO?</b>"))
    conteudo.append(bullet("Aumente a Reposicao Recente (15 -> 30). Aumente a Reserva Origem (25% -> 40%). Diminua a Cobertura (30 -> 15)."))
    
    conteudo.append(p("<b>Como ajustar se estiver sugerindo POUCO?</b>"))
    conteudo.append(bullet("Diminua a Reposicao Recente (15 -> 7). Diminua a Reserva Origem (25% -> 15%). Aumente a Cobertura (30 -> 45)."))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()