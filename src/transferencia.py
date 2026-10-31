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

def calcular_qtd_minima(pesavel: str, custo_unitario: float, qtd_padrao: float = 5.0) -> float:
    if str(pesavel).strip().upper() == 'S':
        return 0.1  # 100g para produtos pesáveis
    if custo_unitario >= 20.0:
        return 1.0
    return float(qtd_padrao)

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
    df["Piso"] = df.apply(lambda r: calcular_qtd_minima(r["ProdutoPesavel"], r["CustoUnitario"], float(r["Piso"])), axis=1)
    
    df["EstoqueIdeal"] = np.maximum(df["Piso"], df["VelocidadePeriodo"] * dias).round(2)
    df["Excesso"] = np.maximum(0, df["SaldoProvavel"] - df["EstoqueIdeal"]).round(2)
    df["Falta"] = np.maximum(0, df["EstoqueIdeal"] - np.maximum(0, df["SaldoAjustado"])).round(2)

    df["PercReserva"] = df["CodigoFilial"].apply(_reserva)
    df["ReservaOrigem"] = np.ceil(df["Excesso"] * df["PercReserva"] / 100).round(2)
    df["ExcessoTransferivel"] = np.maximum(0, df["Excesso"] - df["ReservaOrigem"]).round(2)

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
    demonstracoes = []
    lojas_bloqueadas = []
    
    grupo_atual = grupo.copy()
    doadoras_por_cod = {int(r["CodigoFilial"]): r for _, r in grupo_atual.iterrows()}
    excesso_livre = {int(r["CodigoFilial"]): max(0, float(r["ExcessoTransferivel"])) for _, r in grupo_atual.iterrows()}

    for _, loja in grupo_atual.iterrows():
        cod_loja = int(loja["CodigoFilial"])
        if cod_loja == 5:
            continue

        if (loja["QtdComprada"] == 0 and loja["QtdRecebida"] == 0 and
            loja["QtdVendida"] == 0 and loja["QtdEnviada"] == 0 and
            loja["QtdEmTransito"] == 0):
            
            doadora = None
            for cod_doador in MATRIZ_PROXIMIDADE.get(cod_loja, []):
                qtd_min = calcular_qtd_minima(loja["ProdutoPesavel"], loja["CustoUnitario"], 5.0)
                if excesso_livre.get(cod_doador, 0) >= qtd_min:
                    doadora = doadoras_por_cod[cod_doador]
                    break
            
            if doadora is not None:
                qtd_envio = calcular_qtd_minima(loja["ProdutoPesavel"], loja["CustoUnitario"], 5.0)
                cod_origem = int(doadora["CodigoFilial"])
                
                excesso_livre[cod_origem] -= qtd_envio
                grupo_atual.loc[grupo_atual["CodigoFilial"] == cod_origem, "ExcessoTransferivel"] -= qtd_envio
                grupo_atual.loc[grupo_atual["CodigoFilial"] == cod_origem, "SaldoProvavel"] -= qtd_envio

                demonstracoes.append({
                    "Prioridade": 3, "CodigoProduto": loja["CodigoProduto"],
                    "ReferenciaFabricante": loja["ReferenciaFabricante"], "Produto": loja["Produto"],
                    "Fabricante": loja["Fabricante"], "Embalagem": loja["Embalagem"],
                    "CodigoFilialOrigem": cod_origem, "NomeFilialOrigem": doadora["Filial"],
                    "CodigoFilialDestino": cod_loja, "NomeFilialDestino": loja["Filial"],
                    "QtdTransferir": qtd_envio, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                    "DiasAteZerarDestino": None, "Motivo": "Sem Registro na Filial",
                    "SaldoAjustado": loja["SaldoAjustado"], "QtdEmTransito": loja["QtdEmTransito"],
                    "RetornoFinanceiro": 0
                })
                lojas_bloqueadas.append(cod_loja)

    return demonstracoes, lojas_bloqueadas, grupo_atual


