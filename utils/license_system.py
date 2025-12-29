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
from pathlib import Path

# URL DO SEU ARQUIVO SITE (ALTERE ISTO DEPOIS!)
# Por enquanto usaremos o mesmo repositório de updates
LICENSE_DB_URL = "https://raw.githubusercontent.com/juniorbatistamlk-stack/updates-bot/main/license_database.json"

LICENSE_FILE = ".license"
SUPPORT_CONTACT = "https://t.me/magoTrader_01"

class LicenseSystem:
    def __init__(self):
        self.device_id = self.get_hwid()
        self.license_data = None
        self._here = Path(__file__).resolve()
        self._project_root = self._here.parent.parent
        
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
            key = input("\n🔑 Chave: ").strip().upper()
            
            if not key:
                continue
                
            print("⏳ Verificando licença...")
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
        """Baixa banco de dados do GitHub e valida chave.

        Se não houver conexão, tenta validar usando um banco local (license_database.json)
        presente no projeto/instalador.
        """
        try:
            key_norm = str(key).strip().upper()

            # 1) Tentar online com timeout
            try:
                response = requests.get(LICENSE_DB_URL, timeout=6)
                if response.status_code == 200:
                    db = response.json()
                    found_license = self._find_license_in_db(db, key_norm)
                    if found_license:
                        return self._validate_and_bind(found_license, key_norm)
            except Exception:
                pass

            # 2) Fallback offline
            local_hit = self._find_license_in_local_dbs(key_norm)
            if local_hit:
                found_license, _src = local_hit
                ok, msg, data = self._validate_and_bind(found_license, key_norm)
                if ok:
                    return True, f"{msg} (offline)", data
                return False, msg, None

            return False, "Erro de conexão com servidor de licenças (e chave não encontrada localmente)", None
            
        except Exception as e:
            return False, f"Erro ao verificar licença: {str(e)}", None

    def _find_license_in_db(self, db, key_norm: str):
        try:
            items = db.get("licenses") if isinstance(db, dict) else None
            if not isinstance(items, list):
                return None
            for lic in items:
                k = str(lic.get("key", "")).strip().upper()
                if k == key_norm:
                    return lic
        except Exception:
            return None
        return None

    def _validate_and_bind(self, found_license: dict, key_norm: str):
        lic_hwid = found_license.get("hwid")
        if lic_hwid is not None and str(lic_hwid).strip() and str(lic_hwid).strip() != self.device_id:
            return False, "❌ CHAVE JÁ USADA! Esta licença já foi ativada em outro computador.", None

        try:
            expiry = datetime.fromisoformat(str(found_license.get("expiry_date")))
        except Exception:
            return False, "Licença com data inválida no banco.", None

        if expiry < datetime.now():
            return False, "Esta chave já expirou!", None

        found_license = dict(found_license)
        found_license["key"] = key_norm
        found_license["hwid"] = self.device_id
        return True, "Chave validada com sucesso!", found_license

    def _find_license_in_local_dbs(self, key_norm: str):
        for path in self._iter_local_db_paths():
            try:
                if not path.exists() or not path.is_file():
                    continue
                with path.open("r", encoding="utf-8") as f:
                    db = json.load(f)
                lic = self._find_license_in_db(db, key_norm)
                if lic:
                    return lic, str(path)
            except Exception:
                continue
        return None

    def _iter_local_db_paths(self):
        try:
            yield Path.cwd() / "license_database.json"
        except Exception:
            pass

        yield self._project_root / "license_database.json"
        yield self._project_root / "INSTALADOR_FINAL" / "license_database.json"

        # Scan subfolders inside INSTALADOR_FINAL for any license_database.json
        try:
            base = self._project_root / "INSTALADOR_FINAL"
            if base.exists() and base.is_dir():
                for child in base.iterdir():
                    if child.is_dir():
                        cand = child / "license_database.json"
                        if cand.exists():
                            yield cand
        except Exception:
            pass

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
