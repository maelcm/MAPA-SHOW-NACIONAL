import json

# Lê o seu arquivo json original
try:
    with open('credentials.json', 'r') as f:
        data = json.load(f)

    print("\n--- COPIE O TEXTO ABAIXO PARA O SITE DO STREAMLIT ---\n")
    print("[gcp_service_account]")
    for key, value in data.items():
        # Corrige quebras de linha na chave privada
        valor_limpo = value.replace('\n', '\\n') 
        print(f'{key} = "{valor_limpo}"')
    print("\n-----------------------------------------------------\n")

except Exception as e:
    print("Erro: Seu arquivo credentials.json ainda está inválido ou não foi encontrado.")
    print(f"Detalhe: {e}")