"""
license_generator.py - GERADOR DE LICENÇAS (PRIVADO - APENAS VENDEDOR)
NÃO ENVIAR ESTE ARQUIVO AO CLIENTE!
"""
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta

# CHAVE MESTRA DE CRIPTOGRAFIA (altere para algo único!)
SECRET_KEY = b"darkblack_bot_master_key_2024_v1"

LICENSE_DB = "licenses.json"

def load_licenses():
    """Carrega banco de dados de licenças"""
    if os.path.exists(LICENSE_DB):
        try:
            with open(LICENSE_DB, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Garantir que tem todas as chaves necessárias
                if "total_sales" not in data:
                    data["total_sales"] = 0
                if "licenses" not in data:
                    data["licenses"] = []
                return data
        except:
            pass
    
    # Retornar estrutura padrão
    return {"licenses": [], "total_sales": 0}

def save_licenses(db):
    """Salva banco de dados de licenças"""
    with open(LICENSE_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def generate_license_key(hwid, customer_name, days_valid=365):
    """
    Gera chave de licença única
    
    Args:
        hwid: Hardware ID do cliente
        customer_name: Nome do cliente
        days_valid: Dias de validade (0 = vitalícia)
    
    Returns:
        str: Chave de licença
    """
    # Data de expiração
    if days_valid > 0:
        expiry = (datetime.now() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
    else:
        expiry = "LIFETIME"
    
    # Dados da licença
    license_data = f"{hwid}|{customer_name}|{expiry}"
    
    # Gerar assinatura HMAC
    signature = hmac.new(
        SECRET_KEY, 
        license_data.encode(), 
        hashlib.sha256
    ).hexdigest()[:16].upper()
    
    # Formato final: HWID-SIGNATURE-EXPIRY
    license_key = f"DBB-{hwid[:8]}-{signature}-{expiry[:10].replace('-', '')}"
    
    return license_key, expiry

def main():
    print("="*70)
    print("   🔑 GERADOR DE LICENÇAS - DARK BLACK BOT")
    print("="*70)
    print()
    
    # Carregar banco de dados
    db = load_licenses()
    
    print(f"📊 Licenças vendidas até agora: {db['total_sales']}")
    print()
    print("-"*70)
    
    # Solicitar informações
    print("NOVA LICENÇA:")
    print()
    customer_name = input("Nome do Cliente: ").strip()
    if not customer_name:
        print("❌ Nome inválido!")
        input("Pressione ENTER para sair...")
        return
    
    hwid = input("Hardware ID do Cliente: ").strip().upper()
    if len(hwid) != 32:
        print("❌ HWID inválido! Deve ter 32 caracteres.")
        input("Pressione ENTER para sair...")
        return
    
    print()
    print("Validade da Licença:")
    print("  1. Vitalícia (sem expiração)")
    print("  2. 30 dias")
    print("  3. 90 dias")
    print("  4. 365 dias (1 ano)")
    print("  5. Personalizado")
    
    choice = input("Escolha (1-5): ").strip()
    
    days_map = {
        "1": 0,
        "2": 30,
        "3": 90,
        "4": 365
    }
    
    if choice in days_map:
        days_valid = days_map[choice]
    elif choice == "5":
        days_valid = int(input("Dias de validade: ").strip())
    else:
        print("❌ Opção inválida!")
        input("Pressione ENTER para sair...")
        return
    
    # Gerar licença
    license_key, expiry = generate_license_key(hwid, customer_name, days_valid)
    
    # Salvar no banco de dados
    license_record = {
        "license_key": license_key,
        "customer_name": customer_name,
        "hwid": hwid,
        "expiry_date": expiry,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"
    }
    
    db["licenses"].append(license_record)
    db["total_sales"] += 1
    save_licenses(db)
    
    # Mostrar resultado
    print()
    print("="*70)
    print("✅ LICENÇA GERADA COM SUCESSO!")
    print("="*70)
    print()
    print(f"Cliente: {customer_name}")
    print(f"HWID: {hwid}")
    print(f"Validade: {expiry}")
    print()
    print("-"*70)
    print(f"CHAVE DE LICENÇA:")
    print()
    print(f"    {license_key}")
    print()
    print("-"*70)
    print()
    print("📋 Copie esta chave e envie ao cliente.")
    print(f"💾 Licença salva em: {LICENSE_DB}")
    print()
    input("Pressione ENTER para sair...")

if __name__ == "__main__":
    main()
