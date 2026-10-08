"""Conexão SQL Server + listas para dropdowns (via python-tds)."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

from .config import get_db_credentials


@st.cache_resource
def get_engine():
    cred = get_db_credentials()
    url = (
        f"mssql+pymssql://{cred['username']}:{cred['password']}"
        f"@{cred['server']}:{cred['port']}/{cred['database']}"
    )
    return create_engine(url, pool_pre_ping=True)


def testar_conexao() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False


@st.cache_data(ttl=3600)
def carregar_filiais() -> dict:
    return {
        "ALECRIM": "1",
        "VIA DIRETA": "2",
        "ZONA SUL": "3",
        "ZONA NORTE": "4",
        "ATACADO": "5",
    }


@st.cache_data(ttl=3600)
def carregar_fabricantes() -> dict:
    engine = get_engine()
    q = """
        SELECT CAST(CODFABR AS VARCHAR(20)) AS Codigo, NOMEFABR AS Nome
        FROM Fabricantes WITH (NOLOCK)
        WHERE NOMEFABR IS NOT NULL
          AND LTRIM(RTRIM(NOMEFABR)) <> ''
        ORDER BY NOMEFABR
    """
    df = pd.read_sql(q, engine)
    return {f"{r.Codigo} - {r.Nome}": r.Codigo for r in df.itertuples()}


@st.cache_data(ttl=3600)
def carregar_departamentos() -> dict:
    engine = get_engine()
    q = """
        SELECT DISTINCT LEFT(CodGrupo, 2) AS Codigo, NomeGrupo AS Nome
        FROM Grupos WITH (NOLOCK)
        WHERE LEN(CodGrupo) = 2
          AND LEFT(CodGrupo, 2) NOT IN ('09','10')
        ORDER BY NomeGrupo
    """
    df = pd.read_sql(q, engine)
    return {f"{r.Codigo} - {r.Nome}": r.Codigo for r in df.itertuples()}


@st.cache_data(ttl=3600)
def carregar_grupos() -> dict:
    engine = get_engine()
    q = """
        SELECT DISTINCT LEFT(CodGrupo, 5) AS Codigo, NomeGrupo AS Nome
        FROM Grupos WITH (NOLOCK)
        WHERE LEN(CodGrupo) = 5
          AND LEFT(CodGrupo, 2) NOT IN ('09','10')
        ORDER BY NomeGrupo
    """
    df = pd.read_sql(q, engine)
    return {f"{r.Codigo} - {r.Nome}": r.Codigo for r in df.itertuples()}


@st.cache_data(ttl=3600)
def carregar_subgrupos() -> dict:
    engine = get_engine()
    q = """
        SELECT DISTINCT CodGrupo AS Codigo, NomeGrupo AS Nome
        FROM Grupos WITH (NOLOCK)
        WHERE LEN(CodGrupo) = 9
          AND LEFT(CodGrupo, 2) NOT IN ('09','10')
        ORDER BY NomeGrupo
    """
    df = pd.read_sql(q, engine)
    return {f"{r.Codigo} - {r.Nome}": r.Codigo for r in df.itertuples()}