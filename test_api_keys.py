# test_api_keys.py
"""
Testa se as APIs estão funcionando corretamente:
1. IQ Option API
2. OpenRouter AI API (se configurada)
"""
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def test_iq_option():
    console.print("\n[bold cyan]1. TESTANDO IQ OPTION API[/bold cyan]")
    console.print("-" * 40)
    
    from config import Config
    from api.iq_handler import IQHandler
    
    cfg = Config()
    cfg.email = Prompt.ask("Email IQ Option")
    cfg.password = Prompt.ask("Senha", password=True)
    cfg.account_type = "PRACTICE"
    
    console.print("[yellow]Conectando...[/yellow]")
    api = IQHandler(cfg)
    
    if api.connect():
        balance = api.get_balance()
        console.print(f"[green]✅ IQ Option: CONECTADO[/green]")
        console.print(f"[green]   Saldo: R${balance:.2f}[/green]")
        return True
    else:
        console.print(f"[red]❌ IQ Option: FALHOU[/red]")
        console.print(f"[red]   Erro: {api.last_error}[/red]")
        return False

def test_openrouter():
    console.print("\n[bold cyan]2. TESTANDO OPENROUTER AI API[/bold cyan]")
    console.print("-" * 40)
    
    try:
        from utils.ai_analyzer import AIAnalyzer
        
        # Tentar criar o analyzer
        ai = AIAnalyzer()
        
        # Testar uma request simples
        console.print("[yellow]Testando IA...[/yellow]")
        
        # Verificar se tem API key configurada
        if hasattr(ai, 'client') and ai.client:
            console.print(f"[green]✅ OpenRouter: CONFIGURADO[/green]")
            return True
        else:
            console.print(f"[yellow]⚠️ OpenRouter: Não configurado (opcional)[/yellow]")
            return True
            
    except Exception as e:
        console.print(f"[yellow]⚠️ OpenRouter: {e}[/yellow]")
        return True  # IA é opcional

def test_license():
    console.print("\n[bold cyan]3. TESTANDO SISTEMA DE LICENÇA[/bold cyan]")
    console.print("-" * 40)
    
    try:
        from utils.security import LicenseValidator
        
        validator = LicenseValidator()
        valid, days, msg = validator.validate_license()
        
        if valid:
            console.print(f"[green]✅ Licença: VÁLIDA ({days} dias restantes)[/green]")
        else:
            console.print(f"[red]❌ Licença: {msg}[/red]")
        
        return valid
        
    except Exception as e:
        console.print(f"[yellow]⚠️ Licença: {e}[/yellow]")
        return False

def main():
    console.print("[bold]🔧 TESTE DE APIs DO ANTIGRAVITY[/bold]\n")
    
    # 1. IQ Option
    iq_ok = test_iq_option()
    
    # 2. OpenRouter
    ai_ok = test_openrouter()
    
    # 3. Licença
    license_ok = test_license()
    
    # Resumo
    console.print("\n" + "=" * 40)
    console.print("[bold]RESUMO:[/bold]")
    console.print(f"  IQ Option: {'✅' if iq_ok else '❌'}")
    console.print(f"  OpenRouter: {'✅' if ai_ok else '⚠️'}")
    console.print(f"  Licença: {'✅' if license_ok else '❌'}")
    console.print("=" * 40)
    
    if iq_ok and license_ok:
        console.print("\n[bold green]✅ Tudo funcionando! Bot pronto para operar.[/bold green]")
    else:
        console.print("\n[bold red]❌ Corrija os erros acima antes de operar.[/bold red]")

if __name__ == "__main__":
    main()
