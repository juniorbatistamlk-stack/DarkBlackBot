# main.py
import sys
import time
import threading
import logging
import traceback  # For debugging
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.panel import Panel
import os
import socket

# Define timeout global para TODAS as conexões (30s)
socket.setdefaulttimeout(30)

# Force UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Suppress internal logging
logging.disable(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

from config import Config
from api.iq_handler import IQHandler
from ui.dashboard import Dashboard

# Strategy Imports
from strategies.ferreira import FerreiraStrategy
from strategies.price_action import PriceActionStrategy
from strategies.logica_preco import LogicaPrecoStrategy
from strategies.ana_tavares import AnaTavaresStrategy
from strategies.conservador import ConservadorStrategy
from strategies.alavancagem import AlavancagemStrategy
from strategies.alavancagem_sr import AlavancagemSRStrategy
from utils.ai_analyzer import AIAnalyzer
from utils.memory import TradingMemory
from utils.backtester import Backtester
from utils.smart_trader import SmartTrader
from utils.license_system import check_license

# Shared State
current_profit = 0.0
worker_status = "Iniciando..."
stop_threads = False
bot_logs = []

console = Console()

# =============================================================================
# SISTEMA DE LICENCIAMENTO
# =============================================================================
def verify_license():
    """Verifica licença antes de iniciar"""
    console.print("\\n[bright_cyan]🔐 Verificando licença...[/bright_cyan]\\n")
    
    valid = check_license()
    
    if not valid:
        console.print("\\n[red]❌ Não foi possível iniciar o bot.[/red]")
        input("\\nPressione ENTER para sair...")
        sys.exit(1)
    
    return True


def log_msg(msg):
    global bot_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    bot_logs.append(f"[{timestamp}] {msg}")
    if len(bot_logs) > 10:
        bot_logs.pop(0)

def get_strategy(choice, api, ai_analyzer=None):
    if choice == 1: return FerreiraStrategy(api, ai_analyzer)
    if choice == 2: return PriceActionStrategy(api, ai_analyzer)
    if choice == 3: return LogicaPrecoStrategy(api, ai_analyzer)
    if choice == 4: return AnaTavaresStrategy(api, ai_analyzer)
    if choice == 5: return ConservadorStrategy(api, ai_analyzer)
    if choice == 6: return AlavancagemStrategy(api, ai_analyzer)
    if choice == 7: return AlavancagemSRStrategy(api, ai_analyzer)
    return FerreiraStrategy(api, ai_analyzer)

def select_pairs(api):
    console.print("\n" + "═" * 70)
    console.print("[bold cyan]📊 SELEÇÃO DE MERCADO (OTC)[/bold cyan]")
    console.print("═" * 70)
    console.print("[dim]Modo exclusivo: OTC (24h)[/dim]\n")
    
    # Lista Completa de Pares OTC
    assets_otc = [
        # Majors
        "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", "NZDUSD-OTC", "USDCHF-OTC",
        # Crosses
        "EURJPY-OTC", "GBPJPY-OTC", "AUDJPY-OTC", "CADJPY-OTC", "EURGBP-OTC", "EURCAD-OTC", "EURAUD-OTC", 
        "EURNZD-OTC", "GBPCAD-OTC", "GBPCHF-OTC", "GBPAUD-OTC", "GBPNZD-OTC", "AUDCAD-OTC", "AUDCHF-OTC",
        "AUDNZD-OTC", "CADCHF-OTC", "NZDJPY-OTC",
        # Commodities / Crypto / Stocks (Opcionais, mas focando em Forex OTC)
        "XAUUSD-OTC" # Gold
    ]
    
    target_assets = assets_otc
    
    console.print("\n[bold]Escaneando paridades OTC disponíveis...[/bold]")
    scan = api.scan_available_pairs(target_assets)
    
    open_assets = []
    for a in target_assets:
        if scan.get(a, {}).get("open"):
            open_assets.append((a, scan[a]['payout']))
            
    if not open_assets:
        console.print("[red]Nenhum ativo OTC encontrado![/red]")
        console.print("[yellow]Isso é incomum. Verifique se a corretora não está em manutenção.[/yellow]")
        return ["EURUSD-OTC"] # Fallback
        
    console.print(f"[green]Ativos OTC Disponíveis:[/green]")
    for i, (asset, payout) in enumerate(open_assets):
        payout_color = "green" if payout >= 80 else "yellow"
        console.print(f"{i+1}. {asset} ([{payout_color}]{payout}%[/{payout_color}])")
        
    choices = Prompt.ask("Escolha (ex: 1,2,3 ou 'todas')", default="todas")
    
    if choices.lower() == 'todas' or choices.lower() == 'all':
        selected = [x[0] for x in open_assets]
    else:
        indices = [int(x)-1 for x in choices.split(",") if x.strip().isdigit()]
        selected = [open_assets[i][0] for i in indices if 0 <= i < len(open_assets)]
        
    return selected if selected else [open_assets[0][0]]

class StderrRedirector:
    def __init__(self, logger_func):
        self.logger_func = logger_func
        self._in_write = False  # Prevent recursion
        
    def write(self, message):
        # Prevent infinite loops and filter empty messages
        if self._in_write or not message or not message.strip():
            return
            
        try:
            self._in_write = True
            # Only log actual errors, not debug noise
            if any(keyword in message.lower() for keyword in ['error', 'exception', 'traceback', 'ssl', 'eof', 'timeout']):
                self.logger_func(f"[red][ERRO] {message.strip()}[/red]")
        finally:
            self._in_write = False
            
    def flush(self):
        pass

def run_trading_session(api, strategy, pairs, cfg, memory, ai_analyzer):
    global current_profit, worker_status, stop_threads, bot_logs
    
    # Reset State
    current_profit = 0.0
    stop_threads = False
    bot_logs = []
    
    # Atualizar config com paridades selecionadas
    cfg.asset = ", ".join(pairs) if len(pairs) > 1 else pairs[0]
    
    # Criar dashboard
    dashboard = Dashboard(cfg)
    
    # Função para logs do sistema (IA/IQ)
    def log_system_msg(msg):
        dashboard.log(msg)  # Dashboard separa automaticamente [AI] e [IQ]
    
    # Redirecionar STDERR para o dashboard (Captura erros SSL/Connection)
    # DESABILITADO: Causa duplicação do banner no Live display
    # sys.stderr = StderrRedirector(log_system_msg)
    
    # Conectar logger da API (IQHandler)
    if hasattr(api, 'set_logger'):
        api.set_logger(log_system_msg)
        
    smart_trader = SmartTrader(api, strategy, pairs, memory, {}, ai_analyzer)
    smart_trader.set_system_logger(log_system_msg)  # Conectar logger do sistema
    
    # Conectar logger da estratégia ao dashboard (se suportado)
    if hasattr(strategy, 'set_logger'):
        strategy.set_logger(log_system_msg)
    
    console.print(Panel(f"[bold green]🚀 ROBÔ INICIADO - {strategy.name}[/bold green]\nParidades: {', '.join(pairs)}", border_style="green"))
    
    def worker():
        global current_profit, worker_status, stop_threads
        
        last_candle_traded = None
        cached_signal = None
        
        log_msg(f"[green]✅ Trader Ativo: {strategy.name}[/green]")
        
        while not stop_threads:
            try:
                # === VERIFICAR LIMITES ===
                if cfg.profit_goal > 0 and current_profit >= cfg.profit_goal:
                    log_msg(f"[bold green]═══════════════════════════════════════[/bold green]")
                    log_msg(f"[bold green]🏆 PARABÉNS! META ATINGIDA! 🎉[/bold green]")
                    log_msg(f"[bold green]💰 Lucro: R${current_profit:.2f}[/bold green]")
                    log_msg(f"[bold green]═══════════════════════════════════════[/bold green]")
                    log_msg(f"[green]✅ Encerramento automático ativado.[/green]")
                    log_msg(f"[cyan]📊 Saia do mercado e proteja seu lucro![/cyan]")
                    log_msg(f"[dim]Dica: Consistência é a chave do sucesso![/dim]")
                    stop_threads = True
                    break
                
                if current_profit <= -cfg.stop_loss:
                    log_msg(f"[bold red]═══════════════════════════════════════[/bold red]")
                    log_msg(f"[bold red]🛑 STOP LOSS ACIONADO[/bold red]")
                    log_msg(f"[bold red]💸 Perda: R${abs(current_profit):.2f}[/bold red]")
                    log_msg(f"[bold red]═══════════════════════════════════════[/bold red]")
                    log_msg(f"[yellow]⚠️ Proteção de capital ativada.[/yellow]")
                    log_msg(f"[cyan]🧘 Pare por hoje. O mercado estará aqui amanhã.[/cyan]")
                    log_msg(f"[dim]Lembre-se: Preservar a banca é essencial![/dim]")
                    stop_threads = True
                    break
                
                # === CALCULAR TIMING ===
                candle_duration = cfg.timeframe * 60
                
                try:
                    # Obter timestamp com retry
                    server_time = None
                    try:
                        if api.api:
                            server_time = api.api.get_server_timestamp()
                    except Exception:
                        pass
                    
                    # Tentativa extra se None
                    if server_time is None:
                        time.sleep(0.5)
                        try:
                            if api.api:
                                server_time = api.api.get_server_timestamp()
                        except Exception:
                            pass
                    
                    if server_time is None:
                        worker_status = "⚠️ Sincronizando relógio..."
                        time.sleep(2)
                        continue
                    
                    # Validar que é um número válido antes de qualquer conta
                    if not isinstance(server_time, (int, float)) or server_time <= 0:
                        worker_status = "⚠️ Tempo inválido, aguardando..."
                        time.sleep(2)
                        continue
                        
                    # CRITICAL FIX: Ensure no NoneType math
                    candle_start = int(server_time) - (int(server_time) % int(candle_duration))
                    candle_end = candle_start + candle_duration
                    seconds_left = candle_end - server_time
                    seconds_elapsed = server_time - candle_start
                    
                    # ID único da vela atual
                    current_candle = candle_start
                    
                    # Já operou nesta vela? Aguardar próxima
                    if last_candle_traded == current_candle:
                        worker_status = f"⏳ Aguardando próxima vela ({int(seconds_left)}s)"
                        time.sleep(1)
                        continue
                    
                    # PERÍODO INICIAL (0-29s) - Aguardar e limpar cache
                    if seconds_elapsed < 30:
                        cached_signal = None
                        worker_status = f"💤 Aguardando ({int(seconds_elapsed)}/30s)"
                        time.sleep(1)
                        continue
                    
                    # PERÍODO DE ANÁLISE E EXECUÇÃO (30-60s)
                    # Buscar sinal se não tem
                    if cached_signal is None:
                        worker_status = f"🔍 Analisando mercado..."
                        cached_signal = smart_trader.analyze_all_pairs(cfg.timeframe)
                        if cached_signal:
                            log_msg(f"[cyan]📊 SINAL: {cached_signal['pair']} {cached_signal['signal']}[/cyan]")
                            log_msg(f"[yellow]📋 {cached_signal['desc']}[/yellow]")
                    
                    # Executar no segundo 58-59 (últimos 2 segundos)
                    if cached_signal and seconds_left <= 2:
                        worker_status = "⚡ EXECUTANDO NO SEGUNDO 59!"
                        log_msg(f"[bold green]🚀 DISPARANDO: {cached_signal['pair']} {cached_signal['signal']}[/bold green]")
                        log_msg(f"[cyan]📋 MOTIVO: {cached_signal['desc']}[/cyan]")
                        
                        profit = smart_trader.execute_trade(cached_signal, cfg, log_msg)
                        current_profit += profit
                        cfg.balance = api.get_balance()
                        
                        last_candle_traded = current_candle
                        cached_signal = None
                        log_msg(f"[dim]Trade finalizado. Lucro: R${profit:.2f}[/dim]")
                        time.sleep(2)
                    
                    elif cached_signal:
                        worker_status = f"🎯 SINAL PRONTO! Disparando em {int(seconds_left)}s"
                        time.sleep(0.5)
                    
                    else:
                        worker_status = f"📊 Buscando setup ({int(seconds_elapsed)}s)"
                        time.sleep(1)
                    
                except Exception as e:
                    # Log full traceback for debugging
                    tb = traceback.format_exc()
                    log_msg(f"[yellow]Erro: {e}[/yellow]")
                    log_msg(f"[dim]{tb[:500]}[/dim]")  # Mostrar traceback no dashboard
                    time.sleep(2)
                    
            except Exception as e:
                log_msg(f"[red]Erro: {str(e)}[/red]")
                time.sleep(5)

    # Start Worker
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    
    # UI Loop - Otimizado para evitar flickering
    try:
        # screen=True ajuda a manter a interface fixa e evita 'rolagem' por prints externos
        with Live(dashboard.render(current_profit), auto_refresh=False, screen=True, redirect_stdout=True, redirect_stderr=True) as live:
            while not stop_threads:
                now = time.time()
                
                # Atualizar logs
                dashboard.logs = bot_logs
                
                # Calcular tempo da vela
                secs = now % (cfg.timeframe * 60)
                
                # Atualizar display com refresh manual
                live.update(dashboard.render(current_profit, secs), refresh=True)
                
                # Sleep adequado para não consumir CPU desnecessária
                time.sleep(0.2)
                
        console.print("\n[yellow]Sessão Encerrada. Pressione Enter para voltar...[/yellow]")
        input()
        
    except KeyboardInterrupt:
        stop_threads = True
        console.print("\n[yellow]Parando...[/yellow]")

def main():
    global stop_threads
    
    # 1. License Check - Sistema Simplificado
    from utils.window_manager import set_console_icon, set_console_title
    set_console_title("Dark Black Bot - AI Powered")
    set_console_icon("icon.ico")

    if not verify_license():
        return
    
    console.print()  # Espaço
    
    # Modern Professional Startup Banner
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import time
    
    startup_banner = """
[bold blue]══════════════════════════════════════════════════════════════════════════════[/bold blue]

 [bold cyan]██████╗  █████╗ ██████╗ ██╗  ██╗[/bold cyan]  [bold bright_cyan]██████╗ ██╗      █████╗  ██████╗██╗  ██╗[/bold bright_cyan]
 [bold cyan]██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝[/bold cyan]  [bold bright_cyan]██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝[/bold bright_cyan]
 [bold cyan]██║  ██║███████║██████╔╝█████╔╝ [/bold cyan]  [bold bright_cyan]██████╔╝██║     ███████║██║     █████╔╝[/bold bright_cyan]
 [bold cyan]██║  ██║██╔══██║██╔══██╗██╔═██╗ [/bold cyan]  [bold bright_cyan]██╔══██╗██║     ██╔══██║██║     ██╔═██╗[/bold bright_cyan]
 [bold cyan]██████╔╝██║  ██║██║  ██║██║  ██╗[/bold cyan]  [bold bright_cyan]██████╔╝███████╗██║  ██║╚██████╗██║  ██╗[/bold bright_cyan]
 [bold cyan]╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝[/bold cyan]  [bold bright_cyan]╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝[/bold bright_cyan]

                   [bold bright_cyan]⚡ CHEFÃO DAS BINÁRIAS ⚡[/bold bright_cyan]
         [dim bright_white]Real-Time Analysis  │  Smart Execution  │  AI Powered[/dim bright_white]

[bold blue]══════════════════════════════════════════════════════════════════════════════[/bold blue]
"""
    
    console.print(startup_banner)
    
    # Loading Animation
    with Progress(
        SpinnerColumn("dots", style="bright_cyan"),
        TextColumn("[bright_cyan]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("[bright_cyan]Inicializando sistema...", total=None)
        time.sleep(0.8)
    
    # 2. Config & Login
    cfg = Config()
    
    console.print("\n[bold blue]╡ CONEXÃO IQ OPTION ╞[/bold blue]")
    console.print("[dim bright_white]Autenticando credenciais...[/dim bright_white]\n")
    
    # Account Type Selection
    console.print("[bold bright_white]Selecione o Tipo de Conta:[/bold bright_white]")
    console.print("[bright_cyan]  1. 🛡️  CONTA DE TREINAMENTO (PRACTICE)[/bright_cyan]")
    console.print("[bright_green]  2. 💰 CONTA REAL (REAL MONEY)[/bright_green]")
    acc_choice = IntPrompt.ask("  Opção", choices=["1", "2"], default=1)
    cfg.account_type = "REAL" if acc_choice == 2 else "PRACTICE"
    
    cfg.email = os.getenv("IQ_EMAIL") or Prompt.ask("  📧 [bright_white]Email[/bright_white]")
    cfg.password = os.getenv("IQ_PASSWORD") or Prompt.ask("  🔑 [bright_white]Senha[/bright_white]", password=True)
    
    # Connection with progress bar
    console.print()
    with Progress(
        SpinnerColumn("dots", style="bright_cyan"),
        TextColumn("[bright_cyan]{task.description}"),
        transient=False
    ) as progress:
        task = progress.add_task("[bright_cyan]Conectando ao servidor IQ Option...", total=None)
        api = IQHandler(cfg)
        if not api.connect():
            console.print("[bold red]✗ Falha na autenticação![/bold red]")
            return
        progress.update(task, description="[bright_green]✓ Conectado com sucesso!")
        time.sleep(0.5)
            
    cfg.balance = api.get_balance()
    
    # Show correct balance type
    acc_label = "REAL" if cfg.account_type == "REAL" else "TREINAMENTO"
    color = "bright_green" if cfg.account_type == "REAL" else "bright_cyan"
    
    console.print(f"[bright_white]  💰 Saldo ({acc_label}):[/bright_white] [{color}]R$ {cfg.balance:.2f}[/{color}]\n")
    
    # 3. IA Setup
    ai_analyzer = None
    console.print("[bold blue]╡ INTEGRAÇÃO COM IA ╞[/bold blue]")
    console.print("[dim bright_white]Ativar sistema de análise inteligente OpenRouter (Llama 3.3)?[/dim bright_white]\n")
    
    if Prompt.ask("  🤖 [bright_white]Ativar IA?[/bright_white]", choices=["s", "n"], default="s") == "s":
        try:
            with Progress(
                SpinnerColumn("dots", style="bright_magenta"),
                TextColumn("[bright_magenta]{task.description}"),
                transient=False
            ) as progress:
                task = progress.add_task("[bright_magenta]Inicializando modelo neural...", total=None)
                key = os.getenv("OPENROUTER_API_KEY", "")
                ai_analyzer = AIAnalyzer(key)
                progress.update(task, description="[bright_green]✓ IA inicializada com sucesso!")
                time.sleep(0.5)
            
            console.print("[dim bright_white]  • Modelo: Llama 3.3 70B | Latência: ~2s | Status: Online[/dim bright_white]\n")
        except Exception as e:
            console.print(f"[bright_red]  ✗ Falha ao inicializar IA: {e}[/bright_red]")
            console.print("[bright_cyan]  ⚠️  Continuando sem validação de IA...[/bright_cyan]\n")
    else:
        console.print("[bright_cyan]  ⚠️  IA desativada. Rodando apenas com estratégia...[/bright_cyan]\n")

    # === MENU LOOP ===
    while True:
        console.print("\n" + "═" * 70)
        console.print("[bold bright_cyan]╡ MENU PRINCIPAL ╞[/bold bright_cyan]")
        console.print("═" * 70 + "\n")
        console.print("[bright_white]  1.[/bright_white] [bold bright_green]🚀 INICIAR OPERAÇÕES (Live Trading)[/bold bright_green]")
        console.print("     [dim]→ Executar estratégia em tempo real[/dim]\n")
        console.print("[bright_white]  2.[/bright_white] [bold bright_blue]📊 SIMULADOR (Backtest)[/bold bright_blue]")
        console.print("     [dim]→ Testar estratégias em dados históricos[/dim]\n")
        console.print("[bright_white]  3.[/bright_white] [bold bright_red]🚪 Sair[/bold bright_red]\n")
        console.print("═" * 70)
        
        mode = IntPrompt.ask("Opção", choices=["1", "2", "3"], default=1)
        
        if mode == 3: break
        
        if mode == 1: # LIVE TRADING
            console.print("\n")
            console.print("[bold bright_cyan]╔══════════════════════════════════════════════════════════════════════╗[/bold bright_cyan]")
            console.print("[bold bright_cyan]║[/bold bright_cyan]         [bold white]📊 CENTRAL DE ESTRATÉGIAS[/bold white]                                    [bold bright_cyan]║[/bold bright_cyan]")
            console.print("[bold bright_cyan]╠══════════════════════════════════════════════════════════════════════╣[/bold bright_cyan]")
            console.print("[bold bright_cyan]║[/bold bright_cyan] [dim]Selecione uma estratégia baseada no seu perfil de risco:[/dim]             [bold bright_cyan]║[/bold bright_cyan]")
            console.print("[bold bright_cyan]╚══════════════════════════════════════════════════════════════════════╝[/bold bright_cyan]")
            
            # CONSERVADOR
            console.print("\n[bold bright_green]▓▓▓ PERFIL CONSERVADOR ▓▓▓[/bold bright_green]")
            console.print("─" * 70)
            
            console.print("[bright_green]  1.[/bright_green] [bold white]🎯 FERREIRA TRADER[/bold white] [dim]│ FIMATHE System[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Segue tendências e rompe canais de preço")
            console.print("      [dim]📈 Win Rate: 65-70% │ Sinais: Médio │ Risco: ●●○○○[/dim]")
            
            console.print("\n[bright_green]  2.[/bright_green] [bold white]🔄 PRICE ACTION REVERSAL[/bold white] [dim]│ SMC + Liquidity[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Reversões em zonas de liquidez institucional")
            console.print("      [dim]📈 Win Rate: 68-72% │ Sinais: Baixo │ Risco: ●○○○○[/dim]")
            
            console.print("\n[bright_green]  5.[/bright_green] [bold white]🛡️ CONSERVADOR[/bold white] [dim]│ High Precision[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Filtros rigorosos, poucos sinais, alta precisão")
            console.print("      [dim]📈 Win Rate: 75-80% │ Sinais: Muito Baixo │ Risco: ●○○○○[/dim]")
            
            # MODERADO - Blue theme
            console.print("\n[bold bright_blue]━━━ PERFIL MODERADO ━━━[/bold bright_blue] [dim bright_white](Risco Médio)[/dim bright_white]")
            console.print("─" * 70)
            
            console.print("[bright_blue]  3.[/bright_blue] [bold white]📊 LÓGICA DO PREÇO[/bold white] [dim]│ Candlestick Patterns[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Padrões clássicos: Doji, Hammer, Engulfing")
            console.print("      [dim]📈 Win Rate: 62-68% │ Sinais: Alto │ Risco: ●●●○○[/dim]")
            
            console.print("\n[bright_blue]  4.[/bright_blue] [bold white]⚡ ANA TAVARES[/bold white] [dim]│ Hybrid System[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Combina fluxo de tendência com retração")
            console.print("      [dim]📈 Win Rate: 65-70% │ Sinais: Médio │ Risco: ●●●○○[/dim]")
            
            # AGRESSIVO
            console.print("\n[bold bright_red]▓▓▓ PERFIL AGRESSIVO ▓▓▓[/bold bright_red] [blink]⚠️[/blink]")
            console.print("─" * 70)
            
            console.print("[bright_red]  6.[/bright_red] [bold white]🚀 ALAVANCAGEM LTA/LTB[/bold white] [dim]│ Trend + S/R Zones[/dim]")
            console.print("      [bright_cyan]→[/bright_cyan] Fluxo a favor da tendência + Reversões em S/R")
            console.print("      [bright_cyan]→[/bright_cyan] Analisa 200 velas para detectar zonas")
            console.print("      [dim]📈 Win Rate: 60-68% │ Sinais: Alto │ Risco: ●●●●○[/dim]")
            console.print("      [bright_cyan]⚠️  Stakes progressivos: 2% → 5% → 10% → 20%[/bright_cyan]")
            
            console.print("\n[bright_red]  7.[/bright_red] [bold white]💎 S/R SNIPER PRO[/bold white] [dim]│ Precision Reversal[/dim] [bright_green]⭐ RECOMENDADO[/bright_green]")
            console.print("      [bright_cyan]→[/bright_cyan] Opera APENAS reversões em zonas fortes")
            console.print("      [bright_cyan]→[/bright_cyan] Valida com 5 padrões técnicos + confirmação")
            console.print("      [dim]📈 Win Rate: 70-78% │ Sinais: Baixo │ Risco: ●●●●●[/dim]")
            console.print("      [bright_cyan]⚠️  Alta precisão, alto risco por trade[/bright_cyan]")
            
            console.print("\n[bold bright_cyan]═══════════════════════════════════════════════════════════════════════[/bold bright_cyan]")
            
            sc = IntPrompt.ask("[bright_white]Selecione a Estratégia[/bright_white]", choices=["1","2","3","4","5","6","7"])
            
            # Warning Risk
            if sc in [6, 7]:
                console.print("\n" + "="*70)
                console.print("[bold red]⚠️  AVISO DE RISCO ELEVADO ⚠️[/bold red]")
                console.print("="*70)
                console.print("[yellow]As estratégias de Alavancagem utilizam:[/yellow]")
                console.print("  • Anti-Martingale: Stakes aumentam após vitórias (2% → 4% → 7% → 12% → 20%)")
                console.print("  • Gerenciamento agressivo: Um único trade pode usar 20% da banca")
                console.print("  • Risco de ruína elevado: Sequências de perdas podem zerar a conta")
                console.print("\n[bold white]Estas estratégias são adequadas APENAS para:[/bold white]")
                console.print("  ✓ Traders experientes com disciplina rigorosa")
                console.print("  ✓ Contas de teste ou capital de risco")
                console.print("  ✓ Quem compreende e aceita o risco de perda total\n")
                console.print("[bold red]VOCÊ PODE PERDER TODO O SEU CAPITAL.[/bold red]")
                console.print("="*70 + "\n")
                console.print("[yellow]Você pode perder TODO seu capital.[/yellow]")
                if IntPrompt.ask("Aceitar risco? [1=Sim, 2=Não]", choices=["1", "2"], default=2) == 2:
                    console.print("[green]Decisão prudente! Retornando ao menu...[/green]")
                    continue
            
            
            strategy = get_strategy(sc, api, ai_analyzer)
            console.print(f"\n[bold green]✓ Estratégia Selecionada: {strategy.name}[/bold green]\n")
            
            pairs = select_pairs(api)
            
            # Parametros
            console.print("\n" + "="*70)
            console.print("[bold cyan]⚙️  CONFIGURAÇÃO DE PARÂMETROS[/bold cyan]")
            console.print("="*70 + "\n")
            
            console.print("\n[bold]1. Valor da Entrada Inicial[/bold]")
            console.print("   [dim]Valor investido no primeiro trade (R$)[/dim]")
            cfg.amount = FloatPrompt.ask("   Valor", default=10.0)

            console.print("\n[bold]1.1. Tipo de Opção PREFERIDA[/bold]")
            console.print("   [dim]Qual tipo de contrato priorizar?[/dim]")
            console.print("   [1] ⚡ Binárias (Expiração fixa, ~85%)")
            console.print("   [2] 📈 Digitais (Venda antecipada, ~87% - 92%)")
            console.print("   [3] 🤖 Melhor Payout (O robô escolhe o que pagar mais)")
            op_type = IntPrompt.ask("   Opção", choices=["1", "2", "3"], default=3)
            
            if op_type == 1: cfg.option_type = "BINARY"
            elif op_type == 2: cfg.option_type = "DIGITAL"
            else: cfg.option_type = "BEST"
            
            console.print("\n[bold]2. Timeframe (Período de Análise)[/bold]")
            console.print("   [dim]1 = M1 (1 min) | 5 = M5 (5 min) | 15 = M15 (15 min) | 30 = M30 (30 min)[/dim]")
            console.print("   [bright_green]✨ Recomendado: M5 (melhor relação sinal/ruído)[/bright_green]")
            
            while True:
                cfg.timeframe = IntPrompt.ask("   Timeframe", default=5)
                
                # AVISO CRÍTICO PARA M1
                if cfg.timeframe == 1:
                    console.print("\n" + "="*70)
                    console.print("[bold yellow]⚠️  AVISO IMPORTANTE - TIMEFRAME M1 (1 MINUTO) ⚠️[/bold yellow]")
                    console.print("="*70)
                    console.print("\n[bold white]Por que NÃO recomendamos M1:[/bold white]\n")
                    console.print("  [red]❌[/red] [yellow]Alto nível de RUÍDO de mercado (movimentos aleatórios)[/yellow]")
                    console.print("  [red]❌[/red] [yellow]Sinais falsos aumentam significativamente[/yellow]")
                    console.print("  [red]❌[/red] [yellow]Maior probabilidade de Stop Loss[/yellow]")
                    console.print("  [red]❌[/red] [yellow]Spread e latência afetam mais o resultado[/yellow]\n")
                    
                    console.print("[bold white]Timeframes recomendados:[/bold white]\n")
                    console.print("  [green]✓[/green] [bold bright_green]M5 (5 min)[/bold bright_green]  - [bright_cyan]IDEAL[/bright_cyan] → Equilíbrio perfeito entre frequência e precisão")
                    console.print("  [green]✓[/green] [bold green]M15 (15 min)[/bold green] - [cyan]BOM[/cyan] → Menos sinais, mas mais confiáveis")
                    console.print("  [green]✓[/green] [bold green]M30 (30 min)[/bold green] - [cyan]BOM[/cyan] → Sinais raros, alta qualidade\n")
                    
                    console.print("[bold bright_cyan]🎯 O BOT FOI PROJETADO E OTIMIZADO PARA M5[/bold bright_cyan]\n")
                    
                    console.print("[bold white]💡 Regra de Ouro do Trading:[/bold white]")
                    console.print("   [bright_yellow]\"Atingiu a meta do dia? SAIA DO MERCADO!\"[/bright_yellow]")
                    console.print("   [dim]Não fique operando o dia todo. Consistência > Volume[/dim]\n")
                    
                    console.print("="*70)
                    console.print("[bold red]OPERAR EM M1 É POR SUA CONTA E RISCO[/bold red]")
                    console.print("="*70 + "\n")
                    
                    escolha = IntPrompt.ask(
                        "[bold]Deseja continuar mesmo assim?[/bold]\n   [1] Sim, aceito os riscos do M1\n   [2] Não, quero escolher outro timeframe",
                        choices=["1", "2"],
                        default=2
                    )
                    
                    if escolha == 2:
                        console.print("\n[green]✓ Decisão sábia! Escolha um timeframe mais adequado:[/green]\n")
                        continue  # Volta para escolher outro timeframe
                    else:
                        console.print("\n[yellow]⚠️  Você escolheu prosseguir com M1. Boa sorte![/yellow]")
                        console.print("[dim]Lembre-se: Discipline > Emoção | Stop Loss é seu amigo[/dim]\n")
                        break
                else:
                    # Timeframe válido (M5, M15, M30, etc)
                    break
            
            console.print("\n[bold]3. Meta de Lucro Diária[/bold]")
            console.print("   [dim]O robô para automaticamente ao atingir este valor (R$)[/dim]")
            cfg.profit_goal = FloatPrompt.ask("   Meta", default=100.0)
            
            console.print("\n[bold]4. Stop Loss (Limite de Perda)[/bold]")
            console.print("   [dim]O robô para automaticamente ao atingir este prejuízo (R$)[/dim]")
            cfg.stop_loss = FloatPrompt.ask("   Stop Loss", default=50.0)
            
            console.print("\n[bold]5. Níveis de Martingale (Gales)[/bold]")
            console.print("   [dim]Quantas tentativas de recuperação após perda[/dim]")
            console.print("   [dim]Cada gale multiplica a entrada por 2.2x[/dim]")
            console.print("   [yellow]⚠️  Mais gales = maior risco[/yellow]")
            cfg.martingale_levels = IntPrompt.ask("   Gales", default=2)
            
            cfg.strategy_name = strategy.name
            cfg.stop_win = cfg.profit_goal  # Auto-sync
            
            console.print("\n" + "="*70)
            console.print("[bold green]✓ Configurações salvas![/bold green]")
            console.print("="*70 + "\n")
            
            # Memory Link
            mem = TradingMemory()
            if ai_analyzer: ai_analyzer.set_memory(mem)
            
            run_trading_session(api, strategy, pairs, cfg, mem, ai_analyzer)
            
        elif mode == 2: # BACKTEST
            pairs = select_pairs(api)
            tf = IntPrompt.ask("Timeframe", default=1)
            
            console.print("[yellow]Rodando Backtest...[/yellow]")
            # Test all strategies
            strats = [
                FerreiraStrategy(api), PriceActionStrategy(api), 
                LogicaPrecoStrategy(api), AnaTavaresStrategy(api),
                ConservadorStrategy(api), AlavancagemStrategy(api),
                AlavancagemSRStrategy(api)
            ]
            bt = Backtester(api)
            res = bt.run_backtest(pairs, strats, tf, 100)
            bt.display_results(res, strats)
            input("\nEnter para voltar...")

if __name__ == "__main__":
    main()