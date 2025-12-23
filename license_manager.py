"""
license_manager.py - GERENCIADOR COMPLETO DE LICENÇAS
Sistema profissional com interface gráfica para gerenciar clientes
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta

LICENSE_DB = "license_database.json"

class LicenseManager:
    def __init__(self, root):
        self.root = root
        self.root.title("🔑 Gerenciador de Licenças - Dark Black Bot")
        self.root.geometry("1000x650")
        self.root.configure(bg='#1a1a2e')
        
        self.db = self.load_database()
        self.setup_ui()
        self.refresh_list()
    
    def load_database(self):
        """Carrega banco de dados"""
        if os.path.exists(LICENSE_DB):
            try:
                with open(LICENSE_DB, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"licenses": []}
    
    def save_database(self):
        """Salva banco de dados"""
        with open(LICENSE_DB, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def generate_key(self):
        """Gera chave única de 16 caracteres"""
        # Formato: DBB-XXXX-XXXX-XXXX
        key = "DBB-" + "-".join([
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper()
        ])
        return key
    
    def setup_ui(self):
        """Cria interface"""
        # Header
        header = tk.Frame(self.root, bg='#0f3460', height=70)
        header.pack(fill='x')
        
        tk.Label(
            header,
            text="🔑 GERENCIADOR DE LICENÇAS",
            font=('Arial', 18, 'bold'),
            bg='#0f3460',
            fg='#ffffff'
        ).pack(pady=20)
        
        # Toolbar
        toolbar = tk.Frame(self.root, bg='#1a1a2e')
        toolbar.pack(fill='x', padx=10, pady=10)
        
        tk.Button(
            toolbar,
            text="➕ NOVA LICENÇA",
            command=self.new_license,
            bg='#16C172',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            toolbar,
            text="🔄 RENOVAR",
            command=self.renew_license,
            bg='#4A90E2',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            toolbar,
            text="✏️ EDITAR",
            command=self.edit_license,
            bg='#F5A623',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            toolbar,
            text="🗑️ EXCLUIR",
            command=self.delete_license,
            bg='#E74C3C',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            toolbar,
            text="🔑 GERAR NOVA KEY",
            command=self.regenerate_key,
            bg='#9B59B6',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            toolbar,
            text="📋 COPIAR KEY",
            command=self.copy_key,
            bg='#1ABC9C',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Lista de licenças
        list_frame = tk.Frame(self.root, bg='#1a1a2e')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        columns = ('Nome', 'WhatsApp', 'Chave', 'Status', 'Validade', 'Dias Restantes')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            height=20
        )
        
        # Configurar colunas
        self.tree.heading('Nome', text='Nome')
        self.tree.heading('WhatsApp', text='WhatsApp')
        self.tree.heading('Chave', text='Chave de Licença')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Validade', text='Validade')
        self.tree.heading('Dias Restantes', text='Dias Restantes')
        
        self.tree.column('Nome', width=150)
        self.tree.column('WhatsApp', width=120)
        self.tree.column('Chave', width=200)
        self.tree.column('Status', width=100)
        self.tree.column('Validade', width=100)
        self.tree.column('Dias Restantes', width=120)
        
        self.tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Estilizar Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background='#0f0f1e', foreground='white', fieldbackground='#0f0f1e')
        style.configure('Treeview.Heading', background='#0f3460', foreground='white', font=('Arial', 10, 'bold'))
    
    def refresh_list(self):
        """Atualiza lista de licenças"""
        # Limpar
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar licenças
        for lic in self.db["licenses"]:
            expiry = datetime.fromisoformat(lic["expiry_date"])
            days_left = (expiry - datetime.now()).days
            
            # Verificar status
            if days_left < 0:
                status = "❌ Expirada"
                days_str = f"{abs(days_left)} dias atrás"
            else:
                status = "✅ Ativa"
                days_str = f"{days_left} dias"
            
            self.tree.insert('', 'end', values=(
                lic["name"],
                lic["whatsapp"],
                lic["key"],
                status,
                expiry.strftime("%d/%m/%Y"),
                days_str
            ))
    
    def new_license(self):
        """Criar nova licença"""
        # Dialog personalizado
        dialog = tk.Toplevel(self.root)
        dialog.title("Nova Licença")
        dialog.geometry("400x300")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="📝 NOVA LICENÇA", font=('Arial', 14, 'bold'), bg='#1a1a2e', fg='white').pack(pady=10)
        
        # Nome
        tk.Label(dialog, text="Nome do Cliente:", bg='#1a1a2e', fg='white').pack(pady=5)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.pack()
        
        # WhatsApp
        tk.Label(dialog, text="WhatsApp (com DDI):", bg='#1a1a2e', fg='white').pack(pady=5)
        whatsapp_entry = tk.Entry(dialog, width=40)
        whatsapp_entry.insert(0, "+55")
        whatsapp_entry.pack()
        
        # Dias
        tk.Label(dialog, text="Dias de Validade:", bg='#1a1a2e', fg='white').pack(pady=5)
        days_entry = tk.Entry(dialog, width=40)
        days_entry.insert(0, "30")
        days_entry.pack()
        
        def create():
            name = name_entry.get().strip()
            whatsapp = whatsapp_entry.get().strip()
            
            try:
                days = int(days_entry.get())
            except:
                messagebox.showerror("Erro", "Dias inválido!")
                return
            
            if not name or not whatsapp:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            # Criar licença
            key = self.generate_key()
            expiry_date = datetime.now() + timedelta(days=days)
            
            license_data = {
                "key": key,
                "name": name,
                "whatsapp": whatsapp,
                "created_at": datetime.now().isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "hwid": None, # Será preenchido se implementarmos sincronização reversa, por enquanto é NULL
                "notes": "Gerado via Manager"
            }
            
            self.db["licenses"].append(license_data)
            self.save_database()
            
            dialog.destroy()
            
            # Copiar para área de transferência
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            
            messagebox.showinfo(
                "Licença Criada!",
                f"Chave gerada com sucesso!\n\n"
                f"Cliente: {name}\n"
                f"WhatsApp: {whatsapp}\n"
                f"Validade: {days} dias\n\n"
                f"CHAVE:\n{key}\n\n"
                f"✅ Chave COPIADA para área de transferência!\n"
                f"Cole com Ctrl+V para enviar ao cliente."
            )
            
            self.refresh_list()
        
        tk.Button(
            dialog,
            text="✅ CRIAR LICENÇA",
            command=create,
            bg='#16C172',
            fg='white',
            font=('Arial', 11, 'bold'),
            pady=10
        ).pack(pady=20)
    
    def renew_license(self):
        """Renovar licença selecionada"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença!")
            return
        
        item = self.tree.item(selected[0])
        key = item['values'][2]
        
        # Encontrar licença
        lic = next((l for l in self.db["licenses"] if l["key"] == key), None)
        if not lic:
            return
        
        days = simpledialog.askinteger("Renovar", f"Quantos dias adicionar para {lic['name']}?", initialvalue=30)
        if not days:
            return
        
        # Renovar
        current_expiry = datetime.fromisoformat(lic["expiry_date"])
        if current_expiry < datetime.now():
            # Expirada: renovar a partir de hoje
            new_expiry = datetime.now() + timedelta(days=days)
        else:
            # Ativa: adicionar aos dias restantes
            new_expiry = current_expiry + timedelta(days=days)
        
        lic["expiry_date"] = new_expiry.isoformat()
        self.save_database()
        
        messagebox.showinfo("Sucesso", f"Licença renovada por {days} dias!\nNova validade: {new_expiry.strftime('%d/%m/%Y')}")
        self.refresh_list()
    
    def edit_license(self):
        """Editar licença selecionada"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença!")
            return
        
        item = self.tree.item(selected[0])
        key = item['values'][2]
        
        lic = next((l for l in self.db["licenses"] if l["key"] == key), None)
        if not lic:
            return
        
        # Dialog de edição
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Licença")
        dialog.geometry("400x250")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="✏️ EDITAR LICENÇA", font=('Arial', 14, 'bold'), bg='#1a1a2e', fg='white').pack(pady=10)
        
        tk.Label(dialog, text="Nome:", bg='#1a1a2e', fg='white').pack()
        name_entry = tk.Entry(dialog, width=40)
        name_entry.insert(0, lic["name"])
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="WhatsApp:", bg='#1a1a2e', fg='white').pack()
        whatsapp_entry = tk.Entry(dialog, width=40)
        whatsapp_entry.insert(0, lic["whatsapp"])
        whatsapp_entry.pack(pady=5)
        
        def save():
            lic["name"] = name_entry.get().strip()
            lic["whatsapp"] = whatsapp_entry.get().strip()
            self.save_database()
            dialog.destroy()
            messagebox.showinfo("Sucesso", "Licença atualizada!")
            self.refresh_list()
        
        tk.Button(dialog, text="💾 SALVAR", command=save, bg='#16C172', fg='white', font=('Arial', 11, 'bold'), pady=8).pack(pady=15)
    
    def delete_license(self):
        """Excluir licença"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença!")
            return
        
        item = self.tree.item(selected[0])
        key = item['values'][2]
        name = item['values'][0]
        
        if not messagebox.askyesno("Confirmar", f"Excluir licença de {name}?\n\nEsta ação não pode ser desfeita!"):
            return
        
        self.db["licenses"] = [l for l in self.db["licenses"] if l["key"] != key]
        self.save_database()
        
        messagebox.showinfo("Sucesso", "Licença excluída!")
        self.refresh_list()
    
    def regenerate_key(self):
        """Gerar nova chave para cliente"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença!")
            return
        
        item = self.tree.item(selected[0])
        old_key = item['values'][2]
        name = item['values'][0]
        
        if not messagebox.askyesno("Confirmar", f"Gerar nova chave para {name}?\n\nA chave antiga será invalidada!"):
            return
        
        lic = next((l for l in self.db["licenses"] if l["key"] == old_key), None)
        if not lic:
            return
        
        # Gerar nova chave
        new_key = self.generate_key()
        lic["key"] = new_key
        lic["hwid"] = None
        lic["activated_at"] = None
        
        self.save_database()
        
        messagebox.showinfo(
            "Nova Chave Gerada!",
            f"Nova chave para {name}:\n\n{new_key}\n\n⚠️ IMPORTANTE: Suba o arquivo license_database.json\npara o GitHub para validar a nova chave!"
        )
        self.refresh_list()
    
    def copy_key(self):
        """Copiar chave selecionada para área de transferência"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença!")
            return
        
        item = self.tree.item(selected[0])
        key = item['values'][2]
        name = item['values'][0]
        
        # Copiar para clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        
        messagebox.showinfo(
            "Copiado!",
            f"Chave de {name} copiada!\n\n{key}\n\n✅ Cole com Ctrl+V para enviar."
        )

def main():
    root = tk.Tk()
    app = LicenseManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
