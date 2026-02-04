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
- A **private_key** deve ficar entre `"""` (três aspas), **com quebras de linha reais** (cada linha da chave em uma linha no Secrets). Não cole a chave em uma única linha com `\n`; use Enter para quebrar as linhas.
- O nome da seção **tem que ser** `[gcp_service_account]`.

## Erro "Unable to load PEM file" / InvalidByte(128, 46)

Esse erro costuma vir de **caractere inválido** na chave ao colar nos Secrets. Duas formas de evitar:

### Opção A — Usar só o base64 (recomendado para evitar erro)

Em vez de colar a chave PEM inteira, use o campo **`private_key_base64`**: cole **apenas o conteúdo base64** (todas as linhas entre `-----BEGIN...` e `-----END...` **juntas, em uma única linha**, sem espaços nem quebras).

1. No `credentials.json`, abra o campo `"private_key"`.
2. Apague as linhas `-----BEGIN PRIVATE KEY-----` e `-----END PRIVATE KEY-----`.
3. Junte todas as linhas do meio em uma só (copie e cole em um editor, apague os Enter, ou use substituir `\n` por nada).
4. Nos Secrets do Streamlit, adicione:

```toml
[gcp_service_account]
type = "service_account"
project_id = "meu-extrator-465616"
private_key_id = "277f30603e5f16b80fe72c3d439f845b9604dde8"
private_key_base64 = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCiXX20Xv+69pcwd+WQM4gUaDoz224kBFWNc+Nkx2zgjPvEoXP6b8e0pjsjN2Nx4e5L6EvLP5AxLnSj..."
# ... client_email, client_id, etc. (sem private_key)
client_email = "finbot-service@meu-extrator-465616.iam.gserviceaccount.com"
# ...
```

O app monta o PEM a partir desse valor; assim você não cola a chave com quebras de linha e evita InvalidByte.

### Opção B — Colar a chave PEM inteira

Use `private_key` entre `"""` com **quebras de linha reais** (cada linha da chave em uma linha). Copie de novo do `credentials.json` para não levar aspas curvas ou espaços a mais. O app tenta corrigir `\n` literal e remove caracteres inválidos; se ainda der erro, use a Opção A.

## Erro "Invalid JWT Signature" / invalid_grant

Esse erro aparece quando a **chave privada** está corrompida ao colar (por exemplo no Render na variável **GCP_SERVICE_ACCOUNT_JSON**, ou nos Secrets do Streamlit). O painel do Render/Streamlit às vezes altera ou trunca o JSON.

**Solução:** use **private_key_base64** em vez de `private_key`:

1. No `credentials.json`, no campo `"private_key"`, apague as linhas `-----BEGIN PRIVATE KEY-----` e `-----END PRIVATE KEY-----`.
2. Junte todo o conteúdo do meio em **uma única linha** (sem espaços nem Enter).
3. No JSON que você cola no Render (ou no TOML do Streamlit), **remova** o campo `private_key` e **adicione** `"private_key_base64": "COLE_AQUI_A_LINHA_BASE64"` (no JSON use aspas duplas).

O app reconstrói o PEM a partir do base64 e evita corrupção ao colar.

## Erro "No secrets found" no Render

Se no Render aparecer algo como: *"No secrets found. Valid paths for a secrets.toml file..."*, é porque o Streamlit procura um arquivo `secrets.toml` ao iniciar. No repositório existe a pasta `.streamlit/` com um `secrets.toml` **vazio** (só comentários). Assim o Streamlit encontra o arquivo e não exibe esse erro. No Render as credenciais vêm da variável de ambiente **GCP_SERVICE_ACCOUNT_JSON** (Settings → Environment), não desse arquivo.

## Segurança

- **Nunca** commite o arquivo de secrets com dados reais no Git.
- Use apenas o painel do Streamlit Cloud para colar as credenciais; elas ficam criptografadas no lado deles.
