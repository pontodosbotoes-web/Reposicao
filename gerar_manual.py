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
        ("Parte 1", "O Problema e a Ciencia"),
        ("Parte 2", "Como o sistema pensa (A Matematica)"),
        ("Parte 3", "Primeiro acesso"),
        ("Parte 4", "Dicionario de Filtros"),
        ("Parte 5", "O Cérebro da Operacao (Perfis e Parametros)"),
        ("Parte 6", "Lendo os Resultados e os Cards"),
        ("Parte 7", "O Livro dos Motivos"),
        ("Parte 8", "Sua Rotina Semanal"),
        ("Parte 9", "Perguntas frequentes"),
        ("Parte 10", "Cenarios Reais"),
    ]:
        conteudo.append(p(f"<b>{num}</b> - {titulo}"))
    conteudo.append(PageBreak())

    # ---------- PARTE 1 ----------
    conteudo.append(h1("Parte 1 - O Problema e a Ciencia"))
    conteudo.append(h2("1.1 A Dor do Varejo"))
    conteudo.append(p(
        "Falhas de abastecimento causam ate <b>42% de perda de vendas</b>. Por outro lado, ter produto demais "
        "imobiliza capital e gera perda por validade. O sistema resolve esses dois lados da moeda."
    ))

    conteudo.append(h2("1.2 A Ciencia por tras do Motor"))
    conteudo.append(p(
        "<b>DRP (Distribution Requirements Planning):</b> Base do Estoque Ideal. Usado por Walmart, Carrefour.<br/>"
        "<b>IST (Inter-Store Transfers):</b> Matriz de Proximidade. Usado pela Zara (ciclo de 2 semanas).<br/>"
        "<b>MEIO (Multi-Echelon Inventory Optimization):</b> Otimizacao com Hub Central. A Amazon reduziu capital de giro em ate 27%."
    ))

    conteudo.append(h2("1.3 O Efeito Chicote (P&G)"))
    conteudo.append(p(
        "A P&G descobriu que pedidos de fraldas flutuavam drasticamente por medo de falta. O sistema resolve isso "
        "com o parametro <b>Reposicao Recente</b>, bloqueando pedidos duplicados."
    ))
    conteudo.append(PageBreak())

    # ---------- PARTE 2 ----------
    conteudo.append(h1("Parte 2 - Como o sistema pensa"))
    conteudo.append(h2("2.1 Calculando o Estoque Ideal"))
    conteudo.append(p("Estoque Ideal = max(Piso Exposicao, Velocidade Periodo x (Cobertura + Tempo de Transporte))", ESTILO_CODIGO))
    conteudo.append(nota(
        "Por que somar o Tempo de Transporte? Se a loja vende 5 fitas por dia e o caminhao demora 10 dias, "
        "quando as 50 fitas chegarem, a loja ja vendeu 50. O ideal e mandar 50 (caminhao) + 150 (cobertura) = 200."
    ))

    conteudo.append(h2("2.2 Ideal vs. Quantidade de Transferencia"))
    conteudo.append(p(
        "Essa e uma das maiores duvidas dos gestores:<br/>"
        "<b>Qtd Ideal:</b> E a quantidade para satisfazer o periodo.<br/>"
        "<b>Qtd Transf.:</b> E a acao de hoje. O que falta para cobrir o saldo mais o necessario para o periodo.<br/>"
        "Exemplo: Ideal 100, Saldo 40. Transfere 60. O Ideal e o necessario para o periodo, a transferencia cobre o saldo atual e a necessidade projetada."
    ))

    conteudo.append(h2("2.3 Saldos Negativos (Erro de Movimentação)"))
    conteudo.append(p(
        "Se o saldo estimado de uma loja aparecer negativo (ex.: -60), isso indica <b>erro de movimentação</b>: "
        "provavelmente houve uma entrada antes do período da consulta que o sistema não capturou. "
        "Como não temos controle de inventário físico, o motor trata o saldo negativo como <b>zero</b> (loja vazia) "
        "e sugere apenas o necessário para atingir o Ideal, sem tentar 'resgatar' a dívida fantasma."
    ))

    conteudo.append(h2("2.4 Produtos Pesáveis e a Trava de Compra"))
    conteudo.append(p(
        "O sistema lê a flag <b>ProdutoPesavel</b> do ERP para tratar itens vendidos a granel (KG, MTS, LT) de forma diferente. "
        "Para esses produtos, a quantidade de teste no DEMONSTRAR e o Piso Exposição são ajustados para <b>0,1</b> (ex: 100g). "
        "Além disso, a <b>Trava de Compra</b> impede que o sistema sugira comprar produtos que a filial vende muito pouco localmente, "
        "evitando estoques parados em lojas que não têm demanda."
    ))
    conteudo.append(PageBreak())

    # ---------- PARTE 3 ----------
    conteudo.append(h1("Parte 3 - Primeiro acesso"))
    conteudo.append(p("1. Abra o navegador e digite: https://pb-reposicao.streamlit.app"))
    conteudo.append(p("2. Se o app estiver dormindo, clique em 'Yes, get this app back up!'."))
    conteudo.append(p("3. A tela possui 6 filtros, botoes de acao (Consultar, Limpar, Parametros, Manual, Gerar PDF), 6 cards de resumo e as tabelas."))
    conteudo.append(PageBreak())

    # ---------- PARTE 4 - DICIONARIO DE FILTROS ----------
    conteudo.append(h1("Parte 4 - Dicionario de Filtros"))
    filtros = [
        ["Filtro", "O que faz", "Exemplo"],
        ["Perfil de Analise", "Configura os 9 parametros automaticamente.", "Padrao, Lancamento..."],
        ["Fabricante", "Filtra todos os produtos de uma marca.", "ADERE, 3M"],
        ["Departamento", "Categoria principal.", "TECIDOS"],
        ["Grupo", "Subdivisao da categoria.", "FITAS"],
        ["Subgrupo", "Nivel mais especifico.", "FITA CETIM"],
        ["Produto", "Busca por nome, codigo ou referencia.", "CAIXA QUADRADA"],
    ]
    conteudo.append(tabela(filtros, col_widths=[3.5 * cm, 7 * cm, 3.5 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 5 - O CÉREBRO DA OPERAÇÃO ----------
    conteudo.append(h1("Parte 5 - O Cérebro da Operacao (Perfis e Parametros)"))
    
    conteudo.append(h2("5.1 O Perfil de Analise (O Atalho Inteligente)"))
    perfis_tec = [
        ["Perfil", "Quando usar (O MOTIVO)", "O que acontece se errar?"],
        ["Padrao", "Produtos normais.", "Se usar em sazonal, acumula estoque fora de epoca."],
        ["Lancamento", "Sem historico de venda.", "Se usar Padrao, nao manda nada (prateleira vazia)."],
        ["Classe A", "Campeoes de venda.", "Se usar Baixo Giro, deixa faltar o principal."],
        ["Alto Giro", "Venda rapida.", "Se usar Padrao, zera antes do caminhao chegar."],
        ["Sazonal Longo", "Natal, Carnaval.", "Se usar Curto, acaba no meio da campanha."],
        ["Sazonal Curto", "Pascoa, Halloween.", "Se usar Longo, sobra estoque apos a data."],
        ["Baixo Giro", "Encalhados.", "Se usar Classe A, compra uma montanha."],
        ["Liquidacao", "Fim de ciclo.", "Se usar Padrao, transfere produto morto (gasta frete)."],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(perfis_tec):
        if i > 0:
            for j in range(1, len(row)):
                perfis_tec[i][j] = Paragraph(perfis_tec[i][j], est_tec)
    conteudo.append(tabela(perfis_tec, col_widths=[3 * cm, 5 * cm, 6 * cm]))

    conteudo.append(h2("5.2 Os 11 Parametros (O que cada um resolve?)"))
    param1 = [
        ["Parametro", "O que e", "Impacto se aumentar"],
        ["Periodo de Analise", "Janela historica de vendas.", "Olha mais para tras."],
        ["Filial", "Apenas visual (filtra abas).", "Nao altera o calculo."],
        ["Cobertura de Vendas", "Dias de venda que o produto deve cobrir.", "Ideal maior. Loja pede mais."],
        ["Tempo de Transporte", "Dias entre envio e entrega.", "Ideal maior."],
        ["Piso Exposicao", "Minimo na prateleira.", "Garante prateleira cheia."],
        ["Reserva Origem (%)", "% do excesso que fica na origem.", "Origem doa menos."],
        ["Atacado tem Piso?", "Se atacado respeita piso.", "Atacado segura mais."],
        ["Atacado tem Reserva?", "Se atacado guarda reserva.", "Atacado doa menos."],
        ["Reposicao Recente", "Quarentena pos-recebimento.", "Bloqueia por mais tempo."],
        ["Dias em Transito", "Janela do que esta a caminho.", "Considera envios mais antigos."],
        ["Minimo p/ Compra?", "Usa Piso como qtd minima.", "Evita volumes irrisorios."],
    ]
    est_tec = ParagraphStyle('Tec2', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(param1):
        if i > 0:
            for j in range(1, len(row)):
                param1[i][j] = Paragraph(param1[i][j], est_tec)
    conteudo.append(tabela(param1, col_widths=[3.5 * cm, 6.5 * cm, 4 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 6 - LENDO OS RESULTADOS ----------
    conteudo.append(h1("Parte 6 - Lendo os Resultados e os Cards"))
    conteudo.append(h2("6.1 A Hierarquia de Decisão (Cascata)"))
    conteudo.append(p(
        "O sistema não toma decisões em paralelo. Ele usa uma <b>Cascata (Waterfall)</b>. Um produto passa por etapas de eliminação. "
        "Se ele se encaixa na Etapa 1, ele não vai para a Etapa 2. Isso evita que o mesmo produto apareça em várias abas."
    ))
    
    acoes_fim_linha = [
        ["Etapa", "Ação", "O que significa?"],
        ["1", "DEMONSTRAR", "A loja nunca teve o item. O motor busca doadora com excesso (mín. 5 un ou 0,1 kg) e envia para teste. O produto é bloqueado das etapas seguintes."],
        ["2", "DESCONTINUAR", "A rede toda vende muito pouco (velocidade entre 0 e 0.1). O item deve sair do mix das lojas restantes."],
        ["3", "LIQUIDAR", "A rede toda zerou as vendas. O estoque físico restante deve ser promovido."],
        ["4", "ENVIAR/RECEBER", "O produto vende bem. O motor cruza o excesso de uma loja com a falta de outra. (Inclui a Trava de Recompra)."],
        ["5", "COMPRAR", "Ninguém na rede tem o suficiente. A sugestão é comprar do fornecedor (com Trava de Velocidade Local)."]
    ]
    conteudo.append(tabela(acoes_fim_linha, col_widths=[1.5 * cm, 3 * cm, 9.5 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 7 - O LIVRO DOS MOTIVOS ----------
    conteudo.append(h1("Parte 7 - O Livro dos Motivos"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM REGISTRO NA FILIAL", "A loja nunca recebeu o item e o sistema está enviando uma quantidade inicial (5 un ou 0,1 kg) para iniciar o histórico."],
        ["SEM ESTOQUE", "A loja está zerada e não há nada no caminhão nem na rede."],
        ["AGUARDANDO TRANSFERENCIA", "A loja tem falta, MAS já tem um caminhão indo para lá. Não faça novo pedido."],
        ["RECEBIDO RECENTEMENTE", "A loja recebeu há poucos dias (quarentena). Aguarde as vendas."],
        ["URGENTE - zera hoje", "O estoque acaba em menos de 24 horas."],
        ["Origem parada, destino vendendo", "A doadora não vende, mas a receptora vende muito."],
        ["Alta rotacao no destino", "A receptora vende o dobro."],
        ["Reposicao de ciclo", "Fluxo normal de transferência."],
        ["ESTOQUE COMPLEMENTAR", "Motivo de compra. A rede tem um pouco, mas não o suficiente para a filial."],
        ["ESTOQUE PARADO", "Liquidar. A velocidade de venda caiu para zero na rede."],
        ["FIM DE CICLO NA REDE", "Descontinuar. O produto vende muito pouco (abaixo do limite) em todas as filiais."]
    ]
    est_tec = ParagraphStyle('Tec3', parent=styles['Normal'], fontSize=8, leading=10)
    for i, row in enumerate(motivos):
        if i > 0:
            for j in range(1, len(row)):
                motivos[i][j] = Paragraph(motivos[i][j], est_tec)
    conteudo.append(tabela(motivos, col_widths=[4 * cm, 10 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 8 - ROTINA SEMANAL ----------
    conteudo.append(h1("Parte 8 - Sua Rotina Semanal"))
    conteudo.append(h2("Segunda (10 min)"))
    conteudo.append(p("1. Escolha o Perfil e o Fabricante. 2. Consulte. 3. Filtre por Critica."))
    conteudo.append(h2("Terca a Quinta (Acao)"))
    conteudo.append(p("1. Leia o Motivo. 2. Gere o PDF. 3. Crie a ordem no ERP. 4. Envie lista de COMPRAR e DEMONSTRAR para os times."))
    conteudo.append(h2("Sexta (10 min)"))
    conteudo.append(p("Reabra e compare com a semana anterior."))
    conteudo.append(PageBreak())

    # ---------- PARTE 9 - FAQ ----------------
    conteudo.append(h1("Parte 9 - Perguntas frequentes"))
    faq = [
        ("A sugestao parece errada. O que faco?", "1. Leia o Motivo. 2. Confira Saldo e Em Transito. 3. Verifique se o produto nao caiu em DESC ou LIQ por causa da velocidade da rede."),
        ("Por que um produto nao aparece em mais de uma aba?", "O sistema usa Cascata. Se ele foi para DEMONSTRAR, nao vai para ENVIAR. Se foi para DESC, nao vai para LIQ. Isso evita duplicidade de pedidos."),
        ("Por que a coluna de Prioridade sumiu em algumas abas?", "Acoes de DEMONSTRAR, DESC e LIQ sao absolutas. A prioridade so e calculada no fluxo normal de transferencias (ENVIAR/RECEBER)."),
        ("O que significa um saldo negativo (ex: -60)?", "E um erro de movimentacao (entrada nao lancada). O sistema trata como ZERO para nao pedir quantidades absurdas."),
        ("Como o sistema trata produtos vendidos a granel (KG, MTS)?", "O sistema le a flag 'ProdutoPesavel' do ERP. Para esses itens, o teste inicial e de 0,1 (100g) e o limite para descontinuar e mais flexivel."),
        ("O que e a Trava de Recompra?", "Se o Atacado tem estoque novo e as lojas tem falta (mesmo com velocidade historica baixa), o sistema forca a distribuicao (ENVIAR/RECEBER) em vez de liquidar."),
        ("Como ajustar se estiver sugerindo MUITO?", "Aumente Reposicao Recente ou Reserva. Diminua Cobertura."),
        ("Como ajustar se estiver sugerindo POUCO?", "Diminua Reposicao Recente ou Reserva. Aumente Cobertura."),
        ("O Atacado compra para ele mesmo?", "Sim, se ele estiver abaixo do Ideal."),
        ("Isso substitui o ERP?", "Nao. E uma ferramenta de decisao.")
    ]
    for q, r in faq:
        conteudo.append(p(f"<b>P:</b> {q}", ESTILO_H3))
        conteudo.append(p(f"<b>R:</b> {r}"))
    conteudo.append(PageBreak())

    # ---------- PARTE 10 - CASOS PRATICOS ----------
    conteudo.append(h1("Parte 10 - Cenarios Reais"))
    
    conteudo.append(h2("Caso 4: Loja nunca recebeu o produto (DEMONSTRAR)"))
    conteudo.append(p("O que vejo: Papel Colorido, Origem: ATACADO, Destino: ZONA NORTE, Qtd: 5, Motivo: 'SEM REGISTRO NA FILIAL'."))
    conteudo.append(p("Acao: A loja nunca teve historico. O sistema esta enviando 5 un do Atacado para testar a venda e iniciar o historico."))

    conteudo.append(h2("Caso 2: A rede esta sem estoque (COMPRAR)"))
    conteudo.append(p("O que vejo: Fita Crepe, Sugestao 50, Retorno Financeiro R$ 25.00."))
    conteudo.append(p("Acao: Envie a lista para o time de Compras."))

    conteudo.append(h2("Caso 3: O produto ja esta a caminho (AGUARDANDO)"))
    conteudo.append(p("O que vejo: Papel Kraft, Em Transito 20."))
    conteudo.append(p("Acao: Aguarde a entrega."))
    
    conteudo.append(h2("Caso 4: Loja nunca recebeu o produto (DEMONSTRAR)"))
    conteudo.append(p("O que vejo: Papel Colorido, Origem: ATACADO, Destino: ZONA NORTE, Qtd: 5, Motivo: 'SEM REGISTRO NA FILIAL'."))
    conteudo.append(p("Acao: A loja nunca teve historico. O sistema esta enviando 5 un do Atacado para testar a venda e iniciar o historico."))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()