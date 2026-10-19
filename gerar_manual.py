"""Gera o PDF do Manual do Gestor - Reposicao de Produtos.

Uso:
    python gerar_manual.py

Saida:
    Manual_Reposicao_Gestor.pdf (na pasta atual)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER


# ============================================================
# CANVAS COM CABECALHO E RODAPE
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


# ============================================================
# ESTILOS
# ============================================================
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


# ============================================================
# CONSTRUCAO DO PDF
# ============================================================
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
        ("Parte 8", "Perguntas frequentes (20)"),
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
        "Antes deste sistema, essas decisoes eram tomadas manualmente: telefonemas, planilhas, "
        "calculos por intuicao. Levava horas por semana e gerava erros frequentes. "
        "Com este sistema, o motor faz essas perguntas para <b>todos os produtos</b> em segundos "
        "e prioriza os mais urgentes."
    ))

    conteudo.append(h2("1.2 O que o sistema faz"))
    conteudo.append(p("<b>1. Analisa</b> o historico de vendas e movimentacoes de todas as filiais"))
    conteudo.append(p("<b>2. Calcula</b> o estoque ideal que cada filial deveria ter"))
    conteudo.append(p("<b>3. Identifica</b> quem tem <b>excesso</b> e quem tem <b>falta</b>"))
    conteudo.append(p("<b>4. Sugere</b> qual filial envia, para quem, e em qual quantidade"))
    conteudo.append(p("<b>5. Prioriza</b> por urgencia (o que zera primeiro vem no topo)"))
    conteudo.append(p("<b>6. Gera</b> relatorios em PDF por filial"))

    conteudo.append(h2("1.3 O que o sistema NAO faz"))
    conteudo.append(bullet("[X] <b>Nao substitui sua decisao</b> - ele sugere, voce aprova"))
    conteudo.append(bullet("[X] <b>Nao executa transferencias</b> - voce cria a ordem no ERP"))
    conteudo.append(bullet("[X] <b>Nao altera dados</b> no banco - e somente leitura"))
    conteudo.append(bullet("[X] <b>Nao substitui o bom senso</b> - sempre confira o motivo"))

    conteudo.append(h2("1.4 Em 1 paragrafo"))
    conteudo.append(nota(
        "O sistema olha os ultimos <b>365 dias</b> de cada produto, calcula o <b>ritmo de venda</b> "
        "de cada filial, define <b>quanto cada uma precisa ter em estoque</b> para cobrir <b>30 dias</b> "
        "de venda + <b>10 dias</b> de transporte, e cruza tudo: quem tem demais vira <b>doador</b>, "
        "quem tem de menos vira <b>receptor</b>. O <b>Atacado</b> entra como hub principal, e as "
        "<b>lojas proximas</b> se ajudam quando faz sentido."
    ))

    conteudo.append(h2("1.5 De onde vem a inteligencia"))
    conteudo.append(p("O motor foi construido com base em 3 praticas consolidadas no varejo mundial:"))
    conteudo.append(h3("DRP - Distribution Requirements Planning"))
    conteudo.append(p("Planejamento de reposicao baseado no <b>consumo real</b> de cada ponto de venda."))
    conteudo.append(p("<i>Empresas que usam: Walmart, Carrefour, Pao de Acucar.</i>"))
    conteudo.append(h3("IST - Inter-Store Transfers"))
    conteudo.append(p("Transferencias entre lojas para corrigir desequilibrio enquanto a janela de venda esta aberta."))
    conteudo.append(p("<i>Empresas que usam: Zara, H&M, Best Buy.</i>"))
    conteudo.append(h3("MEIO - Multi-Echelon Inventory Optimization"))
    conteudo.append(p("Otimizacao de inventario em toda a rede, com <b>hub central</b> para consolidar estoque."))
    conteudo.append(p("<i>Empresas que usam: Amazon, Coca-Cola, P&G.</i>"))
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
    conteudo.append(Spacer(1, 0.3 * cm))

    conteudo.append(h2("2.2 Como se calcula o Estoque Ideal"))
    conteudo.append(p("<b>Formula:</b>"))
    conteudo.append(p(
        "Estoque Ideal = max(Piso Exposicao, Velocidade Periodo x (Cobertura + Tempo de Transporte))",
        ESTILO_CODIGO
    ))
    conteudo.append(nota(
        "Dois pontos importantes: (a) o <b>Piso Exposicao</b> garante um minimo na prateleira, "
        "mesmo que a velocidade seja baixa; (b) a velocidade usada e a <b>Periodo</b> "
        "(vendas / dias corridos), nao a Ativa."
    ))

    conteudo.append(h3("Exemplo pratico"))
    conteudo.append(p("Produto: Fita Adesiva 3M"))
    exemplo = [
        ["Variavel", "Valor"],
        ["Vendas nos ultimos 365 dias", "1.825 unidades"],
        ["Velocidade Periodo", "1.825 / 365 = 5 un/dia"],
        ["Cobertura de Vendas", "30 dias"],
        ["Tempo de Transporte", "10 dias"],
        ["Soma", "40 dias"],
        ["Estoque Ideal (sem Piso)", "5 x 40 = 200 unidades"],
    ]
    conteudo.append(tabela(exemplo, col_widths=[7 * cm, 7 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(nota(
        "A loja deveria ter 200 unidades para cobrir 30 dias de venda + 10 de transporte. "
        "Se o Piso Exposicao for maior que isso, o Ideal sera o Piso."
    ))

    conteudo.append(h2("2.3 Como se calculam Excesso e Falta"))
    conteudo.append(p("<b>Formula:</b>"))
    conteudo.append(p("Excesso = Saldo Ajustado - Estoque Ideal   (quando positivo)", ESTILO_CODIGO))
    conteudo.append(p("Falta   = Estoque Ideal - Saldo Ajustado   (quando positivo)", ESTILO_CODIGO))
    conteudo.append(p(
        "<b>Saldo Ajustado</b> = Saldo Provavel + Qtd Em Transito. O sistema <b>sempre</b> usa o "
        "Saldo Ajustado - nunca o saldo puro - para nao sugerir transferencia duplicada."
    ))

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
    conteudo.append(bullet("<b>Atacado</b> tem 400 un de excesso - doador principal"))
    conteudo.append(bullet("<b>Zona Sul</b> tem 45 un de falta - receptor urgente"))
    conteudo.append(bullet("<b>Alecrim</b> tem 20 un de falta - receptor"))
    conteudo.append(bullet("<b>Via Direta</b> tem 40 un de excesso - doador secundario"))

    conteudo.append(h2("2.4 Os 3 tipos de transferencia que o motor faz"))
    conteudo.append(h3("Tipo 1 - Atacado -> Loja (a mais comum)"))
    conteudo.append(p("O Atacado e o <b>hub central</b>. Sempre aparece como primeiro doador."))
    conteudo.append(h3("Tipo 2 - Loja -> Loja (proximidade)"))
    conteudo.append(p("Quando o Atacado nao tem excesso suficiente, as lojas proximas se ajudam."))
    conteudo.append(h3("Tipo 3 - Multiplas origens"))
    conteudo.append(p("O motor combina origens para cobrir a falta total de uma filial."))

    conteudo.append(h2("2.5 A matriz de proximidade"))
    matriz = [
        ["Destino", "Ordem de prioridade dos doadores"],
        ["Alecrim", "1o Atacado, 2o Via Direta, 3o Zona Sul, 4o Zona Norte"],
        ["Via Direta", "1o Atacado, 2o Alecrim, 3o Zona Sul"],
        ["Zona Sul", "1o Atacado, 2o Alecrim, 3o Via Direta"],
        ["Zona Norte", "1o Atacado, 2o Alecrim"],
        ["Atacado", "Nunca recebe"],
    ]
    conteudo.append(tabela(matriz, col_widths=[4 * cm, 10 * cm]))

    conteudo.append(h2("2.6 Regra do minimo de 5 unidades"))
    conteudo.append(p(
        "O motor <b>ignora transferencias menores que 5 unidades</b> em todas as regras: "
        "so sugere se a Falta for >= 5 e se o Excesso Transferivel for >= 5. "
        "Esse e um <b>MOQ interno</b> (Minimum Order Quantity): abaixo desse volume, "
        "o custo logistico da transferencia supera o ganho de disponibilidade."
    ))
    conteudo.append(nota(
        "Amazon usa o mesmo principio para transferencias entre centros de distribuicao. "
        "Acima do MOQ, ganha-se disponibilidade. Abaixo, perde-se dinheiro."
    ))

    conteudo.append(PageBreak())

    # ---------- PARTE 3 ----------
    conteudo.append(h1("Parte 3 - Primeiro acesso"))
    conteudo.append(h2("3.1 Como abrir"))
    conteudo.append(p("1. Abra o navegador (Chrome, Edge ou Firefox)"))
    conteudo.append(p("2. Digite na barra de endereco:"))
    conteudo.append(p("https://pb-reposicao.streamlit.app", ESTILO_CODIGO))
    conteudo.append(p("3. Pressione <b>Enter</b>"))
    conteudo.append(h3("Primeira vez do dia"))
    conteudo.append(p(
        "Se o app estiver 'dormindo', voce vera o botao <b>'Yes, get this app back up!'</b>. "
        "Clique e aguarde ~30 segundos."
    ))

    conteudo.append(h2("3.2 Mapa visual da tela"))
    layout = [
        ["Area", "O que tem"],
        ["Topo", "Titulo 'Reposicao de Produtos'"],
        ["Linha 1", "6 filtros: Perfil, Fabricante, Departamento, Grupo, Subgrupo, Produto"],
        ["Botoes", "Consultar, Limpar, Parametros e Manual"],
        ["Aviso", "Faixa azul quando o Produto esta preenchido"],
        ["Parametros", "Aparece ao clicar em Parametros (3 linhas)"],
        ["Resultados", "Aparece apos consultar (5 abas por filial)"],
    ]
    conteudo.append(tabela(layout, col_widths=[3.5 * cm, 10.5 * cm]))

    conteudo.append(h2("3.3 Problemas comuns"))
    problemas = [
        ["Problema", "Solucao"],
        ["App 'dormindo'", "Clicar em 'Yes, get this app back up!'"],
        ["Tela em branco", "Atualizar navegador"],
        ["Erro de conexao", "Testar em outra rede"],
        ["Consulta nao retorna", "Aguardar 5 min e tentar"],
    ]
    conteudo.append(tabela(problemas, col_widths=[5 * cm, 9 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 4 ----------
    conteudo.append(h1("Parte 4 - Filtros e Parametros"))
    conteudo.append(h2("4.1 Perfil de Analise"))
    conteudo.append(p(
        "O <b>Perfil de Analise</b> configura automaticamente os 9 parametros do motor. "
        "Um mesmo produto pode ser analisado com perfis diferentes, dependendo do seu "
        "momento de vida (lancamento, alta temporada, fim de ciclo)."
    ))
    conteudo.append(h3("Como ele interage com os Parametros?"))
    conteudo.append(p(
        "Ao trocar o Perfil, o sistema sobrescreve os 9 parametros no painel. "
        "Se voce mudar manualmente um parametro, o sistema respeitara sua alteracao e o nome "
        "do perfil continua o mesmo. Para voltar ao padrao, clique em <b>Limpar</b>."
    ))

    conteudo.append(h3("Perfis disponiveis"))
    perfis_desc = [
        ["Perfil", "Quando usar", "Exemplo do Dia a Dia"],
        ["Padrao", "Uso geral", "Materiais continuos."],
        ["Lancamento", "Produto novo/colecao", "Nova colecao de tecidos."],
        ["Classe A", "Maior faturamento", "Fita adesiva basica, papel kraft."],
        ["Alto Giro", "Venda rapida constante", "Bexigas de aniversario."],
        ["Sazonal Longo", "Campanhas longas (Natal/Carnaval)", "Artigos de Natal em novembro."],
        ["Sazonal Curto", "Pico explosivo (Pascoa/Maes/Halloween)", "Mascaras de Halloween."],
        ["Baixo Giro", "Produtos encalhados", "Tecido de seda que vende 1 rolo/mes."],
        ["Liquidacao", "Fim de ciclo / queima", "Itens de Halloween na 1a semana de nov."],
    ]
    conteudo.append(tabela(perfis_desc, col_widths=[2.5 * cm, 4.5 * cm, 7 * cm]))

    conteudo.append(h3("Os 9 parametros de cada perfil (tabela tecnica)"))
    perfis_tec = [
        ["Parametro", "Padrao", "Lanc.", "Classe A", "Alto Giro", "Saz.Longo", "Saz.Curto", "Baixo Giro", "Liquid."],
        ["Periodo analise", "1 ano", "30d", "3m", "3m", "2m", "30d", "1 ano", "6m"],
        ["Cobertura", "30d", "30d", "15d", "15d", "30d", "15d", "30d", "7d"],
        ["Lead time", "10", "10", "7", "7", "10", "7", "10", "10"],
        ["Piso Exposicao", "0", "5", "10", "5", "5", "3", "3", "0"],
        ["Reserva Origem", "25%", "0%", "40%", "15%", "15%", "5%", "30%", "0%"],
        ["Atacado tem Piso?", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao"],
        ["Atacado tem Reserva?", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao", "Nao"],
        ["Reposicao Recente", "15", "7", "7", "7", "7", "5", "20", "30"],
        ["Dias em Transito", "10", "10", "7", "7", "10", "7", "10", "10"],
    ]
    est_tec = ParagraphStyle('Tec', parent=styles['Normal'], fontSize=7, leading=9)
    for i, row in enumerate(perfis_tec):
        if i > 0:
            for j in range(1, 9):
                perfis_tec[i][j] = Paragraph(perfis_tec[i][j], est_tec)
    conteudo.append(tabela(perfis_tec, col_widths=[2.5 * cm, 1.7 * cm, 1.7 * cm, 1.8 * cm, 1.9 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 1.4 * cm]))

    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(h2("4.2 Filtros do topo"))
    filtros = [
        ["Filtro", "O que faz"],
        ["Fabricante", "Nome do fabricante"],
        ["Departamento", "Categoria macro"],
        ["Grupo", "Subdivisao da categoria"],
        ["Subgrupo", "Nivel mais especifico"],
        ["Produto", "Busca por codigo, referencia, nome ou codigo de barras. Aceita E / OU"],
    ]
    conteudo.append(tabela(filtros, col_widths=[4 * cm, 10 * cm]))
    conteudo.append(nota("Escolha pelo menos 1 filtro antes de consultar."))

    conteudo.append(h2("4.3 Busca Avancada de Produto"))
    conteudo.append(p(
        "O campo <b>Produto</b> varre <b>4 fontes</b>: codigo interno, referencia do fabricante, "
        "nome/descricao e codigo de barras (GTIN). Aceita E (espaco) e OU (virgula)."
    ))
    sintaxe = [
        ["Voce digita", "O que o sistema faz"],
        ["CAIXA QUADRADA", "Acha produtos que tenham CAIXA E QUADRADA"],
        ["CAPA, CAPUZ", "Acha produtos com CAPA OU CAPUZ"],
        ["CAIXA QUADRADA, CAPA", "Acha (CAIXA E QUADRADA) OU CAPA"],
    ]
    conteudo.append(tabela(sintaxe, col_widths=[5 * cm, 9 * cm]))

    conteudo.append(h3("Regra especial - Produto e exclusivo"))
    conteudo.append(p(
        "Quando voce digita algo em <b>Produto</b>, o sistema <b>ignora</b> Fabricante, "
        "Departamento, Grupo, Subgrupo e <b>Filial</b>. Busca em <b>toda a rede</b>. "
        "Um aviso azul aparece abaixo dos filtros avisando que essa regra esta ativa."
    ))

    conteudo.append(h2("4.4 Parametros em detalhe"))
    conteudo.append(h3("Linha 1 - Janela de Analise"))
    param1 = [
        ["Parametro", "O que e", "Padrao"],
        ["Periodo de Analise", "Janela historica", "1 ano atras"],
        ["Filial", "Filtrar uma filial (apenas visual)", "(todas)"],
        ["Cobertura de Vendas", "Dias de estoque", "Para 30 dias"],
        ["Tempo de Transporte", "Dias entre envio e entrega", "10 dias"],
    ]
    conteudo.append(tabela(param1, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(h3("Linha 2 - Protecao das Origens"))
    param2 = [
        ["Parametro", "O que e", "Padrao"],
        ["Piso Exposicao (un)", "Minimo na prateleira", "0"],
        ["Reserva Origem (%)", "% do excesso que fica na origem", "25%"],
        ["Atacado tem Piso?", "Atacado respeita piso", "Nao"],
        ["Atacado tem Reserva?", "Atacado guarda reserva", "Nao"],
    ]
    conteudo.append(tabela(param2, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(h3("Linha 3 - Travas de Seguranca"))
    param3 = [
        ["Parametro", "O que e", "Padrao"],
        ["Reposicao Recente (dias)", "Bloqueio pos-recebimento", "15"],
        ["Dias em Transito", "Janela de envio a caminho", "10"],
    ]
    conteudo.append(tabela(param3, col_widths=[4 * cm, 6 * cm, 4 * cm]))

    conteudo.append(PageBreak())

    # ---------- PARTE 5 ----------
    conteudo.append(h1("Parte 5 - Como ler o resultado"))
    conteudo.append(h2("5.1 Abas por filial"))
    conteudo.append(p("Apos consultar, voce vera 5 abas: ATACADO, ALECRIM, VIA DIRETA, ZONA SUL, ZONA NORTE."))
    conteudo.append(bullet("<b>ENVIAR</b> - o que essa filial precisa mandar"))
    conteudo.append(bullet("<b>RECEBER</b> - o que essa filial precisa receber"))
    conteudo.append(bullet("<b>DESCONTINUAR</b> - produtos com giro baixissimo que precisam sair do mix"))
    conteudo.append(bullet("<b>LIQUIDAR</b> - produtos com giro zero que precisam de acao comercial"))

    conteudo.append(h2("5.2 As colunas essenciais"))
    colunas = [
        ["Coluna", "Significado"],
        ["Prioridade", "Critica / Alta / Normal"],
        ["Cod", "Codigo interno do produto"],
        ["Produto", "Descricao do produto"],
        ["Destino / Origem", "Filial parceira"],
        ["Qtd Transf.", "Quanto transferir"],
        ["Reserva", "Quanto a origem guarda"],
        ["Dias p/ Zerar", "Dias ate acabar"],
        ["Qtd Ideal", "Estoque ideal da filial"],
        ["Motivo", "Por que foi sugerido"],
    ]
    conteudo.append(tabela(colunas, col_widths=[4 * cm, 10 * cm]))

    conteudo.append(h2("5.3 Prioridades"))
    prioridades = [
        ["Prioridade", "Criterio", "Acao"],
        ["Critica", "Zera em menos de 7 dias", "Transferir hoje"],
        ["Alta", "Zera de 7 a 14 dias", "Esta semana"],
        ["Normal", "Zera em 15 dias ou mais (ou sem projecao)", "Fluxo regular"],
    ]
    conteudo.append(tabela(prioridades, col_widths=[3 * cm, 7 * cm, 4 * cm]))
    conteudo.append(nota(
        "<b>Dias p/ Zerar</b> usa a Velocidade <b>Ativa</b> (dias em que efetivamente vendeu). "
        "Isso projeta ruptura mais cedo que a media simples e avisa antes."
    ))

    conteudo.append(h2("5.4 Motivos possiveis"))
    motivos = [
        ["Motivo", "Significado"],
        ["SEM ESTOQUE", "Ja zerou - urgente"],
        ["AGUARDANDO TRANSFERENCIA", "Saldo Provavel menor ou igual a 0 E tem envio a caminho (QtdEmTransito &gt; 0)"],
        ["RECEBIDO RECENTEMENTE", "Recebeu nos ultimos N dias (parametro Reposicao Recente)"],
        ["URGENTE - zera em N dias", "Vai zerar em breve"],
        ["Origem parada, destino vendendo", "Origem com velocidade &lt; 0.05 e destino &gt;= 0.1"],
        ["Alta rotacao no destino", "Destino vende 2x mais que origem"],
        ["Maior giro no destino", "Destino vende 1.5x mais que origem"],
        ["Reposicao de ciclo", "Padrao - mantem fluxo"],
    ]
    conteudo.append(tabela(motivos, col_widths=[6 * cm, 8 * cm]))

    conteudo.append(h2("5.5 Acoes de Fim de Linha - Liquidar e Descontinuar"))
    conteudo.append(p(
        "Quando um produto nao vende (ou vende muito pouco) em <b>nenhuma filial</b>, "
        "transferi-lo gera custo de frete e nao resolve a venda. O sistema cria duas secoes "
        "exclusivas de acao comercial."
    ))
    acoes_fim_linha = [
        ["Acao", "Quando acontece?", "O que o gestor deve fazer?"],
        ["LIQUIDAR", "Velocidade exata ZERO em toda a rede, mas ha estoque.", "Nao transferir. Promocao, queima ou devolver ao fornecedor."],
        ["DESCONTINUAR", "Velocidade &gt; 0 mas &lt; 0.1 (fim de ciclo), com estoque.", "Vender ate o fim do estoque. Nao repor e retirar do mix."],
    ]
    conteudo.append(tabela(acoes_fim_linha, col_widths=[3 * cm, 6 * cm, 5 * cm]))
    conteudo.append(nota(
        "O Atacado <b>nunca</b> entra em LIQUIDAR/DESCONTINUAR - apenas as lojas (filiais 1 a 4). "
        "O sistema tambem <b>nao</b> sugere transferir itens de liquidacao/descontinuacao entre lojas: "
        "o objetivo e resolver o estoque na origem."
    ))

    conteudo.append(h2("5.6 Reposicao Recente (anti-gangorra) - bloqueio inteligente"))
    conteudo.append(p(
        "A <b>Reposicao Recente</b> nao bloqueia cegamente toda nova transferencia. "
        "Ela bloqueia apenas quando o que ja foi recebido <b>cobre ou supera</b> a falta atual. "
        "Se recebeu 20 un e a falta continua em 50 un, o produto <b>volta a ser elegivel</b>."
    ))
    conteudo.append(nota(
        "Esse comportamento evita o <b>efeito chicote</b>: pedir de novo o que ja esta chegando. "
        "Estudo classico de P&G com fraldas Pampers mostrou que ignorar o que ja esta a caminho "
        "inflava a variabilidade em 30%+ na cadeia."
    ))

    conteudo.append(h2("5.7 Reserva Origem - arredondamento"))
    conteudo.append(p(
        "A Reserva e calculada como <b>ceil</b> (arredonda para cima) do percentual sobre o Excesso. "
        "Ex.: Excesso 400, Reserva 25% -> 100 un (exato). Excesso 45, Reserva 25% -> 12 un (11.25 arredondado)."
    ))

    conteudo.append(PageBreak())

    # ---------- PARTE 6 ----------
    conteudo.append(h1("Parte 6 - Rotina semanal"))
    conteudo.append(h2("6.1 Segunda-feira (10 min)"))
    conteudo.append(p("1. Abra o app"))
    conteudo.append(p("2. Clique em Parametros"))
    conteudo.append(p("3. Confira os padroes:"))
    conteudo.append(bullet("Periodo = '1 ano atras'"))
    conteudo.append(bullet("Cobertura = 'Para 30 dias'"))
    conteudo.append(bullet("Tempo de Transporte = 10"))
    conteudo.append(p("4. Escolha um Fabricante no topo"))
    conteudo.append(p("5. Clique em Consultar"))
    conteudo.append(p("6. Filtre por Prioridade = Critica"))

    conteudo.append(h2("6.2 Terca a Quinta (acao)"))
    conteudo.append(p("Para cada produto critico:"))
    conteudo.append(p("1. Veja o <b>Motivo</b>"))
    conteudo.append(p("2. Confirme a <b>Qtd Transf.</b>"))
    conteudo.append(p("3. Verifique a <b>Origem</b>"))
    conteudo.append(p("4. Clique em <b>Gerar PDF</b>"))
    conteudo.append(p("5. Crie a ordem no ERP"))

    conteudo.append(h2("6.3 Sexta-feira (10 min)"))
    conteudo.append(p("1. Reabra o app"))
    conteudo.append(p("2. Compare com a semana anterior"))
    conteudo.append(p("3. Ajuste parametros se necessario"))
    conteudo.append(PageBreak())

    # ---------- PARTE 7 ----------
    conteudo.append(h1("Parte 7 - Ajustes finos"))
    conteudo.append(h2("Cenario A - Sugerindo transferencia demais"))
    ajuste_a = [
        ["Ajuste", "Efeito"],
        ["Aumentar Reposicao Recente (15 -> 30)", "Bloqueia por mais tempo"],
        ["Aumentar Reserva Origem (25% -> 40%)", "Origem doa menos"],
        ["Diminuir Cobertura (30 -> 15)", "Ideal menor"],
    ]
    conteudo.append(tabela(ajuste_a, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenario B - Sugerindo transferencia de menos"))
    ajuste_b = [
        ["Ajuste", "Efeito"],
        ["Diminuir Reposicao Recente (15 -> 7)", "Bloqueia menos"],
        ["Diminuir Reserva Origem (25% -> 15%)", "Origem doa mais"],
        ["Aumentar Cobertura (30 -> 45)", "Ideal maior"],
    ]
    conteudo.append(tabela(ajuste_b, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenario C - Produto sempre zerado"))
    ajuste_c = [
        ["Ajuste", "Efeito"],
        ["Aumentar Piso Exposicao (0 -> 5)", "Minimo maior na prateleira"],
        ["Aumentar Cobertura", "Ideal maior"],
        ["Verificar Tempo de Transporte", "Corrigir se subestimado"],
    ]
    conteudo.append(tabela(ajuste_c, col_widths=[8 * cm, 6 * cm]))

    conteudo.append(h2("Cenario D - Duplicidade de envio"))
    ajuste_d = [
        ["Ajuste", "Efeito"],
        ["Aumentar Dias em Transito (10 -> 15)", "Cobre mais tempo"],
        ["Aumentar Reposicao Recente (15 -> 25)", "Quarentena maior"],
    ]
    conteudo.append(tabela(ajuste_d, col_widths=[8 * cm, 6 * cm]))
    conteudo.append(nota("Nunca mude 2 parametros ao mesmo tempo. Assim voce nao sabe qual causou o efeito."))
    conteudo.append(PageBreak())

    # ---------- PARTE 8 - FAQ 20 ----------
    conteudo.append(h1("Parte 8 - Perguntas frequentes"))
    faq = [
        ("O sistema demora quanto para carregar?",
         "Com filtro de fabricante: 30-60 segundos. Sem filtro: pode demorar mais."),
        ("Posso deixar em branco todos os filtros?",
         "Nao. Escolha pelo menos um."),
        ("Por que meu produto nao aparece?",
         "Varias causas: nao vendeu no periodo, esta nos departamentos INATIVO/USO INTERNO, "
         "nao tem excesso nem falta, o filtro excluiu, ou o produto foi removido automaticamente "
         "(ver proxima pergunta)."),
        ("Por que meu produto sumiu da analise automaticamente?",
         "Se o produto nao vendeu (velocidade < 0.1) em NENHUMA filial E nao tem saldo em NENHUMA, "
         "ele e removido. Volta a aparecer quando houver venda ou estoque."),
        ("A sugestao parece errada. O que faco?",
         "1. Verifique o Motivo. 2. Confira movimentacoes estranhas. 3. Verifique o Periodo. 4. Se persistir, acione TI."),
        ("Posso mudar os parametros toda hora?",
         "Nao recomendo. Deixe padrao por 15 dias antes de mexer."),
        ("O PDF pode ser editado?",
         "Nao, e um PDF padrao."),
        ("Como sei se um produto e doador ou receptor?",
         "Doador: secao ENVIAR. Receptor: secao RECEBER."),
        ("Preciso anotar tudo?",
         "Nao. Sempre confira o Motivo antes de aprovar."),
        ("Dois produtos competem pela mesma quantidade?",
         "O motor prioriza por urgencia (Critica -> Alta -> Normal)."),
        ("Como aciono o suporte?",
         "[Contato do responsavel pelo projeto]"),
        ("Consigo ver o historico de sugestoes?",
         "Hoje nao. Sugestao futura."),
        ("Posso exportar para Excel?",
         "So PDF hoje."),
        ("Por que o 'Reserva' varia?",
         "E o percentual (padrao 25%) sobre o Excesso, arredondado para cima. Quanto maior o Excesso, maior a Reserva."),
        ("O que e 'AGUARDANDO TRANSFERENCIA'?",
         "O saldo projetado esta <= 0 E ja existe envio a caminho. Nao duplica."),
        ("O que e 'RECEBIDO RECENTEMENTE'?",
         "Filial recebeu nos ultimos N dias (parametro Reposicao Recente). Esta em quarentena."),
        ("Posso transferir tudo que o sistema sugere?",
         "Nao. O programa nao substitui o bom senso. Sempre confira antes."),
        ("Quando o Ideal e 0?",
         "Produtos sem venda no periodo E sem Piso Exposicao configurado."),
        ("O sistema sugere menos de 5 unidades?",
         "Nao. O motor ignora transferencias < 5 un (MOQ interno para evitar custo logistico)."),
        ("Isso substitui o ERP?",
         "Nao. E uma ferramenta de decisao. A execucao continua no ERP."),
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
        ["MOQ", "Minimum Order Quantity - minimo de 5 un por transferencia"],
        ["Piso Exposicao", "Quantidade minima na prateleira"],
        ["Reposicao Recente", "Bloqueio parcial pos-recebimento"],
        ["Reserva Origem", "% do excesso que fica na origem (ceil)"],
        ["Saldo Ajustado", "SaldoProvavel + QtdEmTransito"],
        ["Saldo Provavel", "Estoque calculado (compras + recebidas - enviadas - vendidas)"],
        ["Tempo de Transporte", "Dias entre envio e entrega"],
        ["Velocidade Ativa", "Vendas / dias com venda (usada em Dias p/ Zerar)"],
        ["Velocidade Periodo", "Vendas / dias corridos (usada no Estoque Ideal)"],
    ]
    conteudo.append(tabela(glossario, col_widths=[5 * cm, 9 * cm]))
    conteudo.append(PageBreak())

    # ---------- PARTE 10 ----------
    conteudo.append(h1("Parte 10 - Casos praticos"))
    conteudo.append(p("Estes casos mostram situacoes reais do dia a dia e como o sistema reage a cada uma."))
    conteudo.append(Spacer(1, 0.3 * cm))

    conteudo.append(h2("Caso 1 - Produto em falta critica (RECEBER)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso1 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias", "Motivo"],
        ["1", "Critica", "562351", "FITA ADESIVA", "Atacado", "85", "3", "URGENTE"],
    ]
    conteudo.append(tabela(caso1, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: gerar PDF, enviar para o Atacado, criar ordem no ERP."))

    conteudo.append(h2("Caso 2 - Produto com excesso (ENVIAR)"))
    conteudo.append(p("Aba Atacado (ENVIAR):"))
    caso2 = [
        ["#", "Prior.", "Cod", "Produto", "Destino", "Qtd", "Reserva"],
        ["1", "Normal", "627893", "FITA PAPEL", "Alecrim", "50", "20"],
        ["2", "Normal", "627893", "FITA PAPEL", "Via Direta", "30", "20"],
    ]
    conteudo.append(tabela(caso2, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 3 * cm, 1.5 * cm, 2 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: confirmar rota, gerar PDF, criar 2 ordens (uma por destino)."))

    conteudo.append(h2("Caso 3 - Transferencia entre lojas (sem passar pelo Atacado)"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso3 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias"],
        ["5", "Alta", "612202", "SUSPENSORIO", "Via Direta", "20", "10"],
    ]
    conteudo.append(tabela(caso3, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 3 * cm, 1.5 * cm, 2 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Acao</b>: confirmar com a Via Direta, gerar PDF, criar ordem no ERP."))

    conteudo.append(h2("Caso 4 - Nenhuma sugestao encontrada"))
    conteudo.append(p("Mensagem: <b>'Nenhuma sugestao encontrada'</b>"))
    conteudo.append(p("Significa que nenhum produto atendeu aos criterios. O que fazer:"))
    conteudo.append(bullet("Confirmar se os produtos estao equilibrados"))
    conteudo.append(bullet("Tentar afrouxar a Cobertura (ex.: 15 dias)"))
    conteudo.append(bullet("Tentar outro periodo de analise (ex.: 6 meses)"))
    conteudo.append(bullet("Verificar se o filtro de Fabricante nao esta muito restritivo"))

    conteudo.append(PageBreak())

    # NOVOS CASOS - LIQUIDAR E DESCONTINUAR
    conteudo.append(h2("Caso 5 - Produto parado: LIQUIDAR"))
    conteudo.append(p("Aba Zona Norte (LIQUIDAR):"))
    caso5 = [
        ["#", "Prior.", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Liq.", "Motivo"],
        ["1", "Normal", "771234", "SQUEEZE HALLOWEEN", "UN", "CASA FESTA", "15", "ESTOQUE PARADO"],
    ]
    conteudo.append(tabela(caso5, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 1.5 * cm, 3 * cm, 2 * cm, 2 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Por que caiu aqui?</b> O produto nao teve <b>NENHUMA</b> venda (velocidade zero) nos ultimos 365 dias em toda a rede, mas a Zona Norte tem 15 unidades no estoque."))
    conteudo.append(p("<b>O que o sistema faz:</b> Nao sugere transferir para outras lojas. Transferir um produto que nao vende so gasta frete e nao gera receita."))
    conteudo.append(p("<b>Acao</b>: Criar uma promocao local, fazer um kit com outro produto, ou devolver ao fornecedor."))

    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(h2("Caso 6 - Produto de fim de ciclo: DESCONTINUAR"))
    conteudo.append(p("Aba Alecrim (DESCONTINUAR):"))
    caso6 = [
        ["#", "Prior.", "Cod", "Produto", "Emb.", "Fabricante", "Qtd p/ Desc.", "Motivo"],
        ["1", "Normal", "554433", "FITA CETIM VERMELHA", "UN", "ADERE", "8", "FIM DE CICLO"],
    ]
    conteudo.append(tabela(caso6, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 1.5 * cm, 3 * cm, 2 * cm, 2 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Por que caiu aqui?</b> O produto tem uma velocidade de venda muito baixa (ex: 0.08 un/dia, ou seja, 1 unidade a cada 12 dias) na rede inteira. O ciclo de vida dele acabou."))
    conteudo.append(p("<b>O que o sistema faz:</b> Nao sugere reposicao. Voce deve vender o que tem e nao comprar mais."))
    conteudo.append(p("<b>Acao</b>: Vender ate o fim do estoque atual. Nao fazer novas compras e retirar o item do mix da loja quando zerar."))

    conteudo.append(PageBreak())

    # NOVOS CASOS - ANTI-GANGORRA E MOQ
    conteudo.append(h2("Caso 7 - Produto recem-recebido: AGUARDANDO QUARENTENA"))
    conteudo.append(p("Aba Zona Sul (RECEBER):"))
    caso7 = [
        ["#", "Prior.", "Cod", "Produto", "Origem", "Qtd", "Dias", "Motivo"],
        ["3", "Alta", "889900", "PAPEL KRAFT", "Atacado", "40", "5", "RECEBIDO RECENTEMENTE"],
    ]
    conteudo.append(tabela(caso7, col_widths=[1 * cm, 2 * cm, 2 * cm, 3.5 * cm, 2 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm]))
    conteudo.append(Spacer(1, 0.2 * cm))
    conteudo.append(p("<b>Por que caiu aqui?</b> A Zona Sul ainda tem uma falta projetada, mas recebeu uma transferencia deste produto nos ultimos 15 dias (parametro Reposicao Recente)."))
    conteudo.append(p("<b>O que o sistema faz:</b> Mostra o alerta para voce saber que a falta existe, mas a origem ja mandou algo recentemente. Ele evita mandar de novo (efeito gangorra)."))
    conteudo.append(p("<b>Acao</b>: Verificar fisicamente na loja. Se a transferencia anterior ja cobre a falta, nao fazer nada. Se nao chegou, acionar a transportadora."))

    conteudo.append(Spacer(1, 0.3 * cm))
    conteudo.append(h2("Caso 8 - Falta pequena: A REGRA DO MINIMO DE 5"))
    conteudo.append(p("Voce consulta e nota que o produto 'Fita Refletiva' tem falta de 3 unidades na Zona Norte, mas ele <b>nao aparece</b> no sistema."))
    conteudo.append(p("<b>Por que nao aparece?</b> O motor ignora transferencias menores que 5 unidades em todas as regras. E o MOQ (Minimum Order Quantity)."))
    conteudo.append(p("<b>O que fazer:</b> O custo logistico (frete, separacao, embalagem) para mover 3 unidades e maior que o beneficio. Deixe o produto seguir o fluxo natural ou aguarde acumular uma falta maior."))

    # ---------- GERAR ----------
    doc.build(conteudo, canvasmaker=ManualCanvas)
    if buffer is None:
        print("PDF gerado com sucesso: Manual_Reposicao_Gestor.pdf")
    else:
        buffer.seek(0)


if __name__ == "__main__":
    gerar()