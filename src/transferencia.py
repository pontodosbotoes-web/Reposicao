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
    df["Excesso"] = np.maximum(0, df["SaldoAjustado"] - df["EstoqueIdeal"])
    df["Falta"] = np.maximum(0, df["EstoqueIdeal"] - df["SaldoAjustado"])

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


def excluir_descontinuados(df: pd.DataFrame) -> pd.DataFrame:
    vel_max = df.groupby("IdProduto")["VelocidadeAtiva"].transform("max")
    saldo_max = df.groupby("IdProduto")["SaldoAjustado"].transform("max")
    return df[(vel_max >= 0.1) | (saldo_max > 0)].copy()


def alocar_produto(df_produto: pd.DataFrame, piso_exposicao: int = 0, atacado_tem_minimo_compra: bool = False) -> tuple[list[dict], list[dict]]:
    vel_max = df_produto["VelocidadePeriodo"].max()

    if vel_max == 0:
        alocacoes = []
        doadoras = df_produto[(df_produto["CodigoFilial"] != 5) & (df_produto["SaldoAjustado"] > 0)]
        for _, doa in doadoras.iterrows():
            qtd = int(doa["SaldoAjustado"])
            if qtd >= 5:
                alocacoes.append({
                    "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                    "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                    "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                    "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                    "CodigoFilialDestino": 0, "NomeFilialDestino": "LIQUIDAR",
                    "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                    "DiasAteZerarDestino": None, "Motivo": "ESTOQUE PARADO",
                    "SaldoAjustado": int(doa["SaldoAjustado"]),
                    "QtdEmTransito": 0
                })
        return alocacoes, []

    elif vel_max < 0.1:
        alocacoes = []
        doadoras = df_produto[(df_produto["CodigoFilial"] != 5) & (df_produto["SaldoAjustado"] > 0)]
        for _, doa in doadoras.iterrows():
            qtd = int(doa["SaldoAjustado"])
            if qtd >= 5:
                alocacoes.append({
                    "Prioridade": 3, "CodigoProduto": doa["CodigoProduto"],
                    "ReferenciaFabricante": doa["ReferenciaFabricante"], "Produto": doa["Produto"],
                    "Fabricante": doa["Fabricante"], "Embalagem": doa["Embalagem"],
                    "CodigoFilialOrigem": int(doa["CodigoFilial"]), "NomeFilialOrigem": doa["Filial"],
                    "CodigoFilialDestino": 0, "NomeFilialDestino": "DESCONTINUAR",
                    "QtdTransferir": qtd, "ReservaOrigem": 0, "IdealOrigem": 0, "IdealDestino": 0,
                    "DiasAteZerarDestino": None, "Motivo": "FIM DE CICLO",
                    "SaldoAjustado": int(doa["SaldoAjustado"]),
                    "QtdEmTransito": 0
                })
        return alocacoes, []

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

            # --- NOVA LÓGICA DE MOTIVO (PRIORIZA O TRÂNSITO) ---
            if rec["QtdEmTransito"] > 0:
                motivo = "AGUARDANDO TRANSFERENCIA"
            elif rec["SaldoAjustado"] <= 0: 
                motivo = "SEM ESTOQUE"
            elif rec["QtdRecebidaRecente"] > 0: 
                motivo = f"RECEBIDO RECENTEMENTE ({int(rec['QtdRecebidaRecente'])} un)"
            elif pd.notna(rec["DiasAteZerar"]) and rec["DiasAteZerar"] < 7: 
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
            })

            excesso_livre[cod_doador] -= qtd
            precisa -= qtd
            qtd_recebida_transf += qtd

        necessidade_ideal = rec["EstoqueIdeal"] - qtd_recebida_transf
        
        if necessidade_ideal > 0:
            minimo = piso_exposicao if atacado_tem_minimo_compra else 1
            if necessidade_ideal >= minimo:
                if qtd_recebida_transf == 0 and rec["SaldoAjustado"] <= 0:
                    motivo_compra = "SEM ESTOQUE"
                else:
                    motivo_compra = "ESTOQUE COMPLEMENTAR"
                
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
                    "Ideal": rec["EstoqueIdeal"]
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
                    "Ideal": atacado.iloc[0]["EstoqueIdeal"]
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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df_base.copy()

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

    df = calcular_indicadores(df, cobertura_alvo, lead_time, piso_exposicao, reserva_pct, atacado_tem_piso, atacado_tem_reserva)
    df = filtrar_recentes(df, df_recebidas_recentes)
    df = excluir_descontinuados(df)

    todas_transf = []
    todas_compras = []

    for _, grupo in df.groupby("IdProduto"):
        t, c = alocar_produto(grupo, piso_exposicao, atacado_tem_minimo_compra)
        todas_transf.extend(t)
        todas_compras.extend(c)

    df_transf = pd.DataFrame(todas_transf)
    if not df_transf.empty:
        df_transf = df_transf.sort_values(["Prioridade", "NomeFilialDestino", "Produto", "Fabricante"]).reset_index(drop=True)

    df_compras = pd.DataFrame(todas_compras)
    if not df_compras.empty:
        df_compras = df_compras.sort_values(["NomeFilialDestino", "Produto"]).reset_index(drop=True)

    return df_transf, df_compras