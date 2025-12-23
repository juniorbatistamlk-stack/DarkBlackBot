# debug_bot.py
"""
🔧 BOT DE DIAGNÓSTICO
Testa cada passo para identificar onde está o problema:
1. Conexão com IQ Option
2. Busca de velas
3. Cálculo de indicadores
4. Geração de sinais
5. Envio de ordens
"""
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from config import Config

console = Console()

def step(num, title):
    console.print(f"\n[bold cyan]PASSO {num}: {title}[/bold cyan]")
    console.print("-" * 50)

def ok(msg):
    console.print(f"[green]✅ {msg}[/green]")

def fail(msg):
    console.print(f"[red]❌ {msg}[/red]")

def warn(msg):
    console.print(f"[yellow]⚠️ {msg}[/yellow]")

def info(msg):
    console.print(f"[dim]{msg}[/dim]")

def main():
    console.print(Panel("[bold red]🔧 BOT DE DIAGNÓSTICO IQ OPTION[/bold red]\nIdentifica problemas na execução de trades", style="bold white"))
    
    # =========================================
    step(1, "CONEXÃO COM IQ OPTION")
    # =========================================
    
    cfg = Config()
    cfg.email = Prompt.ask("Email")
    cfg.password = Prompt.ask("Senha", password=True)
    cfg.account_type = "PRACTICE"
    
    info("Tentando conectar...")
    
    from api.iq_handler import IQHandler
    api = IQHandler(cfg)
    
    if api.connect():
        ok(f"Conectado! Saldo: R${api.get_balance():.2f}")
    else:
        fail(f"Falha ao conectar: {api.last_error}")
        return
    
    # =========================================
    step(2, "BUSCA DE VELAS")
    # =========================================
    
    test_pair = "EURUSD-OTC"
    info(f"Buscando 30 velas de {test_pair}...")
    
    candles = api.get_candles(test_pair, 1, 30)
    
    if candles and len(candles) >= 15:
        ok(f"Recebeu {len(candles)} velas")
        last = candles[-1]
        info(f"Última vela: O={last['open']:.5f} H={last['high']:.5f} L={last['low']:.5f} C={last['close']:.5f}")
    else:
        fail(f"Falha ao buscar velas: recebeu {len(candles) if candles else 0}")
        return
    
    # =========================================
    step(3, "CÁLCULO DE INDICADORES")
    # =========================================
    
    from utils.indicators import calculate_ema
    
    ema9 = calculate_ema(candles[:-1], 9)
    ema21 = calculate_ema(candles[:-1], 21)
    
    if ema9 and ema21:
        ok(f"EMA9 = {ema9:.5f}")
        ok(f"EMA21 = {ema21:.5f}")
        
        if ema9 > ema21:
            info("Tendência: ALTA (EMA9 > EMA21)")
        else:
            info("Tendência: BAIXA (EMA9 < EMA21)")
    else:
        fail("Falha ao calcular EMAs")
        return
    
    # =========================================
    step(4, "GERAÇÃO DE SINAIS")
    # =========================================
    
    from strategies.alavancagem import AlavancagemStrategy
    
    strategy = AlavancagemStrategy(api)
    
    # Testar 3 pares
    test_pairs = ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC"]
    found_signal = None
    
    for pair in test_pairs:
        info(f"Testando {pair}...")
        signal, desc = strategy.check_signal(pair, 1)
        
        if signal:
            ok(f"SINAL: {signal} em {pair}")
            info(f"Motivo: {desc}")
            found_signal = (pair, signal, desc)
            break
        else:
            warn(f"Sem sinal: {desc}")
    
    if not found_signal:
        warn("Nenhum sinal encontrado nos pares testados")
        warn("Isso pode significar:")
        warn("  - Mercado lateral/choppy")
        warn("  - Velas muito pequenas")
        warn("  - EMAs cruzando")
        console.print("\n[yellow]Vou forçar um teste de ordem mesmo assim...[/yellow]")
        found_signal = ("EURUSD-OTC", "CALL", "Teste forçado")
    
    # =========================================
    step(5, "ENVIO DE ORDEM (TESTE REAL)")
    # =========================================
    
    pair, signal, desc = found_signal
    amount = 2.0  # R$2 de teste
    
    console.print(f"\n[bold yellow]⚡ ENVIANDO ORDEM DE TESTE:[/bold yellow]")
    info(f"Par: {pair}")
    info(f"Direção: {signal}")
    info(f"Valor: R${amount:.2f}")
    info(f"Timeframe: 1 minuto")
    
    console.print("\n[dim]Chamando API...[/dim]")
    start = time.time()
    
    check, order_id = api.buy(amount, pair, signal, 1)
    
    elapsed = time.time() - start
    info(f"Tempo de resposta: {elapsed:.2f}s")
    
    if check:
        ok(f"ORDEM ACEITA!")
        ok(f"ID: {order_id}")
        
        console.print("\n[yellow]Aguardando resultado (65s)...[/yellow]")
        time.sleep(65)
        
        result = api.check_win(order_id)
        if result > 0:
            ok(f"WIN: +R${result:.2f}")
        elif result < 0:
            fail(f"LOSS: -R${abs(result):.2f}")
        else:
            warn("EMPATE/Sem resultado")
    else:
        fail(f"ORDEM REJEITADA!")
        fail(f"Motivo: {order_id}")
        
        console.print("\n[bold red]DIAGNÓSTICO:[/bold red]")
        
        if "Timeout" in str(order_id):
            warn("A API demorou mais de 30 segundos para responder")
            warn("Possíveis causas:")
            warn("  - Conexão lenta")
            warn("  - Servidor IQ Option sobrecarregado")
            warn("  - Horário de baixa liquidez")
        elif "closed" in str(order_id).lower():
            warn("O par está fechado")
            warn("Tente outro par ou aguarde o mercado abrir")
        elif "amount" in str(order_id).lower():
            warn("Valor de entrada inválido")
            warn("Verifique o valor mínimo para este par")
        else:
            warn(f"Erro desconhecido: {order_id}")
            warn("Verifique se sua conta tem saldo suficiente")
    
    # =========================================
    step(6, "RESUMO")
    # =========================================
    
    console.print("\n[bold cyan]📊 RESULTADO DO DIAGNÓSTICO:[/bold cyan]")
    console.print(f"  • Conexão: {'✅' if api.api.check_connect() else '❌'}")
    console.print(f"  • Velas: {'✅' if candles else '❌'}")
    console.print(f"  • EMAs: {'✅' if ema9 and ema21 else '❌'}")
    console.print(f"  • Sinal: {'✅' if found_signal else '❌'}")
    console.print(f"  • Ordem: {'✅' if check else '❌'}")
    
    console.print("\n[dim]Diagnóstico concluído![/dim]")

if __name__ == "__main__":
    main()
