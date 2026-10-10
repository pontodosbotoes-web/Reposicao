"""Camada de acesso à Base."""

from pathlib import Path
import pandas as pd
from sqlalchemy import text

from .db import get_engine


_SQL_PATH = Path(__file__).parent.parent / "sql" / "base.sql"
_SQL_BASE = _SQL_PATH.read_text(encoding="utf-8")


def carregar_base(
    data_referencia: str,
    max_lookback: int = 365,
    fabricante: str = "",
    departamento: str = "",
    grupo: str = "",
    subgrupo: str = "",
    filial: str = "",
    produto: str = "",
) -> pd.DataFrame:
    params = {
        "data_referencia": data_referencia,
        "max_lookback": max_lookback,
        "fabricante": fabricante or "",
        "departamento": departamento or "",
        "grupo": grupo or "",
        "subgrupo": subgrupo or "",
        "filial": filial or "",
        "produto": produto or "",
    }
    with get_engine().connect() as conn:
        df = pd.read_sql(text(_SQL_BASE), conn, params=params)

    # Tipagem numérica
    for col in ["VelocidadeAtiva", "VelocidadePeriodo", "DiasAtivo", "DiasInativo",
                "QtdComprada", "QtdRecebida", "QtdEnviada", "QtdVendida",
                "SaldoProvavel", "DiasDesdeCompra"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df
    
_SQL_TRANSITO_PATH = Path(__file__).parent.parent / "sql" / "transf_em_transito.sql"
_SQL_TRANSITO = _SQL_TRANSITO_PATH.read_text(encoding="utf-8")


def carregar_transf_em_transito(
    data_referencia: str,
    dias_transito: int = 10,
) -> pd.DataFrame:
    """Retorna transferências em trânsito: IdProduto, CodFilialDestino, QtdEmTransito."""
    params = {
        "data_referencia": data_referencia,
        "dias_transito": dias_transito,
    }
    with get_engine().connect() as conn:
        df = pd.read_sql(text(_SQL_TRANSITO), conn, params=params)

    if df.empty:
        return pd.DataFrame(columns=["IdProduto", "CodFilialDestino", "QtdEmTransito"])

    df["QtdEmTransito"] = pd.to_numeric(df["QtdEmTransito"], errors="coerce").fillna(0)
    return df