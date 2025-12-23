"""
utils/license_system.py - SISTEMA DE VALIDAÇÃO ONLINE VIA GITHUB v2.0
"""
import os
import json
import requests
import hashlib
from datetime import datetime, timedelta
import platform
import subprocess

# URL DO SEU ARQUIVO SITE (ALTERE ISTO DEPOIS!)
# Por enquanto usaremos o mesmo repositório de updates
LICENSE_DB_URL = "https://raw.githubusercontent.com/juniorbatistamlk-stack/updates-bot/main/license_database.json"

LICENSE_FILE = ".license"
SUPPORT_CONTACT = "https://t.me/magoTrader_01"

class LicenseSystem:
    def __init__(self):
        self.device_id = self.get_hwid()
        self.license_data = None
        
    def get_hwid(self):
        """Gera ID único do hardware"""
        try:
            if platform.system() == "Windows":
                cmd = "wmic csproduct get uuid"
                uuid = subprocess.check_output(cmd).decode().split('\n')[1].strip()
                return hashlib.sha256(uuid.encode()).hexdigest()[:32]
            else:
                return "LINUX_UNSUPPORTED"
        except:
            # Fallback para nome do PC
            return hashlib.sha256(platform.node().encode()).hexdigest()[:32]

    def check_license(self):
        """
        Verifica licença completa (Online + Local)
        Retorna: (is_valid, message, days_left)
        """
        # 1. Tenta carregar licença salva localmente
        local_data = self.load_local()
        
        if not local_data:
            print("\n📋 Nenhuma licença encontrada neste computador.")
            return self.request_activation()
            
        # 2. Verifica se a licença salva é para este PC
        if local_data.get("hwid") != self.device_id:
            print("\n❌ Esta licença pertence a outro computador!")
            # Apaga licença inválida
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
            return self.request_activation()
            
        # 3. Verifica expiração
        expiry_date = datetime.fromisoformat(local_data["expiry_date"])
        days_left = (expiry_date - datetime.now()).days
        
        # Lógica de Avisos
        if days_left < 0:
            print("\n❌ SEU ACESSO EXPIROU!")
            print(f"Sua licença venceu em: {expiry_date.strftime('%d/%m/%Y')}")
            print(f"💬 Para continuar faturando, renove agora: {SUPPORT_CONTACT}")
            input("\nPressione ENTER para sair...")
            return False
            
        if days_left <= 3:
            print("\n⚠️ AVISO DE VENCIMENTO ⚠️")
            print(f"Seu acesso vence em {days_left} dias!")
            print(f"💬 Evite bloqueios, chame o suporte para renovar: {SUPPORT_CONTACT}")
            print("="*60)
            
        print(f"\n✅ Licença Ativa! Dias restantes: {days_left}")
        return True

    def request_activation(self):
        """Solicita chave ao usuário e valida online"""
        print("\n" + "="*60)
        print("🔐 ATIVAÇÃO - DARK BLACK BOT PRO")
        print("="*60)
        print(f"Seu ID de Hardware: {self.device_id}")
        print("\nInsira sua chave de licença para ativar.")
        print("💬 Adquira em: " + SUPPORT_CONTACT)
        print("-" * 60)
        
        while True:
            key = input("\n🔑 Chave: ").strip()
            
            if not key:
                continue
                
            print("⏳ Verificando no servidor...")
            valid, msg, data = self.validate_online(key)
            
            if valid:
                print(f"\n✅ {msg}")
                self.save_local(data)
                return True
            else:
                print(f"\n❌ {msg}")
                retry = input("Tentar novamente? (S/N): ").upper()
                if retry != 'S':
                    return False

    def validate_online(self, key):
        """Baixa banco de dados do GitHub e valida chave"""
        try:
            response = requests.get(LICENSE_DB_URL)
            if response.status_code != 200:
                # Se não conseguir acessar internet/github
                return False, "Erro de conexão com servidor de licenças", None
                
            db = response.json()
            
            found_license = None
            for lic in db["licenses"]:
                if lic["key"] == key:
                    found_license = lic
                    break
            
            if not found_license:
                return False, "Chave inválida ou não encontrada!", None
                
            # Verifica se já está vinculada a OUTRO pc (se tiver o campo hwid no banco online)
            # Nota: O banco online geralmente não tem HWID a menos que você atualize ele
            # Mas podemos implementar verificação de "usada" aqui se quiser
            
            # Verifica validade
            expiry = datetime.fromisoformat(found_license["expiry_date"])
            if expiry < datetime.now():
                return False, "Esta chave já expirou!", None
                
            # Prepara dados para salvar localmente
            # Adicionamos o HWID ATUAL para "travar" neste PC
            found_license["hwid"] = self.device_id
            
            return True, "Chave validada com sucesso!", found_license
            
        except Exception as e:
            return False, f"Erro ao verificar licença: {str(e)}", None

    def load_local(self):
        if not os.path.exists(LICENSE_FILE):
            return None
        try:
            with open(LICENSE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None

    def save_local(self, data):
        with open(LICENSE_FILE, 'w') as f:
            json.dump(data, f)

# Função auxiliar para manter compatibilidade com main.py antigo
def check_license():
    system = LicenseSystem()
    return system.check_license()
