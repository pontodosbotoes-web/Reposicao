"""Camada de acesso à Base."""

from pathlib import Path
import pandas as pd
from sqlalchemy import text

from .db import get_engine


_SQL_PATH = Path(__file__).parent.parent / "sql" / "base.sql"
_SQL_BASE = _SQL_PATH.read_text(encoding="utf-8")

_SQL_TRANSITO_PATH = Path(__file__).parent.parent / "sql" / "transf_em_transito.sql"
_SQL_TRANSITO = _SQL_TRANSITO_PATH.read_text(encoding="utf-8") if _SQL_TRANSITO_PATH.exists() else ""

_SQL_RECEBIDAS_PATH = Path(__file__).parent.parent / "sql" / "transf_recebidas_recentes.sql"
_SQL_RECEBIDAS = _SQL_RECEBIDAS_PATH.read_text(encoding="utf-8") if _SQL_RECEBIDAS_PATH.exists() else ""


def _build_produto_filter(produto: str) -> tuple[str, dict]:
    """
    Constrói o filtro SQL do campo Produto.

    Sintaxe aceita:
      - Espaço = E (AND)  →  'CAIXA QUADRADA' acha quem tem AMBAS
      - Vígula , = OU (OR)  →  'CAPA , CAPUZ' acha quem tem UMA ou OUTRA
    """
    if not produto or not produto.strip():
        return "", {}

    or_groups = [g.strip() for g in produto.split(",") if g.strip()]
    if not or_groups:
        return "", {}

    params: dict = {}
    or_clauses: list[str] = []
    idx = 0

    for grupo in or_groups:
        termos = [t for t in grupo.split() if t]
        if not termos:
            continue

        and_clauses = []
        for termo in termos:
            key = f"prod_{idx}"
            params[key] = f"%{termo}%"
            idx += 1
            and_clauses.append(
                f"(CAST(p.CODPRODUTO AS VARCHAR(100)) LIKE :{key}"
                f" OR CAST(p.CodProdutoFabr AS VARCHAR(100)) LIKE :{key}"
                f" OR p.NOMEPRODUTO LIKE :{key}"
                f" OR EXISTS (SELECT 1 FROM CodigoBarras cb WITH (NOLOCK)"
                f"             WHERE cb.IdProduto = p.IdProduto"
                f"               AND (CAST(cb.CodigoBarras AS VARCHAR(100)) LIKE :{key}"
                f"                    OR CAST(cb.GTIN AS VARCHAR(100)) LIKE :{key})))"
            )
        or_clauses.append("(" + " AND ".join(and_clauses) + ")")

    if not or_clauses:
        return "", {}

    return "AND (" + " OR ".join(or_clauses) + ")", params



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
    produto_filter, produto_params = _build_produto_filter(produto)
    sql = _SQL_BASE.replace("/* PRODUTO_FILTER */", produto_filter)

    params = {
        "data_referencia": data_referencia,
        "max_lookback": max_lookback,
        "fabricante": fabricante or "",
        "departamento": departamento or "",
        "grupo": grupo or "",
        "subgrupo": subgrupo or "",
        "filial": filial or "",
        **produto_params,
    }
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    for col in ["VelocidadeAtiva", "VelocidadePeriodo", "DiasAtivo", "DiasInativo",
                "QtdComprada", "QtdRecebida", "QtdEnviada", "QtdVendida",
                "SaldoProvavel", "DiasDesdeCompra"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def carregar_transf_em_transito(
    data_referencia: str,
    dias_transito: int = 10,
) -> pd.DataFrame:
    """Transferências em trânsito: saídas sem entrada ainda."""
    if not _SQL_TRANSITO:
        return pd.DataFrame(columns=["IdProduto", "CodFilialDestino", "QtdEmTransito"])

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


def carregar_transf_recebidas_recentes(
    data_referencia: str,
    dias_reposicao: int = 15,
) -> pd.DataFrame:
    """Transferências recebidas recentemente (anti-gangorra pós-recebimento)."""
    if not _SQL_RECEBIDAS or dias_reposicao <= 0:
        return pd.DataFrame(columns=["IdProduto", "CodFilial", "QtdRecebidaRecente"])

    params = {
        "data_referencia": data_referencia,
        "dias_reposicao": dias_reposicao,
    }
    with get_engine().connect() as conn:
        df = pd.read_sql(text(_SQL_RECEBIDAS), conn, params=params)

    if df.empty:
        return pd.DataFrame(columns=["IdProduto", "CodFilial", "QtdRecebidaRecente"])

    df["QtdRecebidaRecente"] = pd.to_numeric(df["QtdRecebidaRecente"], errors="coerce").fillna(0)
    return df