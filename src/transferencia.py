"""Regras de transferência (DRP + IST + MEIO)."""

import pandas as pd
import numpy as np


MATRIZ_PROXIMIDADE = {
    1: [5, 2, 3, 4],
    2: [5, 3],
    3: [5, 2],
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
    df["Falta"] = np.maximum(0, df["EstoqueIdeal"] - df["SaldoProvavel"])

    df["PercReserva"] = df["CodigoFilial"].apply(_reserva)
    df["ReservaOrigem"] = np.ceil(df["Excesso"] * df["PercReserva"] / 100).astype(int)

    df["ExcessoTransferivel"] = np.maximum(0, df["Excesso"] - df["ReservaOrigem"])
    df["DiasAteZerar"] = np.where(
        (df["VelocidadeAtiva"] > 0) & (df["SaldoProvavel"] > 0),
        df["SaldoProvavel"] / df["VelocidadeAtiva"],
        np.where(df["SaldoProvavel"] <= 0, 0, np.nan),
    )
    df["QtdRecebidaRecente"] = 0

    return df


def filtrar_recentes(df: pd.DataFrame, df_recentes: pd.DataFrame | None) -> pd.DataFrame:
    if df_recentes is None or df_recentes.empty:
        df["QtdRecebidaRecente"] = 0
        return df
    chave = df["IdProduto"].astype(str) + "-" + df["CodigoFilial"].astype(str)
    chave_rec = df_recentes["IdProduto"].astype(str) + "-" + df_recentes["CodFilial"].astype(str)
    mapa = dict(zip(chave_rec, df_recentes["QtdRecebidaRecente"]))
    df["QtdRecebidaRecente"] = chave.map(mapa).fillna(0)
    return df


def excluir_descontinuados(df: pd.DataFrame) -> pd.DataFrame:
    vel_max = df.groupby("IdProduto")["VelocidadeAtiva"].transform("max")
    return df[vel_max >= 0.1].copy()


def alocar_produto(df_produto: pd.DataFrame) -> list[dict]:
    receptoras = df_produto[df_produto["Falta"] >= 5].copy()
    receptoras = receptoras[receptoras["QtdRecebidaRecente"] < receptoras["Falta"]]
    receptoras = receptoras.sort_values(
        ["VelocidadePeriodo", "VelocidadeAtiva", "DiasInativo"],
        ascending=[False, False, True],
    )

    doadoras = df_produto[df_produto["ExcessoTransferivel"] >= 5].copy()
    doadoras = doadoras.sort_values(
        ["VelocidadePeriodo", "VelocidadeAtiva"],
        ascending=[True, True],
    )

    if receptoras.empty or doadoras.empty:
        return []

    excesso_livre = dict(zip(doadoras["CodigoFilial"], doadoras["ExcessoTransferivel"]))
    alocacoes = []

    for _, rec in receptoras.iterrows():
        precisa = rec["Falta"]
        ordem = MATRIZ_PROXIMIDADE.get(rec["CodigoFilial"], [])

        for cod_doador in ordem:
            if precisa < 5:
                break
            if excesso_livre.get(cod_doador, 0) < 5:
                continue

            doa = doadoras[doadoras["CodigoFilial"] == cod_doador].iloc[0]
            qtd = int(min(excesso_livre[cod_doador], precisa))
            if qtd < 5:
                break

            if rec["SaldoProvavel"] <= 0:
                motivo = "SEM ESTOQUE"
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

            if pd.isna(rec["DiasAteZerar"]):
                prio = 3
            elif rec["DiasAteZerar"] < 7:
                prio = 1
            elif rec["DiasAteZerar"] < 15:
                prio = 2
            else:
                prio = 3

            alocacoes.append({
                "Prioridade": prio,
                "CodigoProduto": rec["CodigoProduto"],
                "ReferenciaFabricante": rec["ReferenciaFabricante"],
                "Produto": rec["Produto"],
                "Fabricante": rec["Fabricante"],
                "Embalagem": rec["Embalagem"],
                "CodigoFilialOrigem": int(doa["CodigoFilial"]),
                "NomeFilialOrigem": doa["Filial"],
                "CodigoFilialDestino": int(rec["CodigoFilial"]),
                "NomeFilialDestino": rec["Filial"],
                "QtdTransferir": qtd,
                "ReservaOrigem": int(doa["ReservaOrigem"]),
                "IdealOrigem": int(doa["EstoqueIdeal"]),
                "IdealDestino": int(rec["EstoqueIdeal"]),
                "DiasAteZerarDestino": round(rec["DiasAteZerar"], 1) if pd.notna(rec["DiasAteZerar"]) else None,
                "Motivo": motivo,
            })

            excesso_livre[cod_doador] -= qtd
            precisa -= qtd

    return alocacoes


def gerar_sugestoes(
    df_base: pd.DataFrame,
    cobertura_alvo: int = 30,
    lead_time: int = 10,
    piso_exposicao: int = 0,
    reserva_pct: float = 25,
    atacado_tem_piso: bool = False,
    atacado_tem_reserva: bool = False,
) -> pd.DataFrame:
    df = calcular_indicadores(
        df_base,
        cobertura_alvo=cobertura_alvo,
        lead_time=lead_time,
        piso_exposicao=piso_exposicao,
        reserva_pct=reserva_pct,
        atacado_tem_piso=atacado_tem_piso,
        atacado_tem_reserva=atacado_tem_reserva,
    )
    df = excluir_descontinuados(df)

    todas = []
    for _, grupo in df.groupby("IdProduto"):
        todas.extend(alocar_produto(grupo))

    if not todas:
        return pd.DataFrame()

    resultado = pd.DataFrame(todas)
    return resultado.sort_values(
        ["Prioridade", "NomeFilialDestino", "Produto", "Fabricante"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)