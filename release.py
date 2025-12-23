"""
release.py - SCRIPT DE DEPLOYMENT AUTOMÁTICO
Execute este script quando quiser lançar uma nova versão do bot
"""
import os
import json
import zipfile
import shutil
from datetime import datetime

def create_release():
    """Cria um pacote de release do bot"""
    
    print("="*70)
    print("   📦 CRIADOR DE RELEASE - DARK BLACK BOT")
    print("="*70)
    print()
    
    # Solicitar informações da versão
    current_version = input("Digite o número da nova versão (ex: 1.0.1): ").strip()
    changelog = input("Descreva as mudanças (changelog): ").strip()
    
    if not current_version or not changelog:
        print("❌ Informações obrigatórias não fornecidas!")
        return
    
    # Criar pasta de release
    release_dir = f"release-{current_version}"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    print(f"\\n📁 Criando release em: {release_dir}")
    
    # Arquivos e pastas para incluir
    files_to_include = [
        "main.py",
        "config.py",
        "get_hwid.py",  # Cliente precisa disso
        "version.json",
        "requirements.txt",
        "api/",
        "strategies/",
        "utils/",
        "ui/"
    ]
    
    # Copiar arquivos
    print("\\n📋 Copiando arquivos...")
    for item in files_to_include:
        source = item
        dest = os.path.join(release_dir, item)
        
        if os.path.exists(source):
            if os.path.isfile(source):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)
                print(f"  ✓ {item}")
            elif os.path.isdir(source):
                shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                print(f"  ✓ {item}/")
    
    # Atualizar version.json
    version_data = {
        "version": current_version,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "changelog": changelog,
        "download_url": f"https://github.com/SEU_USUARIO/darkblack-bot/releases/download/v{current_version}/darkblack-bot-v{current_version}.zip"
    }
    
    with open(os.path.join(release_dir, "version.json"), 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    with open("version.json", 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    # Criar arquivo ZIP
    zip_filename = f"darkblack-bot-v{current_version}.zip"
    print(f"\\n🗜️ Compactando em: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            # Ignorar __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if not file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, release_dir)
                    zipf.write(file_path, arcname)
                    print(f"  + {arcname}")
    
    # Limpar pasta temporária
    shutil.rmtree(release_dir)
    
    print()
    print("="*70)
    print("✅ RELEASE CRIADO COM SUCESSO!")
    print("="*70)
    print()
    print(f"📦 Arquivo: {zip_filename}")
    print(f"📄 Versão: {current_version}")
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Faça upload do arquivo ZIP para GitHub Releases")
    print("2. Ou hospede em Google Drive/Dropbox")
    print("3. Atualize a URL em version.json se necessário")
    print("4. Faça upload do version.json atualizado")
    print()
    print("💡 DICA: Clientes receberão atualização automática na próxima inicialização!")
    print()

if __name__ == "__main__":
    create_release()
    input("\\nPressione ENTER para sair...")
