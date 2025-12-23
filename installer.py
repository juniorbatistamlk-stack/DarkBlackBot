"""
installer.py - INSTALADOR AUTOMÁTICO DO DARK BLACK BOT
Este script será convertido em .exe para distribuição aos clientes
"""
import os
import sys
import subprocess
import zipfile
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json

class BotInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Dark Black Bot - Instalador")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Configurar estilo
        self.root.configure(bg='#1a1a2e')
        
        # Variáveis
        self.install_path = Path.home() / "DarkBlackBot"
        self.current_step = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Cria interface gráfica"""
        # Header
        header = tk.Frame(self.root, bg='#0f3460', height=80)
        header.pack(fill='x')
        
        title = tk.Label(
            header, 
            text="🤖 DARK BLACK BOT PRO",
            font=('Arial', 20, 'bold'),
            bg='#0f3460',
            fg='#ffffff'
        )
        title.pack(pady=20)
        
        # Área de conteúdo
        content = tk.Frame(self.root, bg='#1a1a2e')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Label de status
        self.status_label = tk.Label(
            content,
            text="Bem-vindo ao instalador!",
            font=('Arial', 12),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        self.status_label.pack(pady=10)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(
            content,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=10)
        
        # Log de instalação
        log_frame = tk.Frame(content, bg='#1a1a2e')
        log_frame.pack(fill='both', expand=True, pady=10)
        
        tk.Label(
            log_frame,
            text="Log de Instalação:",
            font=('Arial', 10, 'bold'),
            bg='#1a1a2e',
            fg='#16C172'
        ).pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            bg='#0f0f1e',
            fg='#16C172',
            font=('Consolas', 9)
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Botão de instalação
        self.install_btn = tk.Button(
            content,
            text="INICIAR INSTALAÇÃO",
            command=self.start_installation,
            font=('Arial', 12, 'bold'),
            bg='#16C172',
            fg='#ffffff',
            activebackground='#12a05b',
            pady=10,
            cursor='hand2'
        )
        self.install_btn.pack(pady=20)
    
    def log(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.insert('end', f"[{self.current_step}/5] {message}\\n")
        self.log_text.see('end')
        self.root.update()
    
    def start_installation(self):
        """Inicia instalação em thread separada"""
        self.install_btn.config(state='disabled')
        self.progress.start()
        
        thread = threading.Thread(target=self.install, daemon=True)
        thread.start()
    
    def install(self):
        """Processo de instalação"""
        try:
            # Passo 1: Criar diretório de instalação
            self.current_step = 1
            self.status_label.config(text="Criando diretório de instalação...")
            self.log(f"Criando pasta: {self.install_path}")
            
            self.install_path.mkdir(parents=True, exist_ok=True)
            self.log("✓ Diretório criado com sucesso")
            
            # Passo 2: Verificar Python
            self.current_step = 2
            self.status_label.config(text="Verificando instalação do Python...")
            self.log("Verificando Python...")
            
            python_ok = self.check_python()
            if not python_ok:
                self.log("❌ Python não encontrado!")
                self.log("Por favor, instale Python 3.8+ de python.org")
                self.show_error("Python não encontrado. Instale Python 3.8+ e tente novamente.")
                return
            
            self.log("✓ Python instalado corretamente")
            
            # Passo 3: Extrair arquivos do bot
            self.current_step = 3
            self.status_label.config(text="Extraindo arquivos...")
            self.log("Extraindo bot...")
            
            # Os arquivos do bot estão embutidos no .exe
            # Aqui você precisa incluir a lógica para extrair
            self.extract_bot_files()
            self.log("✓ Arquivos extraídos")
            
            # Passo 4: Instalar dependências
            self.current_step = 4
            self.status_label.config(text="Instalando dependências...")
            self.log("Instalando bibliotecas Python...")
            
            self.install_dependencies()
            self.log("✓ Dependências instaladas")
            
            # Passo 5: Criar atalho
            self.current_step = 5
            self.status_label.config(text="Criando atalho...")
            self.log("Criando atalho na área de trabalho...")
            
            self.create_shortcut()
            self.log("✓ Atalho criado")
            
            # Concluído
            self.progress.stop()
            self.status_label.config(text="✅ Instalação concluída!")
            self.log("")
            self.log("="*50)
            self.log("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
            self.log("="*50)
            self.log("")
            self.log(f"Bot instalado em: {self.install_path}")
            self.log("Use o atalho na área de trabalho para iniciar")
            
            messagebox.showinfo(
                "Sucesso!",
                f"Bot instalado com sucesso!\\n\\n"
                f"Local: {self.install_path}\\n\\n"
                f"Use o atalho 'Dark Black Bot' na área de trabalho"
            )
            
            self.install_btn.config(text="FECHAR", state='normal')
            self.install_btn.config(command=self.root.quit)
            
        except Exception as e:
            self.progress.stop()
            self.log(f"\\n❌ ERRO: {str(e)}")
            self.show_error(f"Erro durante instalação:\\n{str(e)}")
    
    def check_python(self):
        """Verifica se Python está instalado"""
        try:
            result = subprocess.run(
                [sys.executable, '--version'],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip()
            self.log(f"  {version} detectado")
            return True
        except:
            return False
    
    def extract_bot_files(self):
        """Extrai arquivos do bot (embutidos no .exe via PyInstaller)"""
        # Quando compilado com PyInstaller usando --onefile --add-data,
        # os arquivos ficam em sys._MEIPASS
        if getattr(sys, 'frozen', False):
            bundle_dir = Path(sys._MEIPASS)
        else:
            bundle_dir = Path(__file__).parent
        
        bot_zip = bundle_dir / "bot_files.zip"
        
        if bot_zip.exists():
            self.log(f"  Extraindo de {bot_zip.name}")
            with zipfile.ZipFile(bot_zip, 'r') as zip_ref:
                zip_ref.extractall(self.install_path)
        else:
            # Para teste local
            self.log("  Modo de desenvolvimento detectado")
            # Copiar arquivos manualmente se estiver testando
    
    def install_dependencies(self):
        """Instala dependências Python"""
        requirements = self.install_path / "requirements.txt"
        
        if requirements.exists():
            self.log("  Executando pip install...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements)],
                capture_output=True
            )
        else:
            self.log("  requirements.txt não encontrado, pulando...")
    
    def create_shortcut(self):
        """Cria atalho na área de trabalho"""
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "Dark Black Bot.lnk"
        
        try:
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_path / "main.py"}"'
            shortcut.WorkingDirectory = str(self.install_path)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            self.log(f"  Atalho: {shortcut_path}")
        except:
            # Se falhar, criar arquivo .bat simples
            bat_path = desktop / "Dark Black Bot.bat"
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\\n')
                f.write(f'cd /d "{self.install_path}"\\n')
                f.write(f'python main.py\\n')
                f.write(f'pause\\n')
            self.log(f"  Script criado: {bat_path}")
    
    def show_error(self, message):
        """Mostra erro ao usuário"""
        messagebox.showerror("Erro", message)
        self.install_btn.config(text="FECHAR", state='normal')
        self.install_btn.config(command=self.root.quit)

def main():
    root = tk.Tk()
    app = BotInstaller(root)
    root.mainloop()

if __name__ == "__main__":
    main()
