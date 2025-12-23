import PyInstaller.__main__
import shutil
import os
import sys

def build():
    print("=== BUILDING CLIENT ===")
    PyInstaller.__main__.run([
        'main.py',
        '--name=Client',
        '--onefile',
        '--console',
        '--noconfirm',
        '--add-data=master.key;.',
        '--hidden-import=iqoptionapi',
        '--hidden-import=rich',
        '--collect-all=rich',
    ])
    
    print("\n=== BUILDING ADMIN ===")
    PyInstaller.__main__.run([
        'key_gen.py',
        '--name=AdminGen',
        '--onefile',
        '--console',
        '--noconfirm',
        '--hidden-import=rich',
    ])

def organize():
    print("\n=== ORGANIZING ===")
    if os.path.exists("Release"):
        shutil.rmtree("Release")
    
    os.makedirs("Release/Dark Black", exist_ok=True)
    os.makedirs("Release/Admin", exist_ok=True)
    
    if os.path.exists("dist/Client.exe"):
        shutil.move("dist/Client.exe", "Release/Dark Black/Dark Black.exe")
        print("Client Moved OK.")
    else:
        print("ERROR: Client.exe not found!")

    if os.path.exists("dist/AdminGen.exe"):
        shutil.move("dist/AdminGen.exe", "Release/Admin/Gerador de Keys.exe")
        print("Admin Moved OK.")
    else:
        print("ERROR: AdminGen.exe not found!")

if __name__ == "__main__":
    try:
        build()
        organize()
        print("\nSUCCESS!")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        input("Press Enter to exit...")
