"""
publicar_atualizacao.py - PUBLICA NOVA VERSÃO AUTOMÁTICO
Gera pacote do cliente e prepara para publicação no repo de updates
"""
import os
import json
import shutil
import zipfile
from datetime import datetime

# Configurações
VERSION_FILE = "version.json"
UPDATES_DIR = "updates"
PACKAGE_NAME = "darkblack-bot-client"

def load_version():
    """Carrega versão atual"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0.0", "changelog": "Versão inicial"}

def increment_version(version_str, increment_type="patch"):
    """
    Incrementa versão (formato: MAJOR.MINOR.PATCH)
    increment_type: 'major', 'minor', 'patch'
    """
    parts = version_str.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def create_client_package(version):
    """Cria pacote ZIP do cliente"""
    print(f"\n📦 Criando pacote v{version}...")
    
    # Nome do arquivo
    zip_name = f"{PACKAGE_NAME}-v{version}.zip"
    zip_path = os.path.join(UPDATES_DIR, zip_name)
    
    # Arquivos/pastas que vão no pacote do CLIENTE
    items_to_include = [
        "main.py",
        "config.py",
        "run.bat",
        "INSTALAR.bat",
        "requirements.txt",
        "icon.ico",
        "logo.jpg",
        "api/",
        "strategies/",
        "utils/",
        "ui/",
        "tests/",
    ]
    
    # Criar ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in items_to_include:
            if os.path.exists(item):
                if os.path.isfile(item):
                    zipf.write(item, item)
                    print(f"  ✓ {item}")
                else:
                    for root, dirs, files in os.walk(item):
                        # Pular __pycache__ e .pyc
                        if '__pycache__' in root:
                            continue
                        for file in files:
                            if file.endswith('.pyc'):
                                continue
                            file_path = os.path.join(root, file)
                            arcname = file_path
                            zipf.write(file_path, arcname)
                    print(f"  ✓ {item}/")
    
    file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\n✅ Pacote criado: {zip_name} ({file_size_mb:.2f} MB)")
    return zip_name

def update_version_json(version, changelog, zip_name):
    """Atualiza version.json no diretório updates"""
    version_data = {
        "version": version,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "changelog": changelog,
        "download_url": f"https://github.com/juniorbatistamlk-stack/updates-bot/raw/main/{zip_name}",
        "min_supported_version": "1.0.0"
    }
    
    version_path = os.path.join(UPDATES_DIR, VERSION_FILE)
    with open(version_path, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {VERSION_FILE} atualizado")
    return version_data

def create_readme():
    """Cria README.md para o repo de updates"""
    readme_content = f"""# Dark Black Bot - Updates

Este repositório contém apenas os pacotes de atualização do Dark Black Bot.

## Download

Baixe a versão mais recente através do arquivo `version.json`.

## Para Desenvolvedores

Este é um repositório público apenas para distribuição de atualizações.
O código-fonte completo está em um repositório privado.

---
© {datetime.now().year} Dark Black Bot - Todos os direitos reservados
"""
    
    readme_path = os.path.join(UPDATES_DIR, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README.md criado")

def main():
    print("=" * 60)
    print("   🚀 PUBLICADOR DE ATUALIZAÇÕES - DARK BLACK BOT")
    print("=" * 60)
    
    # Criar diretório updates se não existir
    os.makedirs(UPDATES_DIR, exist_ok=True)
    
    # Carregar versão atual
    current_data = load_version()
    current_version = current_data.get("version", "1.0.0")
    
    print(f"\n📌 Versão atual: {current_version}")
    print("\nTipo de atualização:")
    print("  1. PATCH (bug fixes)      - 1.0.0 → 1.0.1")
    print("  2. MINOR (novas features) - 1.0.0 → 1.1.0")
    print("  3. MAJOR (breaking)       - 1.0.0 → 2.0.0")
    
    choice = input("\nEscolha (1/2/3): ").strip()
    
    increment_map = {"1": "patch", "2": "minor", "3": "major"}
    increment_type = increment_map.get(choice, "patch")
    
    new_version = increment_version(current_version, increment_type)
    print(f"\n🆕 Nova versão será: {new_version}")
    
    # Changelog
    print("\nDigite o CHANGELOG (o que mudou):")
    print("(Pressione ENTER duas vezes para finalizar)")
    changelog_lines = []
    while True:
        line = input()
        if line == "":
            break
        changelog_lines.append(line)
    
    changelog = "\n".join(changelog_lines) if changelog_lines else "Melhorias e correções"
    
    # Criar pacote
    zip_name = create_client_package(new_version)
    
    # Atualizar version.json
    version_data = update_version_json(new_version, changelog, zip_name)
    
    # Criar README
    create_readme()
    
    # Atualizar version.json LOCAL também (para referência)
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ TUDO PRONTO!")
    print("=" * 60)
    print(f"\nArquivos criados em: {UPDATES_DIR}/")
    print(f"  - {zip_name}")
    print(f"  - {VERSION_FILE}")
    print(f"  - README.md")
    print("\n📤 PRÓXIMO PASSO:")
    print("   Execute: PUBLICAR_UPDATES.bat")
    print("   (Isso vai enviar para o GitHub de updates)")
    print("\n")

if __name__ == "__main__":
    main()
