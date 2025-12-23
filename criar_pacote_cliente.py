"""
criar_pacote_cliente.py - CRIA PACOTE ZIP PARA O CLIENTE
Versão simplificada e confiável
"""
import zipfile
import os
import shutil
from pathlib import Path

def criar_pacote():
    print("="*70)
    print("   📦 CRIANDO PACOTE PARA CLIENTE")
    print("="*70)
    print()
    
    # Nome do pacote
    pacote_nome = "DarkBlackBot_Pacote.zip"
    
    # Arquivos e pastas para incluir
    itens = [
        "main.py",
        "config.py",
        "get_hwid.py",
        "requirements.txt",
        "INSTALAR.bat",
        "icon.ico",
        "logo.jpg",
        "api/",
        "strategies/",
        "utils/",
        "ui/"
    ]
    
    # Criar ZIP
    print(f"📝 Criando {pacote_nome}...")
    print()
    
    with zipfile.ZipFile(pacote_nome, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in itens:
            if os.path.isfile(item):
                zipf.write(item, item)
                print(f"  ✓ {item}")
            elif os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    # Ignorar __pycache__
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    
                    for file in files:
                        if not file.endswith('.pyc'):
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                            print(f"  ✓ {file_path}")
    
    # Mover para pasta INSTALADOR_FINAL
    output_dir = Path("INSTALADOR_FINAL")
    output_dir.mkdir(exist_ok=True)
    
    final_path = output_dir / pacote_nome
    shutil.move(pacote_nome, final_path)
    
    print()
    print("="*70)
    print("✅ PACOTE CRIADO COM SUCESSO!")
    print("="*70)
    print()
    print(f"📁 Local: {final_path.absolute()}")
    print(f"📊 Tamanho: {final_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("INSTRUÇÕES PARA O CLIENTE:")
    print("1. Baixar o arquivo ZIP")
    print("2. Descompactar em uma pasta")
    print("3. Executar 'INSTALAR.bat'")
    print("4. Seguir as instruções na tela")
    print()
    print("💡 MUITO MAIS SIMPLES E CONFIÁVEL!")
    print()
    
    # Abrir pasta
    if os.name == 'nt':
        os.startfile(str(output_dir))

if __name__ == "__main__":
    criar_pacote()
    input("\nPressione ENTER para sair...")
