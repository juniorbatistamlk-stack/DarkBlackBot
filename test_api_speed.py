"""
Teste de diagnóstico - Verificar tempo de resposta da API
"""
import sys
import time
sys.path.insert(0, '.')

from api.iq_handler import IQHandler
from config import Config
from rich.prompt import Prompt
from rich.console import Console

console = Console()

def main():
    cfg = Config()
    
    console.print("[bold cyan]🔧 TESTE DE VELOCIDADE DA API[/bold cyan]\n")
    
    cfg.email = Prompt.ask("Email")
    cfg.password = Prompt.ask("Senha", password=True)
    
    console.print("\n[yellow]Conectando...[/yellow]")
    api = IQHandler(cfg)
    
    if not api.connect():
        console.print("[red]Falha na conexão![/red]")
        return
    
    console.print("[green]✓ Conectado![/green]\n")
    
    # Teste 1: get_all_open_time
    console.print("[bold]Teste 1: get_all_open_time()[/bold]")
    start = time.time()
    try:
        result = api.api.get_all_open_time()
        elapsed = time.time() - start
        console.print(f"  ✓ OK em {elapsed:.2f}s")
        
        # Verificar EURUSD
        if "turbo" in result and "EURUSD" in result["turbo"]:
            is_open = result["turbo"]["EURUSD"].get("open", False)
            console.print(f"  EURUSD turbo: {'ABERTO' if is_open else 'FECHADO'}")
        else:
            console.print(f"  EURUSD turbo: NÃO ENCONTRADO")
            
        if "binary" in result and "EURUSD" in result["binary"]:
            is_open = result["binary"]["EURUSD"].get("open", False)
            console.print(f"  EURUSD binary: {'ABERTO' if is_open else 'FECHADO'}")
        else:
            console.print(f"  EURUSD binary: NÃO ENCONTRADO")
            
    except Exception as e:
        elapsed = time.time() - start
        console.print(f"  ✗ ERRO em {elapsed:.2f}s: {e}")
    
    # Teste 2: get_all_profit
    console.print("\n[bold]Teste 2: get_all_profit()[/bold]")
    start = time.time()
    try:
        result = api.api.get_all_profit()
        elapsed = time.time() - start
        console.print(f"  ✓ OK em {elapsed:.2f}s")
        if "EURUSD" in result:
            console.print(f"  EURUSD payout: {result['EURUSD']}")
    except Exception as e:
        elapsed = time.time() - start
        console.print(f"  ✗ ERRO em {elapsed:.2f}s: {e}")
    
    console.print("\n[bold green]Diagnóstico completo![/bold green]")

if __name__ == "__main__":
    main()
