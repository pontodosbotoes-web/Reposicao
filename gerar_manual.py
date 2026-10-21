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
        ("Parte 2", "Como o sistema pensa (A Matematica)"),
        ("Parte 3", "Primeiro acesso e Mapa Visual"),
        ("Parte 4", "Dicionario de Filtros"),
        ("Parte 5", "Dicionario de Parametros (Os 11 campos)"),
        ("Parte 6", "Lendo os Resultados e os Cards"),
        ("Parte 7", "O Livro dos Motivos (O que cada um significa)"),
        ("Parte 8", "Cenarios Reais (O que fazer?)"),
        ("Parte 9", "Perguntas frequentes e Ajustes"),
        ("Parte 10", "Glossario de Termos"),
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

    # ---------- PARTE 4 - DICIONARIO DE FILTROS ----------
    conteudo.append(h1("Parte 4 - Dicionario de Filtros"))
    conteudo.append(h2("4.1 Os filtros do topo"))
    filtros = [
        ["Filtro", "O que faz", "Exemplo"],
        ["Perfil de Analise", "Configura os 9 parametros automaticamente.", "Padrao, Lancamento, Classe A..."],
        ["Fabricante", "Filtra todos os produtos de uma marca.", "ADERE, 3M, TOYMASTER"],
        ["Departamento", "Categoria principal.", "TECIDOS, AVIAMENTOS"],
        ["Grupo", "Subdivisao da categoria.", "FITAS, PAPEIS"],
        ["Subgrupo", "Nivel mais especifico.", "FITA CETIM, FITA ADESIVA"],
        ["Produto", "Busca por nome, codigo ou referencia.", "CAIXA QUADRADA"],
    ]
    conteudo.append(tabela(filtros, col_widths=[3.5 * cm, 7 * cm, 3.5 * cm]))
    conteudo.append(nota("Escolha pelo menos 1 filtro antes de consultar."))

    conteudo.append(h2("4.2 Busca Avancada de Produto"))
    conteudo.append(p(
        "O campo <b>Produto</b> varre <b>4 fontes</b> e aceita as regras de <b>E</b> (espaco) e <b>OU</b> (virgula). "
        "Se voce preencher este campo, o sistema <b>ignora</b> Fabricante, Departamento, Grupo, Subgrupo e Filial. "
        "Ele busca em toda a rede."
    ))
    conteudo.append(PageBreak())

    # ---------- PARTE 5 - DICIONARIO DE PARAMETROS ----------
    conteudo.append(h1("Parte 5 - Dicionario de Parametros (Os 11 campos)"))
    conteudo.append(p("Ao clicar no botao <b>Parametros</b>, voce vera 11 campos. Veja o que cada um faz:"))
    
    param1 = [
        ["Parametro", "O que e", "Impacto se aumentar"],
        ["Periodo de Analise", "Janela historica para calcular a velocidade.", "Olha mais para tras (mais estavel)."],
        ["Filial", "Apenas visual (filtra abas).", "Nao altera o calculo, so a exibicao."],
        ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir.", "Ideal maior. Loja pede mais."],
        ["Tempo de Transporte", "Dias entre envio e entrega.", "Ideal maior. Mais seguranca."],
        ["Piso Exposicao", "Minimo na prateleira.", "Garante que a prateleira nao fique vazia."],
        ["Reserva Origem (%)", "% do excesso que fica na origem.", "Origem doa menos (mais conservadora)."],
        ["Atacado tem Piso?", "Se atacado respeita piso.", "Atacado segura mais produto."],
        ["Atacado tem Reserva?", "Se atacado guarda reserva.", "Atacado doa menos."],
        ["Reposicao Recente", "Quarentena pos-recebimento.", "Bloqueia por mais tempo (evita gangorra)."],
        ["Dias em Transito", "Janela para ver o que esta a caminho.", "Considera envios mais antigos como em transito."],
        ["Atacado tem Minimo p/ Compra?", "Usa Piso como qtd minima de compra.", "Evita comprar volumes muito pequenos."],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(param1):
        if i > 0:
            for j in range(1, len(row)):
                param1[i][j] = Paragraph(param1[i][j], est_tec)
    conteudo.append(tabela(param1, col_widths=[4 * cm, 6 * cm, 4 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 6 - LENDO OS RESULTADOS ----------
    conteudo.append(h1("Parte 6 - Lendo os Resultados e os Cards"))
    conteudo.append(h2("6.1 Os Cards e as Abas"))
    conteudo.append(p(
        "Acima das tabelas, voce vera <b>5 cards</b>: Enviar, Receber, Liquidar, Desc. e Comprar. "
        "Cada card mostra o total de <b>Itens</b> e de <b>Unidades</b>."
    ))
    conteudo.append(p("As abas representam as filiais: ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE."))

    conteudo.append(h2("6.2 As 5 Secoes de cada Aba"))
    acoes_fim_linha = [
        ["Acao", "O que significa?"],
        ["ENVIAR", "A filial tem demais e vai doar."],
        ["RECEBER", "A filial tem falta e vai receber."],
        ["COMPRAR", "Ninguem na rede tem. Precisa comprar do fornecedor."],
        ["DESCONTINUAR", "Produto de giro baixo (vende 1 a cada 12 dias). Deve sair do mix."],
        ["LIQUIDAR", "Produto zerado de venda. Deve ser promovido ou devolvido."],
    ]
    conteudo.append(tabela(acoes_fim_linha, col_widths=[3 * cm, 11 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 7 - O LIVRO DOS MOTIVOS ----------
    conteudo.append(h1("Parte 7 - O Livro dos Motivos"))
    conteudo.append(p("O Motivo e o coracao do sistema. Ele te diz exatamente o que esta acontecendo."))
    
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "A loja esta zerada e <b>nao ha nada no caminhao</b>. Alarme vermelho. Acao imediata."],
        ["AGUARDANDO TRANSFERENCIA", "A loja tem falta, <b>MAS</b> ja tem um caminhao cheio de produto indo para la. Nao mande de novo."],
        ["RECEBIDO RECENTEMENTE", "A loja recebeu produto ha poucos dias. Esta de 'castigo' (quarentena) para nao pedir duplicado."],
        ["URGENTE - zera hoje", "O estoque acaba em menos de 24 horas."],
        ["URGENTE - zera em N dias", "Vai acabar logo. Voce tem alguns dias para agir."],
        ["Origem parada, destino vendendo", "A loja doadora quase nao vende, mas a receptora vende muito. O sistema move o produto para onde ele gira."],
        ["Alta rotacao no destino", "A loja receptora vende o dobro da doadora."],
        ["Maior giro no destino", "A loja receptora vende 1.5x mais que a doadora."],
        ["Reposicao de ciclo", "Fluxo normal. Nada de errado, apenas mantendo a prateleira cheia."],
        ["ESTOQUE COMPLEMENTAR", "<b>Motivo de compra.</b> A rede tem um pouco do produto, mas nao o suficiente para o Ideal. Compre so o que falta."],
        ["ESTOQUE PARADO", "<b>Liquidar.</b> O produto tem estoque, mas a velocidade de venda e zero. Ninguem quer."],
        ["FIM DE CICLO", "<b>Descontinuar.</b> O produto vende muito pouco (abaixo de 0.1/dia). Venda o estoque e tire do mix."],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(motivos):
        if i > 0:
            for j in range(1, len(row)):
                motivos[i][j] = Paragraph(motivos[i][j], est_tec)
    conteudo.append(tabela(motivos, col_widths=[4 * cm, 10 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 8 - CENARIOS REAIS ----------
    conteudo.append(h1("Parte 8 - Cenarios Reais (O que fazer?)"))
    
    conteudo.append(h2("Caso 1 - Produto em falta critica (RECEBER)"))
    conteudo.append(p("Voce ve a Fita Adesiva com Prioridade Critica e Motivo 'URGENTE - zera hoje'."))
    conteudo.append(p("<b>Acao:</b> 1. Vejo o Motivo. 2. Confirmo a Origem (Atacado). 3. Clico em Gerar PDF. 4. Crio a ordem no ERP."))

    conteudo.append(h2("Caso 2 - A rede inteira esta sem estoque (COMPRAR)"))
    conteudo.append(p("Voce ve a Fita Crepe na aba COMPRAR do Atacado com Sugestao de Compra 50."))
    conteudo.append(p("<b>Acao:</b> Nenhuma loja tem o produto. Envio a lista para o time de Compras fazer o pedido ao fornecedor."))

    conteudo.append(h2("Caso 3 - O produto ja esta a caminho (AGUARDANDO)"))
    conteudo.append(p("Voce ve Papel Kraft com Em Transito 20 un."))
    conteudo.append(p("<b>Acao:</b> O caminhao ja saiu. Nao faco nada, apenas aguardo a entrega."))

    conteudo.append(h2("Caso 4 - O produto esta encalhado (LIQUIDAR)"))
    conteudo.append(p("Voce ve o Squeeze Halloween com Motivo 'ESTOQUE PARADO'."))
    conteudo.append(p("<b>Acao:</b> Acao comercial: promocao local, kit, ou devolver ao fornecedor."))

    conteudo.append(PageBreak())

    conteudo.append(h2("Caso 5 - Produto de giro baixo (DESCONTINUAR)"))
    conteudo.append(p("Voce ve Fita Cetim Vermelha com Motivo 'FIM DE CICLO'."))
    conteudo.append(p("<b>Acao:</b> Vender ate o fim do estoque. Nao comprar mais."))

    conteudo.append(h2("Caso 6 - Produto recem-recebido (RECEBIDO RECENTEMENTE)"))
    conteudo.append(p("Voce ve Papel Kraft com Motivo 'RECEBIDO RECENTEMENTE'."))
    conteudo.append(p("<b>Acao:</b> A origem ja mandou algo nos ultimos 15 dias. Verifique se chegou. Se sim, nao faca nada. Se nao, acione a transportadora."))

    conteudo.append(PageBreak())

    # ---------- PARTE 9 - FAQ ----------------
    conteudo.append(h1("Parte 9 - Perguntas frequentes e Ajustes"))
    faq = [
        ("A sugestao parece errada. O que faco?", "1. Leia o Motivo. 2. Confira o Saldo e o Em Transito. 3. Verifique movimentacoes estranhas. 4. Acione o TI."),
        ("O sistema sugere menos de 5 unidades?", "Nao. O motor tem uma regra de MOQ. Transferencias ou compras abaixo de 5 un sao ignoradas."),
        ("Como ajustar se estiver sugerindo MUITO?", "Aumente a Reposicao Recente (15->30) para bloquear mais. Aumente a Reserva Origem (25->40) para doar menos. Diminua a Cobertura (30->15)."),
        ("Como ajustar se estiver sugerindo POUCO?", "Diminua a Reposicao Recente (15->7). Diminua a Reserva Origem (25->15). Aumente a Cobertura (30->45)."),
        ("O Atacado compra para ele mesmo?", "Sim. Se ele estiver abaixo do Ideal, a aba COMPRAR dele sugere a compra para repor a propria prateleira do CD."),
        ("Como sei se um produto e doador ou receptor?", "Doador: secao ENVIAR. Receptor: secao RECEBER."),
        ("O que e 'RECEBIDO RECENTEMENTE'?", "A loja recebeu nos ultimos N dias (parametro Reposicao Recente). Esta em quarentena."),
        ("Posso transferir tudo que o sistema sugere?", "Nao. O programa nao substitui o bom senso. Sempre confira o Motivo."),
        ("Isso substitui o ERP?", "Nao. E uma ferramenta de decisao. A execucao continua no ERP."),
    ]
    for q, r in faq:
        conteudo.append(p(f"<b>P:</b> {q}", ESTILO_H3))
        conteudo.append(p(f"<b>R:</b> {r}"))
    conteudo.append(PageBreak())

    # ---------- PARTE 10 - GLOSSARIO ----------
    conteudo.append(h1("Parte 10 - Glossario"))
    glossario = [
        ["Termo", "Definicao"],
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

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()