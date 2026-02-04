# Fazer o repositório aparecer no Streamlit Cloud

Se **maelcm/MAPA-SHOW-NACIONAL** não aparece na lista de repositórios ao criar um app no Streamlit Cloud, siga estes passos:

---

## 1. Entrar com a conta certa do GitHub

1. Acesse **https://share.streamlit.io**
2. Clique em **Sign in** e faça login com **GitHub**
3. Use a conta do GitHub que **é dona** do repositório (a conta **maelcm**)

Se você criou o repositório em outra conta (ex.: outra pessoa), é preciso que **essa conta** entre no Streamlit Cloud ou que o repositório esteja em uma organização à qual sua conta tenha acesso.

---

## 2. Autorizar o Streamlit a ver o repositório

1. No Streamlit Cloud, vá em **New app**
2. Se a lista de repositórios estiver vazia ou sem **MAPA-SHOW-NACIONAL**, clique em **Configure GitHub** (ou em um link do tipo “Grant access to GitHub” / “Authorize”)
3. No GitHub, na tela de autorização do **Streamlit Cloud**:
   - Marque **All repositories**  
   **ou**
   - Em **Only select repositories**, escolha **MAPA-SHOW-NACIONAL** (ou **maelcm/MAPA-SHOW-NACIONAL**)
4. Confirme (**Authorize** / **Install**)
5. Volte ao Streamlit Cloud e atualize a página ou clique de novo em **New app**

O repositório **maelcm/MAPA-SHOW-NACIONAL** deve passar a aparecer na lista.

---

## 3. Se o repositório é de outra pessoa ou organização

- **Opção A:** A pessoa/org que é dona do repositório entra em **https://share.streamlit.io** com a conta do GitHub dela e cria o app a partir de **maelcm/MAPA-SHOW-NACIONAL**.
- **Opção B:** Você faz um **fork** do repositório para a **sua** conta no GitHub. Depois, no Streamlit Cloud, você entra com a sua conta e cria o app a partir do **seu fork** (ex.: **sua-conta/MAPA-SHOW-NACIONAL**).  
  (Atenção: no fork você precisará configurar os Secrets de novo no Streamlit Cloud.)

---

## 4. Conferir se o repositório existe no GitHub

1. Abra **https://github.com/maelcm/MAPA-SHOW-NACIONAL**
2. Se aparecer 404, o repositório não existe ou é privado e sua conta não tem acesso.
3. Se existir e for **privado**, no Streamlit Cloud use a conta **maelcm** (ou uma conta com acesso) e, na autorização do GitHub, inclua esse repositório (ou “All repositories”).

---

## Resumo

| Situação | O que fazer |
|----------|-------------|
| Repositório não aparece na lista | Entrar no Streamlit com a conta **maelcm** e em **Configure GitHub** autorizar “All repositories” ou só **MAPA-SHOW-NACIONAL** |
| Repo é de outra conta | Essa conta cria o app no Streamlit **ou** você faz fork para sua conta e cria o app a partir do fork |
| Repo privado | Usar no Streamlit a conta GitHub que tem acesso ao repo e autorizar o Streamlit a acessar esse repo |

Não existe “pasta” especial no Streamlit: ele só lista repositórios do GitHub da conta conectada e que foram autorizados na instalação do Streamlit Cloud.
