"""Regras de transferência (DRP + IST + MEIO)."""

import pandas as pd
import numpy as np


MATRIZ_PROXIMIDADE = {
    1: [5, 2, 3, 4],
    2: [5, 1, 3],
    3: [5, 1, 2],
    4: [5, 1],
    5: [],
}


def calcular_indicadores(
    df: pd.DataFrame,
    cobertura_alvo: int = 30,
    lead_time: int = 10,
    piso_exposicao: int = 0,
    reserva_pct: float = 25,
    atacado_tem_piso: bool = False,
    atacado_tem_reserva: bool = False,
) -> pd.DataFrame:
    df = df.copy()
    dias = cobertura_alvo + lead_time

    def _piso(cod):
        if cod == 5 and not atacado_tem_piso:
            return 0
        return piso_exposicao

    def _reserva(cod):
        if cod == 5 and not atacado_tem_reserva:
            return 0
        return reserva_pct

    df["Piso"] = df["CodigoFilial"].apply(_piso)
    df["EstoqueIdeal"] = np.maximum(df["Piso"], df["VelocidadePeriodo"] * dias).round(0).astype(int)
    df["Excesso"] = np.maximum(0, df["SaldoProvavel"] - df["EstoqueIdeal"])
    # Saldo negativo é tratado como 0 para não "resgatar" dívidas de erros de movimentação
    df["Falta"] = np.maximum(0, df["EstoqueIdeal"] - np.maximum(0, df["SaldoAjustado"]))

    df["PercReserva"] = df["CodigoFilial"].apply(_reserva)
    df["ReservaOrigem"] = np.ceil(df["Excesso"] * df["PercReserva"] / 100).astype(int)

    df["ExcessoTransferivel"] = np.maximum(0, df["Excesso"] - df["ReservaOrigem"])

    df["DiasAteZerar"] = np.where(
        (df["VelocidadeAtiva"] > 0) & (df["SaldoAjustado"] > 0),
        df["SaldoAjustado"] / df["VelocidadeAtiva"],
        np.where(df["SaldoAjustado"] <= 0, 0, np.nan),
    )

    return df


def filtrar_recentes(df: pd.DataFrame, df_recentes: pd.DataFrame | None) -> pd.DataFrame:
    if df_recentes is None or df_recentes.empty:
        df["QtdRecebidaRecente"] = 0
        return df

    chave = df["IdProduto"].astype(str) + "-" + df["CodigoFilial"].astype(str)
    chave_rec = df_recentes["IdProduto"].astype(str) + "-" + df_recentes["CodFilial"].astype(str)
    mapa = dict(zip(chave_rec, df_recentes["QtdRecebidaRecente"]))

    df["QtdRecebidaRecente"] = chave.map(mapa).fillna(0)
    df["QtdRecebidaRecente"] = pd.to_numeric(df["QtdRecebidaRecente"], errors="coerce").fillna(0)
    return df


