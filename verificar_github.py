import requests
import json
import os

URL = "https://raw.githubusercontent.com/juniorbatistamlk-stack/updates-bot/main/license_database.json"

print("🔍 VERIFICANDO O QUE ESTÁ NO GITHUB...")
print(f"Link: {URL}")
print("-" * 50)

try:
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Arquivo encontrado no GitHub!")
        print(f"Total de licenças lá: {len(data['licenses'])}")
        print("\n📋 LISTA DE CHAVES NO GITHUB:")
        github_keys = []
        for lic in data['licenses']:
            print(f" - {lic['key']} ({lic['name']})")
            github_keys.append(lic['key'])
            
        print("-" * 50)
        
        # Agora verifica a chave que o usuário tentou
        chave_tentada = "DBB-C71C-6ED1-BB0D" # A do print
        
        if chave_tentada in github_keys:
            print(f"✅ A chave {chave_tentada} ESTÁ no GitHub.")
            print("Se o bot diz inválida, pode ser problema de cache ou HWID.")
        else:
            print(f"❌ A chave {chave_tentada} NÃO ESTÁ no GitHub!")
            print("⚠️ MOTIVO DO ERRO: Você criou a chave no PC mas não subiu para o site.")
            print("👉 SOLUÇÃO: Faça upload do arquivo 'license_database.json' para o GitHub.")
            
    else:
        print(f"❌ Erro ao acessar GitHub: {response.status_code}")
        print("O arquivo pode não existir lá ainda.")

except Exception as e:
    print(f"Erro: {e}")

input("\nPressione ENTER para sair...")
