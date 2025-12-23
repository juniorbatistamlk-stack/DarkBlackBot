"""
build_installer.py - GERADOR DO INSTALADOR .EXE
Execute este script para criar o instalador que será enviado aos clientes
"""
import os
import shutil
import zipfile
import subprocess
from pathlib import Path

def create_bot_package():
    """Cria pacote ZIP com arquivos do bot"""
    print("📦 Criando pacote do bot...")
    
    # Arquivos para incluir no instalador
    files_to_include = [
        "main.py",
        "config.py",
        "get_hwid.py",
        "requirements.txt",
        "version.json",
        "api/",
        "strategies/",
        "utils/",
        "ui/"
    ]
    
    # Criar ZIP temporário
    with zipfile.ZipFile("bot_files.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_to_include:
            if os.path.exists(item):
                if os.path.isfile(item):
                    zipf.write(item)
                    print(f"  + {item}")
                elif os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        # Ignorar __pycache__
                        dirs[:] = [d for d in dirs if d != '__pycache__']
                        
                        for file in files:
                            if not file.endswith('.pyc'):
                                file_path = os.path.join(root, file)
                                zipf.write(file_path)
                                print(f"  + {file_path}")
    
    print("✓ Pacote criado: bot_files.zip\n")

def build_exe():
    """Compila instalador em .exe usando PyInstaller"""
    print("🔨 Compilando instalador.exe...")
    print("(Isso pode demorar alguns minutos...)\n")
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",                    # Arquivo único
        "--windowed",                   # Sem console
        "--name=DarkBlackBot_Installer", # Nome do .exe
        "--icon=NONE",                  # Ícone (você pode adicionar um .ico)
        "--add-data=bot_files.zip;.",   # Incluir ZIP no .exe
        "installer.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Compilação concluída!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ PyInstaller não encontrado!")
        print("Instale com: pip install pyinstaller")
        return False

def cleanup():
    """Limpa arquivos temporários"""
    print("🧹 Limpando arquivos temporários...")
    
    # Remover ZIP temporário
    if os.path.exists("bot_files.zip"):
        os.remove("bot_files.zip")
    
    # Remover pasta build do PyInstaller
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Manter dist/ mas avisar
    print("✓ Limpeza concluída\n")

def main():
    print("="*70)
    print("   🚀 GERADOR DE INSTALADOR - DARK BLACK BOT")
    print("="*70)
    print()
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("⚠️  PyInstaller não instalado!")
        print("\nInstalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Etapa 1: Criar pacote
    create_bot_package()
    
    # Etapa 2: Compilar
    success = build_exe()
    
    if not success:
        print("\n❌ Falha ao criar instalador!")
        input("\nPressione ENTER para sair...")
        return
    
    # Etapa 3: Limpar
    cleanup()
    
    # Resultado final
    output_dir = Path("INSTALADOR_FINAL")
    if not output_dir.exists():
        output_dir.mkdir()
        
    source_exe = Path("dist") / "DarkBlackBot_Installer.exe"
    final_exe = output_dir / "DarkBlackBot_Installer.exe"
    
    if source_exe.exists():
        shutil.copy2(source_exe, final_exe)
        
    print("="*70)
    print("✅ INSTALADOR CRIADO COM SUCESSO!")
    print("="*70)
    print()
    print(f"📁 Pasta: {output_dir.absolute()}")
    print(f"📦 Arquivo: {final_exe.name}")
    print(f"📊 Tamanho: {final_exe.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    # Abrir pasta final
    if os.name == 'nt':
        os.startfile(str(output_dir))
    
    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    import sys
    main()