def processar_demonstrar(grupo: pd.DataFrame) -> tuple[list[dict], list[int], pd.DataFrame]:
    """
    Etapa 1: Identifica lojas sem histórico e busca doadora (excedente >= 5).
    Retorna: (lista_demonstracoes, lista_cod_filiais_destino_bloqueadas, grupo_atualizado)
    """
    QUANTIDADE_INICIAL = 5
    demonstracoes = []
    lojas_bloqueadas = []
    
    # Copia o grupo para atualizar o excesso da doadora sem sujar o original
    grupo_atual = grupo.copy()
    
    # Dicionário para busca rápida de doadora por matriz de proximidade
    doadoras_por_cod = {int(r["CodigoFilial"]): r for _, r in grupo_atual.iterrows()}
    # Mapeia o excesso disponível dinamicamente
    excesso_livre = {int(r["CodigoFilial"]): max(0, int(r["ExcessoTransferivel"])) for _, r in grupo_atual.iterrows()}

    for _, loja in grupo_atual.iterrows():
        cod_loja = int(loja["CodigoFilial"])
        if cod_loja == 5: # Atacado não é avaliado para DEMONSTRAR
            continue

        # Verifica se a loja não tem nenhum histórico nem trânsito
        if (loja["QtdComprada"] == 0 and loja["QtdRecebida"] == 0 and
            loja["QtdVendida"] == 0 and loja["QtdEnviada"] == 0 and
            loja["QtdEmTransito"] == 0):
            
            # Busca doadora na matriz de proximidade que tenha EXCEDENTE >= 5
            doadora = None
            for cod_doador in MATRIZ_PROXIMIDADE.get(cod_loja, []):
                if excesso_livre.get(cod_doador, 0) >= QUANTIDADE_INICIAL:
                    doadora = doadoras_por_cod[cod_doador]
                    break
            
            if doadora is not None:
                cod_origem = int(doadora["CodigoFilial"])
                # Consome o excesso da doadora
                excesso_livre[cod_origem] -= QUANTIDADE_INICIAL
                # Atualiza no dataframe para refletir nas próximas alocações normais
                grupo_atual.loc[grupo_atual["CodigoFilial"] == cod_origem, "ExcessoTransferivel"] -= QUANTIDADE_INICIAL
                grupo_atual.loc[grupo_atual["CodigoFilial"] == cod_origem, "SaldoProvavel"] -= QUANTIDADE_INICIAL

                demonstracoes.append({
                    "Prioridade": 3,
                    "CodigoProduto": loja["CodigoProduto"],
                    "ReferenciaFabricante": loja["ReferenciaFabricante"],
                    "Produto": loja["Produto"],
                    "Fabricante": loja["Fabricante"],
                    "Embalagem": loja["Embalagem"],
                    "CodigoFilialOrigem": cod_origem,
                    "NomeFilialOrigem": doadora["Filial"],
                    "CodigoFilialDestino": cod_loja,
                    "NomeFilialDestino": loja["Filial"],
                    "QtdTransferir": QUANTIDADE_INICIAL,
                    "ReservaOrigem": 0,
                    "IdealOrigem": 0,
                    "IdealDestino": 0,
                    "DiasAteZerarDestino": None,
                    "Motivo": "Sem Registro na Filial",
                    "SaldoAjustado": int(loja["SaldoAjustado"]),
                    "QtdEmTransito": int(loja["QtdEmTransito"]),
                    "RetornoFinanceiro": 0
                })
                lojas_bloqueadas.append(cod_loja)

    return demonstracoes, lojas_bloqueadas, grupo_atual


