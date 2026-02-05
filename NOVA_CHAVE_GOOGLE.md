# Como criar uma nova chave no Google Cloud (Invalid JWT Signature)

Quando aparece **Invalid JWT Signature**, a chave da conta de serviço não é mais válida. Siga estes passos para criar uma nova.

## Passo a passo

1. **Abra o Google Cloud Console**  
   https://console.cloud.google.com/iam-admin/serviceaccounts

2. **Selecione o projeto**  
   No topo da página, escolha o projeto (ex.: **meu-extrator-465616**).

3. **Abra a conta de serviço**  
   Na lista, clique no **e-mail** da conta (ex.: `finbot-service@meu-extrator-465616.iam.gserviceaccount.com`).

4. **Vá na aba Keys (Chaves)**  
   No menu da conta de serviço, clique em **KEYS** / **Chaves**.

5. **Criar nova chave**  
   - Clique em **ADD KEY** / **Adicionar chave**  
   - Escolha **Create new key** / **Criar nova chave**  
   - Marque **JSON**  
   - Clique em **Create** / **Criar**

6. **Salvar o arquivo**  
   O navegador vai baixar um arquivo JSON.  
   - **Renomeie** esse arquivo para **credentials.json**  
   - **Mova** (ou copie) para a pasta do projeto **MAPA SHOW NACIONAL** (mesma pasta do `run_terminal.py`)  
   - **Substitua** o arquivo **credentials.json** antigo que está lá

7. **No terminal, na pasta do projeto:**

   ```powershell
   python gerar_json_credenciais.py
   python run_terminal.py
   ```

Depois disso o sistema deve conectar normalmente.
