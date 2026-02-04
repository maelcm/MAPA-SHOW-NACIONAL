# Passo a passo: Deploy no Render (Git + repositório GitHub)

## Parte 1 — Conectar o repositório e criar o Web Service

### Passo 1 — Abrir o painel do Render
1. Abra o navegador.
2. Acesse: **https://dashboard.render.com**
3. Faça **login** (ou crie uma conta com e-mail ou GitHub).

---

### Passo 2 — Iniciar a criação de um Web Service
1. No canto superior direito, clique no botão **"New +"** (ou **"New"**).
2. No menu que abrir, clique em **"Web Service"**.

---

### Passo 3 — Conectar o GitHub (se ainda não estiver conectado)
1. Na tela de criação do Web Service, o Render pede para escolher um **repositório**.
2. Se aparecer **"Connect a repository"** ou **"Connect account"**:
   - Clique em **"Connect GitHub"** (ou **"Connect account"**).
   - Autorize o Render a acessar sua conta do GitHub.
   - Se pedir, escolha **"All repositories"** ou marque o repositório **MAPA-SHOW-NACIONAL**.
   - Conclua a conexão.
3. Volte à tela de criação do Web Service (ou clique de novo em **New +** → **Web Service**).

---

### Passo 4 — Escolher o repositório maelcm/MAPA-SHOW-NACIONAL
1. Na lista de repositórios, procure por **"MAPA-SHOW-NACIONAL"** (ou **"maelcm/MAPA-SHOW-NACIONAL"**).
2. Clique em **"Connect"** (ou no nome do repositório) ao lado de **MAPA-SHOW-NACIONAL**.
3. Se o repositório não aparecer:
   - Confirme que você está logado no GitHub com a conta que tem acesso ao repositório **maelcm/MAPA-SHOW-NACIONAL**.
   - No Render, em **Account Settings** ou **Dashboard**, verifique se o GitHub está conectado e se o repositório está na lista; se não estiver, conecte de novo e autorize o repositório.

---

### Passo 5 — Configurar o serviço (Django no Render)
1. **Name:** pode deixar **mapa-show-nacional** (ou o nome que o Render sugerir).
2. **Region:** escolha a mais próxima (ex.: Oregon, Frankfurt).
3. **Branch:** deixe **main** (ou a branch onde está o código).
4. **Runtime:** **Python**.
5. **Build Command:**  
   `pip install -r requirements-django.txt && python manage.py collectstatic --noinput`
6. **Start Command:**  
   `gunicorn config.wsgi`
7. Se o Render detectar o **render.yaml** (Blueprint), ele pode preencher isso automaticamente — nesse caso, confira os comandos acima.

---

### Passo 6 — Variável de ambiente (credenciais do Google)
1. Role até a seção **"Environment"** ou **"Environment Variables"**.
2. Clique em **"Add Environment Variable"** (ou **"Add variable"**).
3. **Key:** digite exatamente:  
   `GCP_SERVICE_ACCOUNT_JSON`
4. **Value:**  
   - Abra o arquivo **credentials.json** do projeto (no seu PC).
   - Selecione **todo** o conteúdo (Ctrl+A).
   - Copie (Ctrl+C).
   - Cole no campo **Value** do Render (Ctrl+V).  
   Pode ser em uma linha ou com quebras de linha; o app aceita os dois.
5. Clique em **"Save"** ou **"Add"** na variável.

---

### Passo 7 — Criar o Web Service
1. Role até o final da página.
2. Clique em **"Create Web Service"** (ou **"Deploy"**).
3. O Render vai fazer o **build** e o **deploy**; isso pode levar alguns minutos.

---

### Passo 8 — Pegar o link do sistema
1. Quando o deploy terminar, no topo da página do serviço aparece a **URL** do app.
2. O formato é algo como:  
   **https://mapa-show-nacional-xxxx.onrender.com**
3. Esse é o **link para entrar no sistema** — use no celular ou no PC.

---

## Resumo rápido

| Passo | O que fazer |
|-------|------------------|
| 1 | Abrir https://dashboard.render.com e fazer login |
| 2 | Clicar em **New +** → **Web Service** |
| 3 | Conectar o GitHub (se pedir) e autorizar o repositório |
| 4 | Escolher o repositório **maelcm/MAPA-SHOW-NACIONAL** e clicar em Connect |
| 5 | Conferir Build Command e Start Command (ou usar o que vier do render.yaml) |
| 6 | Adicionar variável **GCP_SERVICE_ACCOUNT_JSON** com o conteúdo do credentials.json |
| 7 | Clicar em **Create Web Service** |
| 8 | Copiar a URL do app (ex.: https://mapa-show-nacional-xxxx.onrender.com) |

---

## Problemas comuns

- **Repositório não aparece:** Conecte de novo o GitHub em **Account Settings** e autorize o repositório **MAPA-SHOW-NACIONAL**.
- **Build falha:** Confira se no GitHub existem os arquivos **requirements.txt** e **app.py** na raiz do repositório.
- **Erro de conexão com o Google:** Confira se a variável **GCP_SERVICE_ACCOUNT_JSON** foi colada por completo (todo o JSON do credentials.json).
