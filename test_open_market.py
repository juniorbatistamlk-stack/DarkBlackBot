"""
Teste de diagnóstico para verificar se o mercado aberto está funcionando
"""
import sys
sys.path.insert(0, '.')

from api.iq_handler import IQHandler
from config import Config
from rich.prompt import Prompt
from rich.console import Console
import time

console = Console()

def main():
    cfg = Config()
    
    console.print("[bold cyan]🔧 TESTE DE MERCADO ABERTO[/bold cyan]\n")
    
    cfg.email = Prompt.ask("Email")
    cfg.password = Prompt.ask("Senha", password=True)
    
    console.print("\n[yellow]Conectando...[/yellow]")
    api = IQHandler(cfg)
    
    if not api.connect():
        console.print("[red]Falha na conexão![/red]")
        return
    
    console.print("[green]✓ Conectado![/green]\n")
    
    # Testar diferentes pares
    test_pairs = ["EURUSD", "EURUSD-OTC"]
    
    for pair in test_pairs:
        console.print(f"\n[bold]Testando: {pair}[/bold]")
        
        # 1. Verificar se está aberto
        try:
            all_assets = api.api.get_all_open_time()
            
            is_open_binary = False
            is_open_turbo = False
            
            if "binary" in all_assets and pair in all_assets["binary"]:
                is_open_binary = all_assets["binary"][pair].get("open", False)
                
            if "turbo" in all_assets and pair in all_assets["turbo"]:
                is_open_turbo = all_assets["turbo"][pair].get("open", False)
                
            console.print(f"  Binária: {'✓ Aberto' if is_open_binary else '✗ Fechado'}")
            console.print(f"  Turbo: {'✓ Aberto' if is_open_turbo else '✗ Fechado'}")
            
        except Exception as e:
            console.print(f"  [red]Erro ao verificar status: {e}[/red]")
        
        # 2. Tentar pegar payout
        try:
            profits = api.api.get_all_profit()
            if pair in profits:
                payout = profits[pair]
                console.print(f"  Payout: {payout}")
            else:
                console.print(f"  [yellow]Payout não encontrado[/yellow]")
        except Exception as e:
            console.print(f"  [red]Erro payout: {e}[/red]")
    
    console.print("\n[bold green]Diagnóstico completo![/bold green]")
    console.print("\nSe EURUSD mostra 'Fechado' para Turbo e Binária,")
    console.print("significa que o mercado aberto não está disponível agora.")
    console.print("Use OTC para operar.")

if __name__ == "__main__":
    main()
