"""Credenciais do SQL Server (st.secrets ou .env)."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


def get_db_credentials() -> dict:
    try:
        import streamlit as st
        cred = st.secrets.get("sql_server")
        if cred:
            return {
                "server":   cred["server"],
                "port":     cred.get("port", "1433"),
                "database": cred["database"],
                "username": cred["username"],
                "password": cred["password"],
            }
    except Exception:
        pass

    return {
        "server":   os.getenv("DB_SERVER", "201.76.148.154"),
        "port":     os.getenv("DB_PORT", "1433"),
        "database": os.getenv("DB_DATABASE", "DBcronos"),
        "username": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
    }