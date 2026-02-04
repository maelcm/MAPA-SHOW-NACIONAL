# Django + Render — Passo a passo

O projeto tem **duas formas** de rodar no Render:

1. **Django** (este guia) — use **requirements-django.txt** e **gunicorn**
2. **Streamlit** — use **requirements.txt** e **streamlit run app.py**

Para usar **Django** no Render:

## No painel do Render (New Web Service)

1. **Build Command:**  
   `pip install -r requirements-django.txt && python manage.py collectstatic --noinput`

2. **Start Command:**  
   `gunicorn config.wsgi --bind 0.0.0.0:$PORT`

3. **Variável de ambiente:**  
   - Key: `GCP_SERVICE_ACCOUNT_JSON`  
   - Value: conteúdo completo do **credentials.json** (uma linha ou com quebras)

4. (Opcional) **DJANGO_SECRET_KEY:**  
   Pode deixar o Render gerar ou definir um valor secreto.

## Rodar Django localmente

```bash
pip install -r requirements-django.txt
python manage.py collectstatic --noinput
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

## Estrutura do projeto (Django)

- **config/** — settings, urls, wsgi
- **mesas/** — app (views, services Google Sheets, templates, static)
- **manage.py** — comando Django
- **requirements-django.txt** — dependências para Render (Django + gunicorn + whitenoise + gspread)

O mesmo Google Sheets (Layout_Mesas, RESERVAS) é usado; a lógica é a mesma do app Streamlit.
