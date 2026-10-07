# PB Transferência

Motor de sugestão de transferências entre filiais — DRP + IST + MEIO.

## 🎯 O que faz

Consulta o SQL Server, aplica regras de DRP (Distribution Requirements Planning) 
e IST (Inter-Store Transfers) e sugere o que **enviar** e o que **receber** em cada 
filial, priorizando por velocidade de venda e urgência.

## 🏗️ Arquitetura

```
Streamlit (app.py)
     │
     ▼
src/transferencia.py   ← regras de negócio
     │
     ▼
src/base.py            ← SQL + tipagem
     │
     ▼
src/db.py              ← conexão SQL Server
```

## 🚀 Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Configure `.streamlit/secrets.toml` com suas credenciais (veja `.example`).

## ☁️ Deploy no Streamlit Cloud

1. Suba o repositório no GitHub
2. Acesse https://share.streamlit.io
3. Selecione o repositório e defina `app.py` como main file
4. Em **Settings → Secrets**, configure:

```toml
[sql_server]
server   = "IP_DO_SERVIDOR"
port     = "1433"
database = "NOME_DO_BANCO"
username = "USUARIO_LEITURA"
password = "SENHA"
```

5. Deploy 🚀

## ⚠️ Segurança

- ❌ Nunca versione `.streamlit/secrets.toml` nem `.env`
- ✅ Use apenas usuário de leitura no SQL Server
- ✅ Na nuvem, use **Streamlit Secrets** (nunca hardcode)