def alocar_fluxo_normal(df_produto: pd.DataFrame, piso_exposicao: int = 0, atacado_tem_minimo_compra: bool = False) -> tuple[list[dict], list[dict]]:
    receptoras = df_produto[df_produto["Falta"] > 0].copy()
    receptoras = receptoras[receptoras["QtdRecebidaRecente"] < receptoras["Falta"]]
    receptoras = receptoras.sort_values(["VelocidadePeriodo", "VelocidadeAtiva", "DiasInativo"], ascending=[False, False, True])

    doadoras = df_produto[df_produto["ExcessoTransferivel"] > 0].copy()
    doadoras = doadoras.sort_values(["VelocidadePeriodo", "VelocidadeAtiva"], ascending=[True, True])

    excesso_livre = dict(zip(doadoras["CodigoFilial"], doadoras["ExcessoTransferivel"]))
    alocacoes = []
    compras = []

    for _, rec in receptoras.iterrows():
        precisa = rec["Falta"]
        qtd_recebida_transf = 0
        ordem = MATRIZ_PROXIMIDADE.get(rec["CodigoFilial"], [])
        
        qtd_min_rec = calcular_qtd_minima(rec["ProdutoPesavel"], rec["CustoUnitario"], 5.0)

        for cod_doador in ordem:
            if precisa < qtd_min_rec: break
            if excesso_livre.get(cod_doador, 0) < qtd_min_rec: continue

            doa = doadoras[doadoras["CodigoFilial"] == cod_doador].iloc[0]
            qtd = min(excesso_livre[cod_doador], precisa)
            if qtd < qtd_min_rec: break

            if rec["QtdEmTransito"] > 0: motivo = "AGUARDANDO TRANSFERENCIA"
            elif rec["SaldoAjustado"] <= 0: motivo = "SEM ESTOQUE"
            elif rec["QtdRecebidaRecente"] > 0: motivo = f"RECEBIDO RECENTEMENTE ({rec['QtdRecebidaRecente']} un)"
            elif pd.notna(rec["DiasAteZerar"]) and rec["DiasAteZerar"] < 7: 
                motivo = "URGENTE - zera hoje" if rec["DiasAteZerar"] < 1 else f"URGENTE - zera em {int(rec['DiasAteZerar'])} dias"
            elif doa["VelocidadePeriodo"] < 0.05 and rec["VelocidadePeriodo"] >= 0.1: motivo = "Origem parada, destino vendendo"
            elif rec["VelocidadePeriodo"] > doa["VelocidadePeriodo"] * 2: motivo = "Alta rotacao no destino"
            elif rec["VelocidadePeriodo"] > doa["VelocidadePeriodo"] * 1.5: motivo = "Maior giro no destino"
            else: motivo = "Reposicao de ciclo"

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
                "QtdTransferir": qtd, "ReservaOrigem": doa["ReservaOrigem"],
                "IdealOrigem": doa["EstoqueIdeal"], "IdealDestino": rec["EstoqueIdeal"],
                "DiasAteZerarDestino": round(rec["DiasAteZerar"], 1) if pd.notna(rec["DiasAteZerar"]) else None,
                "Motivo": motivo, "SaldoAjustado": rec["SaldoAjustado"],
                "QtdEmTransito": rec["QtdEmTransito"], "RetornoFinanceiro": 0
            })

            excesso_livre[cod_doador] -= qtd
            precisa -= qtd
            qtd_recebida_transf += qtd

        necessidade_ideal = max(0, rec["Falta"] - qtd_recebida_transf)
        limite_compra = 0.01 if str(rec["ProdutoPesavel"]).strip().upper() == 'S' else 0.10
        
        if necessidade_ideal > 0 and rec["VelocidadePeriodo"] >= limite_compra:
            minimo = piso_exposicao if atacado_tem_minimo_compra else qtd_min_rec
            if necessidade_ideal >= minimo:
                motivo_compra = "SEM ESTOQUE" if qtd_recebida_transf == 0 and rec["SaldoAjustado"] <= 0 else "ESTOQUE COMPLEMENTAR"
                preco_venda = rec["PrecoVenda1"] if rec["CodigoFilial"] == 1 else rec["PrecoVenda2"]
                margem = preco_venda - rec["CustoUnitario"]
                retorno_fin = margem * necessidade_ideal
                
                compras.append({
                    "NomeFilialDestino": rec["Filial"], "CodigoProduto": rec["CodigoProduto"],
                    "ReferenciaFabricante": rec["ReferenciaFabricante"], "Produto": rec["Produto"],
                    "Fabricante": rec["Fabricante"], "Embalagem": rec["Embalagem"],
                    "QtdSugerida": necessidade_ideal, "Motivo": motivo_compra,
                    "Velocidade": rec["VelocidadePeriodo"], "Ideal": rec["EstoqueIdeal"],
                    "Custo": rec["CustoCompra2"], "RetornoFinanceiro": retorno_fin
                })

    atacado = df_produto[df_produto["CodigoFilial"] == 5]
    if not atacado.empty:
        falta_atacado_ideal = atacado.iloc[0]["EstoqueIdeal"] - atacado.iloc[0]["SaldoAjustado"]
        if falta_atacado_ideal > 0:
            qtd_min_atac = calcular_qtd_minima(atacado.iloc[0]["ProdutoPesavel"], atacado.iloc[0]["CustoUnitario"], 5.0)
            minimo = piso_exposicao if atacado_tem_minimo_compra else qtd_min_atac
            if falta_atacado_ideal >= minimo:
                motivo_compra = "SEM ESTOQUE" if atacado.iloc[0]["SaldoAjustado"] <= 0 else "ESTOQUE COMPLEMENTAR"
                preco_venda = atacado.iloc[0]["PrecoVenda2"]
                margem = preco_venda - atacado.iloc[0]["CustoUnitario"]
                retorno_fin = margem * falta_atacado_ideal

                compras.append({
                    "NomeFilialDestino": "ATACADO", "CodigoProduto": atacado.iloc[0]["CodigoProduto"],
                    "ReferenciaFabricante": atacado.iloc[0]["ReferenciaFabricante"], "Produto": atacado.iloc[0]["Produto"],
                    "Fabricante": atacado.iloc[0]["Fabricante"], "Embalagem": atacado.iloc[0]["Embalagem"],
                    "QtdSugerida": falta_atacado_ideal, "Motivo": motivo_compra,
                    "Velocidade": atacado.iloc[0]["VelocidadePeriodo"], "Ideal": atacado.iloc[0]["EstoqueIdeal"],
                    "Custo": atacado.iloc[0]["CustoCompra2"], "RetornoFinanceiro": retorno_fin
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
        dems, lojas_bloqueadas, grupo_atualizado = processar_demonstrar(grupo)
        todas_demonstracoes.extend(dems)

        grupo_restante = grupo_atualizado[~grupo_atualizado["CodigoFilial"].isin(lojas_bloqueadas)].copy()
        if grupo_restante.empty: continue

        vel_max = grupo_restante["VelocidadePeriodo"].max()
        is_pesavel = str(grupo_restante.iloc[0].get("ProdutoPesavel", "N")).strip().upper() == "S"
        qtd_min = calcular_qtd_minima(grupo_restante.iloc[0].get("ProdutoPesavel", "N"), grupo_restante.iloc[0]["CustoUnitario"], 5.0)
        limite_desc = 0.01 if is_pesavel else 0.1

        # Trava de Recompra
        atacado_grupo = grupo_restante[grupo_restante["CodigoFilial"] == 5]
        tem_estoque_atacado = not atacado_grupo.empty and atacado_grupo.iloc[0]["SaldoProvavel"] > 0
        tem_falta_lojas = grupo_restante[grupo_restante["CodigoFilial"] != 5]["Falta"].max() >= qtd_min
        forcar_normal = tem_estoque_atacado and tem_falta_lojas

        if vel_max == 0 and not forcar_normal:
            _tem_hist = (grupo_restante["QtdComprada"] > 0) | (grupo_restante["QtdRecebida"] > 0) | (grupo_restante["QtdVendida"] > 0) | (grupo_restante["QtdEnviada"] > 0)
            _elegivel = (grupo_restante["SaldoProvavel"] > 0) & (grupo_restante["QtdRecebidaRecente"] == 0) & _tem_hist
            doadoras = grupo_restante[(grupo_restante["CodigoFilial"] != 5) & _elegivel]
            
            for _, doa in doadoras.iterrows():
                qtd = doa["SaldoProvavel"]
                if qtd >= qtd_min:
                    todas_transf.append({
                        "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                        "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                        "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                        "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                        "CodigoFilialDestino": 0, "NomeFilialDestino": "LIQUIDAR",
                        "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                        "DiasAteZerarDestino": None, "Motivo": "ESTOQUE PARADO",
                        "SaldoAjustado": doa["SaldoProvavel"], "QtdEmTransito": 0, "RetornoFinanceiro": 0
                    })

        elif vel_max < limite_desc and not forcar_normal:
            _tem_hist = (grupo_restante["QtdComprada"] > 0) | (grupo_restante["QtdRecebida"] > 0) | (grupo_restante["QtdVendida"] > 0) | (grupo_restante["QtdEnviada"] > 0)
            _elegivel = (grupo_restante["SaldoProvavel"] > 0) & (grupo_restante["QtdRecebidaRecente"] == 0) & _tem_hist
            doadoras = grupo_restante[(grupo_restante["CodigoFilial"] != 5) & _elegivel]
            
            for _, doa in doadoras.iterrows():
                qtd = doa["SaldoProvavel"]
                if qtd >= qtd_min:
                    todas_transf.append({
                        "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                        "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                        "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                        "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                        "CodigoFilialDestino": 0, "NomeFilialDestino": "DESCONTINUAR",
                        "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                        "DiasAteZerarDestino": None, "Motivo": "FIM DE CICLO NA REDE",
                        "SaldoAjustado": doa["SaldoProvavel"], "QtdEmTransito": 0, "RetornoFinanceiro": 0
                    })

        else:
            t, c = alocar_fluxo_normal(grupo_restante, piso_exposicao, atacado_tem_minimo_compra)
            todas_transf.extend(t)
            todas_compras.extend(c)

    # Formata os DataFrames de saída
    df_transf = pd.DataFrame(todas_transf)
    if not df_transf.empty:
        df_transf = df_transf.sort_values(["Prioridade", "NomeFilialDestino", "Produto", "Fabricante"]).reset_index(drop=True)
    else:
        df_transf = pd.DataFrame(columns=["Prioridade", "CodigoProduto", "ReferenciaFabricante", "Produto", "Fabricante", "Embalagem", "CodigoFilialOrigem", "NomeFilialOrigem", "CodigoFilialDestino", "NomeFilialDestino", "QtdTransferir", "ReservaOrigem", "IdealOrigem", "IdealDestino", "DiasAteZerarDestino", "Motivo", "SaldoAjustado", "QtdEmTransito", "RetornoFinanceiro"])

    df_compras = pd.DataFrame(todas_compras)
    if not df_compras.empty:
        df_compras = df_compras.sort_values(["NomeFilialDestino", "Produto"]).reset_index(drop=True)
    else:
        df_compras = pd.DataFrame(columns=["NomeFilialDestino", "CodigoProduto", "ReferenciaFabricante", "Produto", "Fabricante", "Embalagem", "QtdSugerida", "Motivo", "Velocidade", "Ideal", "Custo", "RetornoFinanceiro"])

    df_demonstracao = pd.DataFrame(todas_demonstracoes)
    if not df_demonstracao.empty:
        df_demonstracao = df_demonstracao.sort_values(["NomeFilialOrigem", "Produto"]).reset_index(drop=True)
    else:
        df_demonstracao = pd.DataFrame(columns=["Prioridade", "CodigoProduto", "ReferenciaFabricante", "Produto", "Fabricante", "Embalagem", "CodigoFilialOrigem", "NomeFilialOrigem", "CodigoFilialDestino", "NomeFilialDestino", "QtdTransferir", "ReservaOrigem", "IdealOrigem", "IdealDestino", "DiasAteZerarDestino", "Motivo", "SaldoAjustado", "QtdEmTransito", "RetornoFinanceiro"])

    return df_transf, df_compras, df_demonstracao