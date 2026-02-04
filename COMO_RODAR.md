# Como rodar o sistema — Gestão Festa São Pedro 2026

## Local (no seu PC)

1. Coloque o arquivo **credentials.json** (Google Service Account) na mesma pasta do **app.py**.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode o app:
   ```bash
   streamlit run app.py
   ```
4. Abra no navegador: **http://localhost:8501**

## Streamlit Cloud

1. Envie o projeto para o GitHub (app.py, requirements.txt, credentials não vão no Git).
2. Em [share.streamlit.io](https://share.streamlit.io): **New app** → repositório **maelcm/MAPA-SHOW-NACIONAL**, arquivo **app.py**.
3. Em **Settings → Secrets**, cole o conteúdo do **credentials.json** em formato TOML (veja **SECRETS_STREAMLIT_CLOUD.md**).
4. O link do app aparecerá após o deploy (ex.: https://xxxxx.streamlit.app).

## Render (Django não é mais usado neste projeto)

Se quiser usar o **Render** com **Streamlit**:

1. **Build Command:** `pip install -r requirements.txt`
2. **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
3. **Environment:** variável **GCP_SERVICE_ACCOUNT_JSON** = conteúdo completo do **credentials.json** (uma linha, JSON).

## Resumo

- **Local:** `credentials.json` na pasta + `streamlit run app.py`
- **Streamlit Cloud:** Secrets em TOML (gcp_service_account)
- **Render:** variável **GCP_SERVICE_ACCOUNT_JSON** com o JSON do credentials
