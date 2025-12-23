"""
Corrige licenças antigas adicionando campo 'used'
"""
import json

# Carregar banco
with open("license_database.json", 'r', encoding='utf-8') as f:
    db = json.load(f)

# Corrigir cada licença
for lic in db["licenses"]:
    if "used" not in lic:
        lic["used"] = False
        print(f"✅ Corrigido: {lic['key']}")

# Salvar
with open("license_database.json", 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print("\n✅ Banco de dados corrigido!")
print("Agora tente ativar a licença novamente.")
