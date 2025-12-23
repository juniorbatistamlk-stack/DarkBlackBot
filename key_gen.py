# key_gen.py
"""
🔑 GERADOR DE LICENÇAS - DARK BLACK BOT PRO
Gerencia usuários, gera chaves, renova e edita licenças.
"""
import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel

console = Console()

LICENSE_FILE = "licenses.json"

def load_licenses():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"licenses": []}

def save_licenses(data):
    with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_key():
    """Gera uma chave única de 20 caracteres"""
    raw = secrets.token_hex(16)
    key = f"DBB-{raw[:4].upper()}-{raw[4:8].upper()}-{raw[8:12].upper()}-{raw[12:16].upper()}"
    return key

def hash_key(key):
    """Cria hash da chave para armazenamento seguro"""
    return hashlib.sha256(key.encode()).hexdigest()

def show_menu():
    console.print(Panel(
        "[bold red]🔑 GERADOR DE LICENÇAS[/bold red]\n"
        "[white]DARK BLACK BOT PRO[/white]",
        border_style="red"
    ))
    
    console.print("\n[bold]OPÇÕES:[/bold]")
    console.print("1. [green]➕ Criar nova licença[/green]")
    console.print("2. [cyan]📋 Listar todas as licenças[/cyan]")
    console.print("3. [yellow]✏️ Editar usuário[/yellow]")
    console.print("4. [blue]🔄 Renovar licença[/blue]")
    console.print("5. [magenta]🔑 Gerar nova chave para usuário[/magenta]")
    console.print("6. [red]🗑️ Excluir licença[/red]")
    console.print("7. [dim]🚪 Sair[/dim]")
    
    return IntPrompt.ask("\nEscolha", choices=["1","2","3","4","5","6","7"])

def create_license():
    console.print("\n[bold green]➕ CRIAR NOVA LICENÇA[/bold green]\n")
    
    name = Prompt.ask("Nome do usuário")
    whatsapp = Prompt.ask("WhatsApp (com DDD)")
    days = IntPrompt.ask("Dias de validade", default=30)
    
    key = generate_key()
    key_hash = hash_key(key)
    
    license_data = {
        "id": secrets.token_hex(8),
        "name": name,
        "whatsapp": whatsapp,
        "key_hash": key_hash,
        "key_preview": f"{key[:8]}...{key[-4:]}",  # Para exibição
        "used": False,
        "activated_at": None,
        "hwid": None,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=days)).isoformat(),
        "days": days
    }
    
    data = load_licenses()
    data["licenses"].append(license_data)
    save_licenses(data)
    
    console.print(f"\n[bold green]✅ LICENÇA CRIADA COM SUCESSO![/bold green]")
    console.print(f"\n[bold yellow]⚠️ ATENÇÃO: Envie esta chave ao usuário:[/bold yellow]")
    console.print(Panel(f"[bold white]{key}[/bold white]", border_style="green"))
    console.print(f"\n[dim]👤 Usuário: {name}[/dim]")
    console.print(f"[dim]📱 WhatsApp: {whatsapp}[/dim]")
    console.print(f"[dim]📅 Válido por: {days} dias[/dim]")
    console.print(f"[dim]⚠️ A chave só pode ser usada 1 vez![/dim]")

def list_licenses():
    console.print("\n[bold cyan]📋 TODAS AS LICENÇAS[/bold cyan]\n")
    
    data = load_licenses()
    
    if not data["licenses"]:
        console.print("[yellow]Nenhuma licença cadastrada.[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", width=8)
    table.add_column("Nome", width=15)
    table.add_column("WhatsApp", width=15)
    table.add_column("Status", width=12)
    table.add_column("Expira em", width=12)
    table.add_column("Chave", width=18)
    
    for lic in data["licenses"]:
        # Calcular status
        expires = datetime.fromisoformat(lic["expires_at"])
        now = datetime.now()
        days_left = (expires - now).days
        
        if lic["used"]:
            if days_left < 0:
                status = "[red]❌ VENCIDA[/red]"
            elif days_left <= 3:
                status = f"[yellow]⚠️ {days_left}d[/yellow]"
            else:
                status = f"[green]✅ {days_left}d[/green]"
        else:
            status = "[dim]🔒 NÃO USADA[/dim]"
        
        table.add_row(
            lic["id"][:8],
            lic["name"][:15],
            lic["whatsapp"],
            status,
            expires.strftime("%d/%m/%Y"),
            lic["key_preview"]
        )
    
    console.print(table)

