# Ligar o Cursor ao Git (GitHub)

O projeto **já é um repositório Git** com remote **https://github.com/maelcm/MAPA-SHOW-NACIONAL.git**. Para o Cursor usar o Git corretamente:

---

## 1. Abrir a pasta certa no Cursor

1. No Cursor: **File** → **Open Folder** (ou **Arquivo** → **Abrir Pasta**).
2. Escolha exatamente: **c:\Users\Info\MAPA SHOW NACIONAL**
3. Confirme com **Selecionar Pasta** / **Open**.

Assim o Cursor passa a usar o `.git` que está dentro dessa pasta e o painel **Source Control** mostra as alterações.

---

## 2. Usar o Source Control (Git) no Cursor

1. Clique no ícone **Source Control** na barra lateral esquerda (ou **Ctrl+Shift+G**).
2. Você deve ver:
   - **Changes** (arquivos modificados e não rastreados)
   - Caixa de mensagem para **Commit**
   - Botões **Commit**, **Sync**, **...** (mais opções)
3. Para enviar para o GitHub:
   - Marque os arquivos que quer incluir (ou use **Stage All**).
   - Escreva uma mensagem de commit (ex.: "Atualizações").
   - Clique em **Commit**.
   - Depois clique em **Sync** (ou **Push**) para enviar ao **origin/main**.

---

## 3. Se o Cursor não mostrar Git

- **Git instalado:** o Cursor usa o Git do sistema. Instale o Git: https://git-scm.com/download/win e reinicie o Cursor.
- **Conta GitHub no Cursor:** não é obrigatório para commit/push; o push pode pedir login no GitHub (janela do navegador ou credential manager).
- **Repositório em outra pasta:** só a pasta **MAPA SHOW NACIONAL** (onde está o `.git`) deve estar aberta como pasta do workspace para o Git aparecer no Cursor.

---

## 4. Resumo

| O que fazer | Onde |
|-------------|------|
| Abrir a pasta do projeto | **File** → **Open Folder** → `c:\Users\Info\MAPA SHOW NACIONAL` |
| Ver alterações e fazer commit | Barra lateral → **Source Control** (ícone de ramo) ou **Ctrl+Shift+G** |
| Enviar para o GitHub | No Source Control: **Commit** depois **Sync** / **Push** |

O remote **origin** já aponta para **https://github.com/maelcm/MAPA-SHOW-NACIONAL.git**. Depois de abrir a pasta certa no Cursor, o Git e o Cursor ficam interligados.
