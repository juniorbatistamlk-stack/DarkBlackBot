"""
get_hwid.py - Hardware ID Generator
Este script é enviado ao CLIENTE para ele obter o Hardware ID do PC dele.
"""
import platform
import subprocess
import hashlib

def get_hwid():
    """
    Gera um Hardware ID único baseado em:
    - Processador
    - Serial da Placa-mãe (Windows)
    - UUID do disco
    """
    hwid_parts = []
    
    # 1. Nome do processador
    try:
        processor = platform.processor()
        if processor:
            hwid_parts.append(processor)
    except:
        pass
    
    # 2. Serial da placa-mãe (Windows)
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic baseboard get serialnumber", 
                shell=True, 
                encoding='utf-8',
                stderr=subprocess.DEVNULL
            ).strip().split('\n')
            if len(result) > 1:
                serial = result[1].strip()
                if serial and serial != "SerialNumber":
                    hwid_parts.append(serial)
    except:
        pass
    
    # 3. UUID do sistema
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic csproduct get uuid",
                shell=True,
                encoding='utf-8',
                stderr=subprocess.DEVNULL
            ).strip().split('\n')
            if len(result) > 1:
                uuid = result[1].strip()
                if uuid and uuid != "UUID":
                    hwid_parts.append(uuid)
    except:
        pass
    
    # 4. Fallback: nome da máquina
    if not hwid_parts:
        hwid_parts.append(platform.node())
    
    # Gerar hash único
    combined = "-".join(hwid_parts)
    hwid = hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
    
    return hwid

if __name__ == "__main__":
    print("="*60)
    print("   GERADOR DE HARDWARE ID - DARK BLACK BOT")
    print("="*60)
    print()
    print("Este código identifica seu computador de forma única.")
    print("Envie este código para o vendedor para receber sua licença.")
    print()
    print("-"*60)
    
    hwid = get_hwid()
    
    print(f"SEU HARDWARE ID: {hwid}")
    print("-"*60)
    print()
    print("📋 Copie e envie este código para o vendedor.")
    print("⚠️  NÃO compartilhe este código publicamente!")
    print()
    input("Pressione ENTER para sair...")
