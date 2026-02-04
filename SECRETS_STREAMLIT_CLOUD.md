# Secrets no Streamlit Cloud

O app usa **Google Sheets** e precisa das credenciais do Google (service account). No **Streamlit Cloud** você não usa o arquivo `credentials.json`; em vez disso, cola os dados em formato **TOML** nas Secrets do app.

## Como configurar

1. Abra o painel do seu app no [Streamlit Cloud](https://share.streamlit.io).
2. Vá em **Settings** → **Secrets**.
3. Cole o conteúdo em **formato TOML** (veja exemplo abaixo).
4. Salve. As mudanças levam cerca de **1 minuto** para propagar.

## Formato TOML (exemplo)

O app espera uma chave `gcp_service_account` com os mesmos campos do `credentials.json`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "SEU_PROJECT_ID"
private_key_id = "SEU_PRIVATE_KEY_ID"
private_key = """
-----BEGIN PRIVATE KEY-----
COLE_AQUI_TODAS_AS_LINHAS_DA_CHAVE_PRIVADA_DO_credentials.json
-----END PRIVATE KEY-----
"""
client_email = "sua-conta@seu-projeto.iam.gserviceaccount.com"
client_id = "SEU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

## Como obter o TOML a partir do credentials.json

- Copie cada campo do `credentials.json` para o TOML.
- A **private_key** deve ficar entre `"""` (três aspas), com as quebras de linha preservadas.
- O nome da seção **tem que ser** `[gcp_service_account]` — é isso que o `app.py` usa em `st.secrets["gcp_service_account"]`.

## Segurança

- **Nunca** commite o arquivo de secrets com dados reais no Git.
- Use apenas o painel do Streamlit Cloud para colar as credenciais; elas ficam criptografadas no lado deles.
