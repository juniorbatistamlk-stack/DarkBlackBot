import PyInstaller.__main__
import shutil
import os
from pathlib import Path

def build_manager():
    print("🚀 INICIANDO CRIAÇÃO DO GERENCIADOR DE LICENÇAS...")
    
    # 1. Limpar builds anteriores
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # 2. Configurar PyInstaller
    args = [
        'license_manager.py',  # Script principal
        '--name=Gerenciador_Licencas',  # Nome do executável
        '--onefile',           # Arquivo único
        '--windowed',          # Sem janela de console (GUI)
        '--clean',             # Limpar cache
        '--noconfirm',         # Não pedir confirmação
    ]
    
    # 3. Executar
    print("🔨 Compilando Gerenciador_Licencas.exe...")
    PyInstaller.__main__.run(args)
    
    # 4. Organizar saída
    output_dir = Path("INSTALADOR_FINAL")
    if not output_dir.exists():
        output_dir.mkdir()
        
    source_exe = Path("dist") / "Gerenciador_Licencas.exe"
    final_exe = output_dir / "Gerenciador_Licencas_(SEU_USO).exe"
    
    if source_exe.exists():
        shutil.copy2(source_exe, final_exe)
        
    # Limpeza
    if os.path.exists("Gerenciador_Licencas.spec"):
        os.remove("Gerenciador_Licencas.spec")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        
    print("="*70)
    print("✅ GERENCIADOR CRIADO COM SUCESSO!")
    print("="*70)
    print(f"📁 Pasta: {output_dir.absolute()}")
    print(f"📦 Arquivo: {final_exe.name}")
    print()
    
    # Abrir pasta
    if os.name == 'nt':
        os.startfile(str(output_dir))

if __name__ == "__main__":
    build_manager()
