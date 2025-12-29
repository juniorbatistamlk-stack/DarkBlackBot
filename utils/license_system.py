"""
utils/license_system.py - SISTEMA DE VALIDAÇÃO ONLINE VIA GITHUB v2.0
"""
import os
import json
import requests
import hashlib
import time
from datetime import datetime
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
        Retorna: True se válido, False se inválido/bloqueado
        """
        # Tenta carregar licença salva localmente
        local_data = self.load_local()
        
        # 1. SEM LICENÇA -> PEDIR ATIVAÇÃO
        if not local_data:
            return self.request_activation()
            
        # 2. VERIFICA HWID (ANTICÓPIA)
        if local_data.get("hwid") != self.device_id:
            print("\n❌ LICENÇA INVÁLIDA PARA ESTE COMPUTADOR!")
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
            return self.request_activation()
            
        # 3. VERIFICA ESTADO E VALIDADE
        try:
            expiry_date = datetime.fromisoformat(local_data["expiry_date"])
            days_left = (expiry_date - datetime.now()).days
        except:
            print("\n❌ ERRO NA LICENÇA (DATA CORROMPIDA)")
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
            return self.request_activation()
        
        # === CENÁRIO 1: LICENÇA VENCIDA (BLOQUEIO) ===
        if days_left < 0:
            self.show_expired_screen(days_left)
            input("\nPressione ENTER para sair...")
            return False
            
        # === CENÁRIO 2: LICENÇA VENCENDO (AVISO) ===
        if days_left <= 3:
            self.show_warning_screen(days_left)
            print(f"\n✅ Acesso liberado temporariamente... ({days_left} dias restantes)")
            time.sleep(3) # Delay para ler
            return True
            
        # === CENÁRIO 3: LICENÇA OK (SILENCIOSO) ===
        print(f"✅ Licença Validada! Dias restantes: {days_left}")
        return True

    def show_expired_screen(self, days_left):
        """Tela de Bloqueio Persuasiva"""
        print("\n" + "█"*60)
        print("🛑 ACESSO BLOQUEADO - LICENÇA EXPIRADA")
        print("█"*60)
        print("\n😱 OPA! SEU ROBÔ PAROU DE FATURAR!")
        print(f"Sua licença venceu há {abs(days_left)} dias.\n")
        print("Para continuar faturando muito no automático e não")
        print("perder as oportunidades de hoje, renove agora!\n")
        print("👉 CLIQUE AQUI AGORA: " + SUPPORT_CONTACT)
        print("\n(Renove e receba sua nova chave em minutos)")
        print("█"*60 + "\n")

    def show_warning_screen(self, days_left):
        """Tela de Aviso Persuasiva"""
        print("\n" + "═"*60)
        print(f"⚠️ AVISO URGENTE: RESTAM APENAS {days_left} DIAS!")
        print("═"*60)
        print("\nSeu acesso ao bot está vencendo...")
        print("Não deixe para a última hora e corra o risco de")
        print("ficar sem operar justo no melhor dia do mercado!\n")
        print("🚀 Garanta sua renovação agora mesmo:")
        print("👉 " + SUPPORT_CONTACT)
        print("\nEvite paradas desnecessárias no seu lucro!")
        print("═"*60 + "\n")

    def request_activation(self):
        """Solicita chave ao usuário e valida online"""
        print("\n" + "="*60)
        print("🔐 ATIVAÇÃO - DARK BLACK BOT PRO")
        print("="*60)
        print(f"Seu ID de Hardware: {self.device_id}")
        print("\nInsira sua chave de licença para ativar.")
        print("Adquira em: " + SUPPORT_CONTACT)
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
                return False, "Erro de conexão com servidor de licenças", None
                
            db = response.json()
            
            found_license = None
            for lic in db["licenses"]:
                if lic["key"] == key:
                    found_license = lic
                    break
            
            if not found_license:
                return False, "Chave inválida ou não encontrada!", None
            
            # VALIDAÇÃO DE USO ÚNICO (HWID)
            if found_license.get("hwid") and found_license["hwid"] is not None and found_license["hwid"] != self.device_id:
                return False, "❌ CHAVE JÁ USADA! Esta licença já foi ativada em outro computador.", None
                
            # Verifica validade
            expiry = datetime.fromisoformat(found_license["expiry_date"])
            if expiry < datetime.now():
                return False, "Esta chave já expirou!", None
                
            # VINCULA a chave a ESTE PC
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

# Função auxiliar para manter compatibilidade
def check_license():
    system = LicenseSystem()
    return system.check_license()
