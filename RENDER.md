# Deploy no Render (Git + Render)

O app pode rodar no **Render** em vez do Streamlit Cloud. O Render usa **Git** (GitHub) e variáveis de ambiente para credenciais.

## 1. Repositório no GitHub

O código já está em: **https://github.com/maelcm/MAPA-SHOW-NACIONAL**

Garanta que o `render.yaml` e as alterações estejam commitados e enviados (`git push`).

## 2. Criar o serviço no Render

1. Acesse **https://dashboard.render.com** e entre na sua conta.
2. **New** → **Web Service**.
3. Conecte o **GitHub** (se ainda não estiver conectado) e escolha o repositório **maelcm/MAPA-SHOW-NACIONAL**.
4. O Render deve detectar o `render.yaml` (Blueprint). Se pedir para criar a partir do Blueprint, confirme.
5. Ou configure manualmente:
   - **Name:** mapa-show-nacional (ou outro nome).
   - **Runtime:** Python.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

## 3. Variável de ambiente (credenciais Google)

O app lê as credenciais do Google da variável **`GCP_SERVICE_ACCOUNT_JSON`**.

1. No Render: abra o seu **Web Service** → **Environment**.
2. **Add Environment Variable**.
3. **Key:** `GCP_SERVICE_ACCOUNT_JSON`
4. **Value:** o conteúdo **inteiro** do seu arquivo `credentials.json` (Google Service Account), em **uma única linha**.
   - Abra o `credentials.json` no seu PC.
   - Copie todo o JSON (incluindo `{` e `}`).
   - Cole no campo Value. Pode ser com quebras de linha ou sem; o app aceita e normaliza a chave privada.

**Exemplo (estrutura):**
```json
{"type":"service_account","project_id":"meu-extrator-465616","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"...","universe_domain":"googleapis.com"}
```

5. Salve. O Render faz redeploy ao salvar variáveis (ou você pode clicar em **Manual Deploy**).

## 4. Link do sistema

Depois do deploy, o link do app aparece no topo do serviço no Render, no formato:

**`https://mapa-show-nacional-xxxx.onrender.com`**

(ou o nome que você deu ao serviço). Use esse link para acessar o sistema no celular ou no PC.

## 5. Atualizações (Git + Render)

- Faça alterações no código e dê **push** para o GitHub (`git push origin main`).
- O Render pode estar configurado para **auto-deploy** em cada push; se não estiver, use **Manual Deploy** no painel do serviço.

## Resumo

| Onde        | O quê |
|------------|--------|
| GitHub     | Código (app.py, render.yaml, requirements.txt, etc.) |
| Render     | Hospedagem do app (Web Service) |
| Render Env | Variável `GCP_SERVICE_ACCOUNT_JSON` = conteúdo do `credentials.json` |
| Link       | URL do serviço no Render (ex.: `https://mapa-show-nacional-xxxx.onrender.com`) |