def edit_user():
    console.print("\n[bold yellow]✏️ EDITAR USUÁRIO[/bold yellow]\n")
    
    data = load_licenses()
    list_licenses()
    
    if not data["licenses"]:
        return
    
    user_id = Prompt.ask("\nDigite o ID do usuário")
    
    for lic in data["licenses"]:
        if lic["id"].startswith(user_id):
            console.print(f"\n[cyan]Editando: {lic['name']}[/cyan]")
            
            new_name = Prompt.ask("Novo nome", default=lic["name"])
            new_whatsapp = Prompt.ask("Novo WhatsApp", default=lic["whatsapp"])
            
            lic["name"] = new_name
            lic["whatsapp"] = new_whatsapp
            
            save_licenses(data)
            console.print("[green]✅ Usuário atualizado![/green]")
            return
    
    console.print("[red]Usuário não encontrado.[/red]")

def renew_license():
    console.print("\n[bold blue]🔄 RENOVAR LICENÇA[/bold blue]\n")
    
    data = load_licenses()
    list_licenses()
    
    if not data["licenses"]:
        return
    
    user_id = Prompt.ask("\nDigite o ID do usuário")
    
    for lic in data["licenses"]:
        if lic["id"].startswith(user_id):
            console.print(f"\n[cyan]Renovando licença de: {lic['name']}[/cyan]")
            
            days = IntPrompt.ask("Quantos dias adicionar?", default=30)
            
            # Renovar a partir de hoje ou da data de expiração (o que for maior)
            current_expires = datetime.fromisoformat(lic["expires_at"])
            now = datetime.now()
            
            if current_expires > now:
                new_expires = current_expires + timedelta(days=days)
            else:
                new_expires = now + timedelta(days=days)
            
            lic["expires_at"] = new_expires.isoformat()
            lic["days"] = lic.get("days", 0) + days
            
            save_licenses(data)
            console.print(f"[green]✅ Licença renovada! Nova validade: {new_expires.strftime('%d/%m/%Y')}[/green]")
            return
    
    console.print("[red]Usuário não encontrado.[/red]")

def generate_new_key():
    console.print("\n[bold magenta]🔑 GERAR NOVA CHAVE[/bold magenta]\n")
    
    data = load_licenses()
    list_licenses()
    
    if not data["licenses"]:
        return
    
    user_id = Prompt.ask("\nDigite o ID do usuário")
    
    for lic in data["licenses"]:
        if lic["id"].startswith(user_id):
            console.print(f"\n[cyan]Gerando nova chave para: {lic['name']}[/cyan]")
            
            if Confirm.ask("[yellow]Isso invalidará a chave anterior. Continuar?[/yellow]"):
                new_key = generate_key()
                lic["key_hash"] = hash_key(new_key)
                lic["key_preview"] = f"{new_key[:8]}...{new_key[-4:]}"
                lic["used"] = False
                lic["activated_at"] = None
                lic["hwid"] = None
                
                save_licenses(data)
                
                console.print(f"\n[bold green]✅ NOVA CHAVE GERADA![/bold green]")
                console.print(Panel(f"[bold white]{new_key}[/bold white]", border_style="green"))
                console.print("[dim]⚠️ A chave anterior foi invalidada![/dim]")
            return
    
    console.print("[red]Usuário não encontrado.[/red]")

def delete_license():
    console.print("\n[bold red]🗑️ EXCLUIR LICENÇA[/bold red]\n")
    
    data = load_licenses()
    list_licenses()
    
    if not data["licenses"]:
        return
    
    user_id = Prompt.ask("\nDigite o ID do usuário")
    
    for i, lic in enumerate(data["licenses"]):
        if lic["id"].startswith(user_id):
            console.print(f"\n[red]Excluindo: {lic['name']} ({lic['whatsapp']})[/red]")
            
            if Confirm.ask("[bold red]TEM CERTEZA? Esta ação não pode ser desfeita![/bold red]"):
                data["licenses"].pop(i)
                save_licenses(data)
                console.print("[green]✅ Licença excluída![/green]")
            return
    
    console.print("[red]Usuário não encontrado.[/red]")

def main():
    while True:
        choice = show_menu()
        
        if choice == 1:
            create_license()
        elif choice == 2:
            list_licenses()
        elif choice == 3:
            edit_user()
        elif choice == 4:
            renew_license()
        elif choice == 5:
            generate_new_key()
        elif choice == 6:
            delete_license()
        elif choice == 7:
            console.print("\n[dim]Até logo![/dim]")
            break
        
        Prompt.ask("\n[dim]Pressione Enter para continuar...[/dim]")

if __name__ == "__main__":
    main()
