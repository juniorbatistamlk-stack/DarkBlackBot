#!/usr/bin/env python3
"""
Teste de Paridades e Timeframes
Verifica quais pares aceitam operar em M1, M5, M15 e M30
"""
import time
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import box
import getpass

from api.iq_handler import IQHandler
from config import Config

console = Console()

# Lista completa de pares OTC
ALL_PAIRS = [
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", "NZDUSD-OTC", "USDCHF-OTC",
    "EURJPY-OTC", "GBPJPY-OTC", "AUDJPY-OTC", "CADJPY-OTC", "EURGBP-OTC", "EURCAD-OTC", "EURAUD-OTC", 
    "EURNZD-OTC", "GBPCAD-OTC", "GBPCHF-OTC", "GBPAUD-OTC", "GBPNZD-OTC", "AUDCAD-OTC", "AUDCHF-OTC",
    "AUDNZD-OTC", "CADCHF-OTC", "NZDJPY-OTC", "XAUUSD-OTC"
]

TIMEFRAMES = [1, 5, 15, 30]  # M1, M5, M15, M30

def test_pair_timeframes():
    """Testa cada par em cada timeframe"""
    cfg = Config()
    # Prompt de credenciais se não estiverem configuradas
    if not cfg.email:
        cfg.email = Prompt.ask("Email da IQ Option", default="")
    if not cfg.password:
        try:
            cfg.password = getpass.getpass("Senha da IQ Option: ")
        except Exception:
            cfg.password = Prompt.ask("Senha da IQ Option", default="")
    api = IQHandler(cfg)
    
    console.print("[bold bright_cyan]🔐 Conectando à API IQ Option...[/]", style="on black")
    
    if not api.connect():
        console.print("[bold red]❌ Falha ao conectar[/]", style="on black")
        return
    
    console.print("[bold green]✅ Conectado![/]\n", style="on black")
    
    results = {}
    failed_pairs = []
    valid_pairs = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Testando pares...", total=len(ALL_PAIRS) * len(TIMEFRAMES))
        
        for pair in ALL_PAIRS:
            pair_results = {}
            pair_valid = True
            
            for tf in TIMEFRAMES:
                try:
                    # Tentar buscar 5 velas (teste mínimo)
                    candles = api.get_candles(pair, tf, 5)
                    
                    if candles and len(candles) > 0:
                        pair_results[f"M{tf}"] = "✅"
                    else:
                        pair_results[f"M{tf}"] = "❌"
                        pair_valid = False
                except Exception as e:
                    pair_results[f"M{tf}"] = "❌"
                    pair_valid = False
                
                progress.update(task, advance=1)
                time.sleep(0.2)  # Anti-rate-limit
            
            results[pair] = pair_results
            
            if pair_valid:
                valid_pairs.append(pair)
            else:
                failed_pairs.append(pair)
    
    # Exibir resultados
    console.print("\n[bold bright_cyan]═══════════════════════════════════════════════[/]", style="on black")
    console.print("[bold bright_cyan]RESULTADO DO TESTE DE TIMEFRAMES[/]\n", style="on black")
    
    # Tabela com resultados
    t = Table(box=box.DOUBLE, expand=False)
    t.add_column("Par", justify="left", style="bold white", width=18)
    t.add_column("M1", justify="center", width=6)
    t.add_column("M5", justify="center", width=6)
    t.add_column("M15", justify="center", width=6)
    t.add_column("M30", justify="center", width=6)
    t.add_column("Status", justify="center", width=12)
    
    for pair in sorted(ALL_PAIRS):
        tf_results = results.get(pair, {})
        m1 = tf_results.get("M1", "?")
        m5 = tf_results.get("M5", "?")
        m15 = tf_results.get("M15", "?")
        m30 = tf_results.get("M30", "?")
        
        status = "[bold green]✅ VÁLIDO[/]" if pair in valid_pairs else "[bold red]❌ INVÁLIDO[/]"
        
        t.add_row(pair, m1, m5, m15, m30, status)
    
    console.print(t, style="on black")
    
    # Resumo
    console.print("\n[bold bright_cyan]═══════════════════════════════════════════════[/]", style="on black")
    console.print(f"\n📊 [bold]RESUMO:[/]", style="on black")
    console.print(f"   • Total de pares: [bold white]{len(ALL_PAIRS)}[/]", style="on black")
    console.print(f"   • Válidos (✅): [bold green]{len(valid_pairs)}[/]", style="on black")
    console.print(f"   • Inválidos (❌): [bold red]{len(failed_pairs)}[/]\n", style="on black")
    
    if failed_pairs:
        console.print("[bold red]Pares INVÁLIDOS (remover):[/]", style="on black")
        for pair in failed_pairs:
            console.print(f"   ❌ {pair}", style="on black")
    
    console.print("\n[bold green]Pares VÁLIDOS (manter):[/]", style="on black")
    for pair in valid_pairs:
        console.print(f"   ✅ {pair}", style="on black")
    
    # Gerar código Python para copiar
    console.print("\n[bold bright_cyan]═══════════════════════════════════════════════[/]", style="on black")
    console.print("[bold]Código atualizado para main.py:[/]\n", style="on black")
    
    valid_pairs_str = ", ".join([f'"{p}"' for p in valid_pairs])
    console.print(f"[dim]target_assets = [{valid_pairs_str}][/]", style="on black")
    
    api.disconnect()

if __name__ == "__main__":
    try:
        test_pair_timeframes()
    except KeyboardInterrupt:
        console.print("\n[yellow]Teste cancelado pelo usuário[/]", style="on black")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Erro: {e}[/]", style="on black")
        sys.exit(1)
