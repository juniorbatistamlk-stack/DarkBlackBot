"""
Compila o Gerenciador de Licenças em um executável
"""
import PyInstaller.__main__
import os
import shutil
from pathlib import Path

print("🔨 Compilando Gerenciador de Licenças...")
print()

# Limpar builds anteriores
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

# Compilar
PyInstaller.__main__.run([
    'license_manager.py',
    '--name=Gerenciador_Licencas',
    '--onefile',
    '--windowed',
    '--clean',
    '--noconfirm',
])

# Mover para pasta final
output_dir = Path("INSTALADOR_FINAL")
output_dir.mkdir(exist_ok=True)

source = Path("dist") / "Gerenciador_Licencas.exe"
dest = output_dir / "Gerenciador_Licencas_v2.exe"

if source.exists():
    shutil.copy2(source, dest)
    
# Limpar
if os.path.exists("Gerenciador_Licencas.spec"):
    os.remove("Gerenciador_Licencas.spec")
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

print()
print("="*70)
print("✅ GERENCIADOR COMPILADO COM SUCESSO!")
print("="*70)
print()
print(f"📁 Local: {dest.absolute()}")
print(f"📦 Arquivo: Gerenciador_Licencas.exe")
print()
print("💡 Agora você pode:")
print("   - Clicar 2x no .exe para abrir o gerenciador")
print("   - Criar atalho na área de trabalho")
print("   - Não precisa mais de Python!")
print()

# Abrir pasta
if os.name == 'nt':
    os.startfile(str(output_dir))

input("\nPressione ENTER para sair...")
