# Como rodar o sistema — Gestão Festa São Pedro 2026

## Uso pelo terminal

Para usar **no terminal** do seu PC:

1. Coloque o **credentials.json** (Google Service Account) na pasta do projeto (mesma pasta do **run_terminal.py**).
2. Instale as dependências (só uma vez):
   ```bash
   pip install -r requirements.txt
   ```
3. Rode:
   ```bash
   python run_terminal.py
   ```
4. Use o menu: ver mapa, extrato, fazer reserva, marcar vendido, cancelar reserva, sair.

O terminal usa o **credentials.json** da pasta; se existir **gcp_credenciais.txt** (gerado por `python gerar_json_credenciais.py`), ele é usado antes.

### Se der "Invalid JWT Signature" no terminal

A chave da conta de serviço pode estar **revogada**. Faça o seguinte:

1. No [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts) → sua conta de serviço → **Keys** → **Add Key** → **Create new key** → **JSON**. Baixe o arquivo.
2. Substitua o **credentials.json** na pasta do projeto pelo arquivo baixado (renomeie para `credentials.json`).
3. Rode `python gerar_json_credenciais.py` (isso cria/atualiza o **gcp_credenciais.txt**).
4. Rode de novo `python run_terminal.py`.

---

## Local com navegador (Streamlit)

1. Coloque o arquivo **credentials.json** na mesma pasta do **app.py**.
2. Instale as dependências: `pip install -r requirements.txt`
3. Rode: `streamlit run app.py`
4. Abra no navegador: **http://localhost:8501**

### Se der "Invalid JWT Signature" no Streamlit local

Rode `python gerar_json_credenciais.py` (gera **gcp_credenciais.txt**). Depois rode de novo `streamlit run app.py`. Ou baixe uma nova chave no [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts) → sua conta → Keys → Add Key → JSON e substitua o **credentials.json**.

## Streamlit Cloud

1. Envie o projeto para o GitHub (app.py, requirements.txt, credentials não vão no Git).
2. Em [share.streamlit.io](https://share.streamlit.io): **New app** → repositório **maelcm/MAPA-SHOW-NACIONAL**, arquivo **app.py**.
3. Em **Settings → Secrets**, cole o conteúdo do **credentials.json** em formato TOML (veja **SECRETS_STREAMLIT_CLOUD.md**).
4. O link do app aparecerá após o deploy (ex.: https://xxxxx.streamlit.app).

## Resumo

- **Terminal:** `credentials.json` na pasta + `python run_terminal.py`
- **Navegador local:** `streamlit run app.py` → http://localhost:8501
- **Streamlit Cloud:** Secrets em TOML (veja SECRETS_STREAMLIT_CLOUD.md)
