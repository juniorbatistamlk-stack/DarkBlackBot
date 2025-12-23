# test_strategy6.py
"""
Script de teste para verificar:
1. Se a estratégia 6 está gerando sinais
2. Se a API IQ Option está respondendo
"""
import sys
import os
from config import Config
from api.iq_handler import IQHandler
from strategies.alavancagem import AlavancagemStrategy
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def test_strategy():
    console.print("[bold cyan]🧪 TESTE DA ESTRATÉGIA 6[/bold cyan]\n")
    
    # 1. Login
    cfg = Config()
    cfg.email = os.getenv("IQ_EMAIL") or Prompt.ask("Email")
    cfg.password = os.getenv("IQ_PASSWORD") or Prompt.ask("Senha", password=True)
    cfg.account_type = "PRACTICE"
    
    console.print("\n[yellow]Conectando...[/yellow]")
    api = IQHandler(cfg)
    if not api.connect():
        console.print("[red]❌ Falha ao conectar![/red]")
        return
    
    console.print(f"[green]✅ Conectado! Saldo: R${api.get_balance():.2f}[/green]\n")
    
    # 2. Testar estratégia
    strategy = AlavancagemStrategy(api)
    
    # Pares para testar
    test_pairs = ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC"]
    
    console.print("[bold]📊 TESTANDO SINAIS:[/bold]\n")
    
    for pair in test_pairs:
        console.print(f"[cyan]Par: {pair}[/cyan]")
        
        # Buscar sinal
        signal, desc = strategy.check_signal(pair, 1)
        
        if signal:
            console.print(f"  [green]✅ SINAL: {signal}[/green]")
            console.print(f"  [yellow]📋 {desc}[/yellow]")
            
            # Testar API
            console.print(f"\n[bold yellow]🔧 TESTANDO ENVIO PARA IQ OPTION...[/bold yellow]")
            console.print(f"  Par: {pair}")
            console.print(f"  Direção: {signal}")
            console.print(f"  Valor: R$2.00 (teste)")
            
            # Tentar enviar ordem de teste
            check, order_id = api.buy(2.0, pair, signal, 1)
            
            if check:
                console.print(f"  [bold green]✅ ORDEM ENVIADA COM SUCESSO![/bold green]")
                console.print(f"  [dim]ID: {order_id}[/dim]")
                
                # Aguardar resultado
                console.print(f"\n  [yellow]Aguardando resultado...[/yellow]")
                import time
                time.sleep(65)
                
                result = api.check_win(order_id)
                if result > 0:
                    console.print(f"  [green]🎉 WIN: +R${result:.2f}[/green]")
                elif result < 0:
                    console.print(f"  [red]❌ LOSS: -R${abs(result):.2f}[/red]")
                else:
                    console.print(f"  [yellow]⚖️ EMPATE[/yellow]")
            else:
                console.print(f"  [red]❌ FALHA AO ENVIAR ORDEM[/red]")
                console.print(f"  [red]Erro: {order_id}[/red]")
            
            break  # Testar apenas 1 sinal
        else:
            console.print(f"  [dim]⏳ {desc}[/dim]")
    
    console.print("\n[bold green]✅ Teste concluído![/bold green]")

if __name__ == "__main__":
    test_strategy()