def alocar_fluxo_normal(df_produto: pd.DataFrame, piso_exposicao: int = 0, atacado_tem_minimo_compra: bool = False) -> tuple[list[dict], list[dict]]:
    """Gera transferências e compras normais (Velocidade >= 0.1 na rede)"""
    receptoras = df_produto[df_produto["Falta"] >= 5].copy()
    receptoras = receptoras[receptoras["QtdRecebidaRecente"] < receptoras["Falta"]]
    receptoras = receptoras.sort_values(["VelocidadePeriodo", "VelocidadeAtiva", "DiasInativo"], ascending=[False, False, True])

    doadoras = df_produto[df_produto["ExcessoTransferivel"] >= 5].copy()
    doadoras = doadoras.sort_values(["VelocidadePeriodo", "VelocidadeAtiva"], ascending=[True, True])

    excesso_livre = dict(zip(doadoras["CodigoFilial"], doadoras["ExcessoTransferivel"]))
    alocacoes = []
    compras = []

    for _, rec in receptoras.iterrows():
        precisa = rec["Falta"]
        qtd_recebida_transf = 0
        ordem = MATRIZ_PROXIMIDADE.get(rec["CodigoFilial"], [])

        for cod_doador in ordem:
            if precisa < 5: break
            if excesso_livre.get(cod_doador, 0) < 5: continue

            doa = doadoras[doadoras["CodigoFilial"] == cod_doador].iloc[0]
            qtd = int(min(excesso_livre[cod_doador], precisa))
            if qtd < 5: break

            if rec["QtdEmTransito"] > 0: 
                motivo = "AGUARDANDO TRANSFERENCIA"
            elif rec["SaldoAjustado"] <= 0: 
                motivo = "SEM ESTOQUE"
            elif rec["QtdRecebidaRecente"] > 0: 
                motivo = f"RECEBIDO RECENTEMENTE ({int(rec['QtdRecebidaRecente'])} un)"
            elif pd.notna(rec["DiasAteZerar"]) and rec["DiasAteZerar"] < 7: 
                if rec["DiasAteZerar"] < 1:
                    motivo = "URGENTE - zera hoje"
                else:
                    motivo = f"URGENTE - zera em {int(rec['DiasAteZerar'])} dias"
            elif doa["VelocidadePeriodo"] < 0.05 and rec["VelocidadePeriodo"] >= 0.1: 
                motivo = "Origem parada, destino vendendo"
            elif rec["VelocidadePeriodo"] > doa["VelocidadePeriodo"] * 2: 
                motivo = "Alta rotacao no destino"
            elif rec["VelocidadePeriodo"] > doa["VelocidadePeriodo"] * 1.5: 
                motivo = "Maior giro no destino"
            else: 
                motivo = "Reposicao de ciclo"

            if pd.isna(rec["DiasAteZerar"]): prio = 3
            elif rec["DiasAteZerar"] < 7: prio = 1
            elif rec["DiasAteZerar"] < 15: prio = 2
            else: prio = 3

            alocacoes.append({
                "Prioridade": prio, "CodigoProduto": rec["CodigoProduto"],
                "ReferenciaFabricante": rec["ReferenciaFabricante"], "Produto": rec["Produto"],
                "Fabricante": rec["Fabricante"], "Embalagem": rec["Embalagem"],
                "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                "CodigoFilialDestino": int(rec["CodigoFilial"]), "NomeFilialDestino": rec["Filial"],
                "QtdTransferir": qtd, "ReservaOrigem": int(doa["ReservaOrigem"]),
                "IdealOrigem": int(doa["EstoqueIdeal"]), "IdealDestino": int(rec["EstoqueIdeal"]),
                "DiasAteZerarDestino": round(rec["DiasAteZerar"], 1) if pd.notna(rec["DiasAteZerar"]) else None,
                "Motivo": motivo, "SaldoAjustado": int(rec["SaldoAjustado"]),
                "QtdEmTransito": int(rec["QtdEmTransito"]),
                "RetornoFinanceiro": 0
            })

            excesso_livre[cod_doador] -= qtd
            precisa -= qtd
            qtd_recebida_transf += qtd

        # Cálculo da Compra (usando Falta em vez de Ideal)
        necessidade_ideal = max(0, rec["Falta"] - qtd_recebida_transf)
        
        if necessidade_ideal > 0:
            minimo = piso_exposicao if atacado_tem_minimo_compra else 1
            if necessidade_ideal >= minimo:
                if qtd_recebida_transf == 0 and rec["SaldoAjustado"] <= 0:
                    motivo_compra = "SEM ESTOQUE"
                else:
                    motivo_compra = "ESTOQUE COMPLEMENTAR"

                preco_venda = rec["PrecoVenda1"] if rec["CodigoFilial"] == 1 else rec["PrecoVenda2"]
                custo = rec["CustoUnitario"]
                margem = preco_venda - custo
                retorno_fin = margem * int(necessidade_ideal)
                
                compras.append({
                    "NomeFilialDestino": rec["Filial"],
                    "CodigoProduto": rec["CodigoProduto"],
                    "ReferenciaFabricante": rec["ReferenciaFabricante"],
                    "Produto": rec["Produto"],
                    "Fabricante": rec["Fabricante"],
                    "Embalagem": rec["Embalagem"],
                    "QtdSugerida": int(necessidade_ideal),
                    "Motivo": motivo_compra,
                    "Velocidade": rec["VelocidadePeriodo"],
                    "Ideal": rec["EstoqueIdeal"],
                    "Custo": rec["CustoCompra2"],
                    "RetornoFinanceiro": retorno_fin
                })

    atacado = df_produto[df_produto["CodigoFilial"] == 5]
    if not atacado.empty:
        falta_atacado_ideal = atacado.iloc[0]["EstoqueIdeal"] - atacado.iloc[0]["SaldoAjustado"]
        if falta_atacado_ideal > 0:
            minimo = piso_exposicao if atacado_tem_minimo_compra else 1
            if falta_atacado_ideal >= minimo:
                if atacado.iloc[0]["SaldoAjustado"] <= 0:
                    motivo_compra = "SEM ESTOQUE"
                else:
                    motivo_compra = "ESTOQUE COMPLEMENTAR"

                preco_venda = atacado.iloc[0]["PrecoVenda2"]
                custo = atacado.iloc[0]["CustoUnitario"]
                margem = preco_venda - custo
                retorno_fin = margem * int(falta_atacado_ideal)

                compras.append({
                    "NomeFilialDestino": "ATACADO",
                    "CodigoProduto": atacado.iloc[0]["CodigoProduto"],
                    "ReferenciaFabricante": atacado.iloc[0]["ReferenciaFabricante"],
                    "Produto": atacado.iloc[0]["Produto"],
                    "Fabricante": atacado.iloc[0]["Fabricante"],
                    "Embalagem": atacado.iloc[0]["Embalagem"],
                    "QtdSugerida": int(falta_atacado_ideal),
                    "Motivo": motivo_compra,
                    "Velocidade": atacado.iloc[0]["VelocidadePeriodo"],
                    "Ideal": atacado.iloc[0]["EstoqueIdeal"],
                    "Custo": atacado.iloc[0]["CustoCompra2"],
                    "RetornoFinanceiro": retorno_fin
                })

    return alocacoes, compras


def gerar_sugestoes(
    df_base: pd.DataFrame,
    df_transito: pd.DataFrame | None = None,
    df_recebidas_recentes: pd.DataFrame | None = None,
    cobertura_alvo: int = 30,
    lead_time: int = 10,
    piso_exposicao: int = 0,
    reserva_pct: float = 25,
    atacado_tem_piso: bool = False,
    atacado_tem_reserva: bool = False,
    atacado_tem_minimo_compra: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
    df = df_base.copy()

    # 1. Prepara dados de trânsito
    if df_transito is not None and not df_transito.empty:
        df_tr = df_transito.groupby(["IdProduto", "CodFilialDestino"], as_index=False)["QtdEmTransito"].sum()
        df = df.merge(df_tr, left_on=["IdProduto", "CodigoFilial"], right_on=["IdProduto", "CodFilialDestino"], how="left")
        df["QtdEmTransito"] = df["QtdEmTransito"].fillna(0)
        df.drop(columns=["CodFilialDestino"], inplace=True)
    else:
        df["QtdEmTransito"] = 0

    df["QtdEmTransito"] = pd.to_numeric(df["QtdEmTransito"], errors="coerce").fillna(0)
    df["SaldoProvavel"] = pd.to_numeric(df["SaldoProvavel"], errors="coerce").fillna(0)
    df["SaldoAjustado"] = df["SaldoProvavel"] + df["QtdEmTransito"]

    # 2. Aplica quarentena antes de qualquer análise
    df = filtrar_recentes(df, df_recebidas_recentes)

    # 3. Calcula Indicadores Base (Ideal, Excesso, Falta, etc.)
    df = calcular_indicadores(df, cobertura_alvo, lead_time, piso_exposicao, reserva_pct, atacado_tem_piso, atacado_tem_reserva)

    todas_transf = []
    todas_compras = []
    todas_demonstracoes = []

    # 4. Loop Produto a Produto com CASCATA (Waterfall)
    for prod_id, grupo in df.groupby("IdProduto"):
        
        # --- ETAPA 1: DEMONSTRAR ---
        dems, lojas_bloqueadas, grupo_atualizado = processar_demonstrar(grupo)
        todas_demonstracoes.extend(dems)

        # Filtra o grupo removendo as lojas que já foram atendidas no DEMONSTRAR
        grupo_restante = grupo_atualizado[~grupo_atualizado["CodigoFilial"].isin(lojas_bloqueadas)].copy()
        
        if grupo_restante.empty:
            continue

        # --- ETAPA 2, 3 e 4: DESC, LIQ ou NORMAL ---
        # Avalia apenas as lojas que sobraram (Dúvida 2 - Opção B)
        vel_max = grupo_restante["VelocidadePeriodo"].max()

        if vel_max == 0:
            # --- LIQUIDAR ---
            # Só liquida se já teve histórico
            _tem_hist = (grupo_restante["QtdComprada"] > 0) | (grupo_restante["QtdRecebida"] > 0) | (grupo_restante["QtdVendida"] > 0) | (grupo_restante["QtdEnviada"] > 0)
            _elegivel = (grupo_restante["SaldoProvavel"] > 0) & (grupo_restante["QtdRecebidaRecente"] == 0) & _tem_hist
            doadoras = grupo_restante[(grupo_restante["CodigoFilial"] != 5) & _elegivel]
            
            for _, doa in doadoras.iterrows():
                qtd = int(doa["SaldoProvavel"])
                if qtd >= 5:
                    todas_transf.append({
                        "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                        "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                        "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                        "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                        "CodigoFilialDestino": 0, "NomeFilialDestino": "LIQUIDAR",
                        "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                        "DiasAteZerarDestino": None, "Motivo": "ESTOQUE PARADO",
                        "SaldoAjustado": int(doa["SaldoProvavel"]),
                        "QtdEmTransito": 0, "RetornoFinanceiro": 0
                    })

        elif vel_max < 0.1:
            # --- DESCONTINUAR ---
            # Só descontinua se já teve histórico
            _tem_hist = (grupo_restante["QtdComprada"] > 0) | (grupo_restante["QtdRecebida"] > 0) | (grupo_restante["QtdVendida"] > 0) | (grupo_restante["QtdEnviada"] > 0)
            _elegivel = (grupo_restante["SaldoProvavel"] > 0) & (grupo_restante["QtdRecebidaRecente"] == 0) & _tem_hist
            doadoras = grupo_restante[(grupo_restante["CodigoFilial"] != 5) & _elegivel]
            
            for _, doa in doadoras.iterrows():
                qtd = int(doa["SaldoProvavel"])
                if qtd >= 5:
                    todas_transf.append({
                        "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                        "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                        "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                        "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                        "CodigoFilialDestino": 0, "NomeFilialDestino": "DESCONTINUAR",
                        "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                        "DiasAteZerarDestino": None, "Motivo": "FIM DE CICLO",
                        "SaldoAjustado": int(doa["SaldoProvavel"]),
                        "QtdEmTransito": 0, "RetornoFinanceiro": 0
                    })

        else:
            # --- FLUXO NORMAL (ENVIAR / RECEBER / COMPRAR) ---
            t, c = alocar_fluxo_normal(grupo_restante, piso_exposicao, atacado_tem_minimo_compra)
            todas_transf.extend(t)
            todas_compras.extend(c)

    # Formata os DataFrames de saída
    df_transf = pd.DataFrame(todas_transf)
    if not df_transf.empty:
        df_transf = df_transf.sort_values(["Prioridade", "NomeFilialDestino", "Produto", "Fabricante"]).reset_index(drop=True)

    df_compras = pd.DataFrame(todas_compras)
    if not df_compras.empty:
        df_compras = df_compras.sort_values(["NomeFilialDestino", "Produto"]).reset_index(drop=True)

    df_demonstracao = pd.DataFrame(todas_demonstracoes)
    if not df_demonstracao.empty:
        df_demonstracao = df_demonstracao.sort_values(["NomeFilialOrigem", "Produto"]).reset_index(drop=True)

    return df_transf, df_compras, df_demonstracao