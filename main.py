# main.py
import sys
import time
import threading
import logging
import traceback
import os
import socket
from datetime import datetime

# External Libs
from rich.console import Console
from rich.align import Align
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markup import escape
from rich.text import Text
from rich import box
from rich.padding import Padding
from rich.console import Group
from dotenv import load_dotenv

# Internal Modules
from config import Config
from api.iq_handler import IQHandler
from ui.dashboard import Dashboard
from ui.cli_style import header_panel, menu_table, info_kv, print_panel, title_panel, section
from utils.ai_analyzer import AIAnalyzer
from utils.memory import TradingMemory
from utils.backtester import Backtester
from utils.smart_trader import SmartTrader
from utils.license_system import check_license
from utils.window_manager import set_console_icon, set_console_title

# Strategies
from strategies.ferreira import FerreiraStrategy
from strategies.price_action import PriceActionStrategy
from strategies.logica_preco import LogicaPrecoStrategy
from strategies.ana_tavares import AnaTavaresStrategy
from strategies.conservador import ConservadorStrategy
from strategies.alavancagem import AlavancagemStrategy
from strategies.alavancagem_sr import AlavancagemSRStrategy

# =============================================================================
# SETUP GLOBAL
# =============================================================================
load_dotenv()

# Timeout global para conexões (30s)
socket.setdefaulttimeout(30)

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Suppress internal logging
logging.disable(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

console = Console(style="white on black")


def black_spacer(lines: int = 1) -> None:
    """Imprime linhas preenchidas com fundo preto para evitar faixas cinzas no terminal."""
    try:
        width = max(1, int(console.size.width))
    except Exception:
        width = 120
    for _ in range(max(0, int(lines))):
        console.print(" " * width, style="on black")

# Shared State
current_profit = 0.0
worker_status = "Iniciando..."
stop_threads = False
bot_logs = []

def verify_license():
    """Verifica licença antes de iniciar"""
    console.print(Align.center("[dim]🔐 Verificando autenticidade...[/dim]"), style="on black")
    if not check_license():
        console.print("[red]❌ Não foi possível iniciar o bot. Licença inválida.[/red]", style="on black")
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    return True

def log_msg(msg):
    global bot_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    bot_logs.append(f"[{timestamp}] {msg}")
    if len(bot_logs) > 10:
        bot_logs.pop(0)

def get_strategy(choice, api, ai_analyzer=None):
    strategies = {
        1: FerreiraStrategy,
        2: PriceActionStrategy,
        3: LogicaPrecoStrategy,
        4: AnaTavaresStrategy,
        5: ConservadorStrategy,
        6: AlavancagemStrategy,
        7: AlavancagemSRStrategy
    }
    strategy_cls = strategies.get(choice, FerreiraStrategy)
    return strategy_cls(api, ai_analyzer)

def select_pairs(api):
    from rich import box
    from rich.table import Table

    # print_panel(console, header_panel("Seleção de Mercado • OTC 24h")) -> REMOVIDO
    # console.print(Align.center("[bold white]SELEÇÃO DE MERCADO OTC[/]"))
    print_panel(console, title_panel("SELEÇÃO DE MERCADO OTC", "OTC 24h", border_style="bright_cyan"))
    
    # Lista Completa de Pares OTC (modo normal)
    target_assets = [
        "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", "NZDUSD-OTC", "USDCHF-OTC",
        "EURJPY-OTC", "GBPJPY-OTC", "AUDJPY-OTC", "CADJPY-OTC", "EURGBP-OTC", "EURCAD-OTC", "EURAUD-OTC", 
        "EURNZD-OTC", "GBPCAD-OTC", "GBPCHF-OTC", "GBPAUD-OTC", "GBPNZD-OTC", "AUDCAD-OTC", "AUDCHF-OTC",
        "AUDNZD-OTC", "CADCHF-OTC", "NZDJPY-OTC", "XAUUSD-OTC"
    ]
    
    black_spacer(1)
    console.print("[dim]Escaneando paridades OTC disponíveis...[/dim]", style="on black")
    scan = api.scan_available_pairs(target_assets)
    
    open_assets = []
    for a in target_assets:
        if scan.get(a, {}).get("open"):
            open_assets.append((a, scan[a]['payout']))
            
    if not open_assets:
        print_panel(console, info_kv(
            "OTC",
            [("Status", "[bold bright_red]Nenhum ativo OTC encontrado[/]"), ("Dica", "[dim]Verifique se a corretora está online.[/]")],
            border_style="bright_cyan",
        ))
        return ["EURUSD-OTC"] # Fallback

    # Lista com linhas divisórias
    t = Table(box=box.MINIMAL, expand=True, show_lines=True)
    t.style = "on black"
    t.add_column("#", justify="center", style="dim", width=4)
    t.add_column("Ativo", justify="center", style="bold white")
    t.add_column("Payout", justify="center")
    for i, (asset, payout) in enumerate(open_assets):
        p_color = "bright_green" if payout >= 80 else "bright_magenta" if payout >= 70 else "white"
        t.add_row(str(i + 1), asset, f"[{p_color}]{payout:.0f}%[/]")

    # Cabeçalho da lista simples
    console.print(Align.center(f"[dim]Total: {len(open_assets)} ativos encontrados[/dim]"), style="on black")
    # print_panel(console, info_kv("Lista", [("Ativos", "")], border_style="white")) -> REMOVIDO
    console.print(t, style="on black")
    console.rule(style="dim on black") # Fechamento visual sutil
        
    choices = Prompt.ask("Escolha (ex: 1,2,3 ou 'todas')", default="todas")
    
    if choices.lower() in ['todas', 'all']:
        selected = [x[0] for x in open_assets]
    else:
        indices = [int(x)-1 for x in choices.split(",") if x.strip().isdigit()]
        selected = [open_assets[i][0] for i in indices if 0 <= i < len(open_assets)]
        
    return selected if selected else [open_assets[0][0]]

def run_trading_session(api, strategy, pairs, cfg, memory, ai_analyzer):
    global current_profit, worker_status, stop_threads, bot_logs
    
    current_profit = 0.0
    stop_threads = False
    bot_logs = []
    
    cfg.asset = ", ".join(pairs) if len(pairs) > 1 else pairs[0]
    dashboard = Dashboard(cfg)
    
    def log_system_msg(msg):
        dashboard.log(msg)
    
    # Conectando loggers
    if hasattr(api, 'set_logger'): api.set_logger(log_system_msg)
        
    smart_trader = SmartTrader(api, strategy, pairs, memory, {}, ai_analyzer)
    smart_trader.set_system_logger(log_system_msg)

    # Conectar logger da IA ao painel do sistema (se existir)
    if ai_analyzer and hasattr(ai_analyzer, 'set_logger'):
        ai_analyzer.set_logger(log_system_msg)
        dashboard.log("[AI] ✅ IA conectada ao painel")
    elif not ai_analyzer:
        dashboard.log("[AI] ⚠️ IA desativada nesta sessão")
    
    if hasattr(strategy, 'set_logger'): strategy.set_logger(log_system_msg)
    
    console.print(
        Panel(
            f"[bold green]🚀 ROBÔ INICIADO - {strategy.name}[/bold green]\nParidades: {', '.join(pairs)}",
            border_style="green",
            style="on black",
            expand=True,
        ),
        style="on black",
    )
    
    def worker():
        global current_profit, worker_status, stop_threads
        last_candle_traded = None
        cached_signal = None

        failed_pairs_this_candle = set()
        
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
                
                # Obter timestamp seguro com tratamento de erro
                try:
                    server_time = api.get_server_timestamp()
                except Exception:
                    # Se falhar (desconexão/sync), força None para cair na validação abaixo
                    server_time = 0
                
                # Sincronização básica
                if server_time <= 0:
                    worker_status = "⚠️ Sincornizando relógio..."
                    time.sleep(1)
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
                
                # Resetar blacklist quando muda a vela
                if last_candle_traded != current_candle and seconds_elapsed < 2:
                    failed_pairs_this_candle.clear()
                
                # Já operou nesta vela? Aguardar próxima
                if last_candle_traded == current_candle:
                    worker_status = f"⏳ Aguardando próxima vela ({int(seconds_left)}s)"
                    time.sleep(1)
                    continue
                
                # OTIMIZAÇÃO DE IA (ECONOMIA DE TOKENS)
                # M1: Analisa nos últimos 15s | M5+: Analisa no último 45s (mais sinais)
                ai_window = 15 if cfg.timeframe == 1 else 45
                
                if seconds_left > ai_window:
                    cached_signal = None
                    wait_t = int(seconds_left - ai_window)
                    worker_status = f"⏳ Aguardando Janela IA | M{cfg.timeframe} ({wait_t}s)"
                    time.sleep(1)
                    continue
                
                # PERÍODO DE ANÁLISE E EXECUÇÃO (30-60s)
                # Buscar sinal se não tem
                if cached_signal is None:
                    worker_status = f"🔍 Analisando {len(pairs)} pares..."
                    analysis_start = time.time()
                    try:
                        cached_signal = smart_trader.analyze_all_pairs(cfg.timeframe, exclude_pairs=failed_pairs_this_candle)
                    except Exception as e:
                        analysis_elapsed = time.time() - analysis_start
                        log_msg(f"[yellow]⚠️ Erro na análise ({analysis_elapsed:.1f}s): {str(e)[:50]}[/yellow]")
                        cached_signal = None
                    
                    analysis_elapsed = time.time() - analysis_start
                    if cached_signal:
                        log_msg(f"[cyan]📊 SINAL: {cached_signal['pair']} {cached_signal['signal']} ({analysis_elapsed:.1f}s)[/cyan]")
                        log_msg(f"[yellow]📋 {escape(str(cached_signal.get('desc', '')))}[/yellow]")
                    elif analysis_elapsed > 20:
                        log_msg(f"[yellow]⏱️ Análise demorou {analysis_elapsed:.1f}s - pode haver gargalo[/yellow]")

                # ARMAR no último 2s e EXECUTAR no segundo 59 (1s antes da virada).
                # Motivo: Antecipar a virada para pegar a abertura exata.
                arm_window = 2.0
                open_window = 5.0 # Janela permissiva para delay

                if cached_signal and (0 < seconds_left <= arm_window):
                    worker_status = "⏱️ SINAL ARMADO! Aguardando ponto de disparo (59s)..."

                    # Espera server-side até segundo 59 (1s antes do fim)
                    target_turn = candle_end - 1
                    while True:
                        try:
                            now_ts = api.get_server_timestamp()
                        except Exception:
                            now_ts = 0
                        if isinstance(now_ts, (int, float)) and now_ts >= target_turn:
                            break
                        time.sleep(0.05)

                    # Confirmar que estamos dentro da janela inicial da nova vela
                    try:
                        now_ts = api.get_server_timestamp()
                    except Exception:
                        now_ts = 0

                    if not isinstance(now_ts, (int, float)) or now_ts <= 0:
                        worker_status = "⚠️ Tempo inválido na virada. Abortando entrada."
                        cached_signal = None
                        time.sleep(0.5)
                        continue

                    new_elapsed = now_ts - target_turn
                    if not (0.0 <= new_elapsed <= open_window):
                        worker_status = f"⛔ Perdeu a virada ({new_elapsed:.2f}s). Abortando entrada."
                        cached_signal = None
                        time.sleep(0.5)
                        continue

                    worker_status = "⚡ EXECUTANDO (abertura da nova vela)!"
                    log_msg(f"[bold green]🚀 DISPARANDO: {cached_signal['pair']} {cached_signal['signal']}[/bold green]")
                    log_msg(f"[cyan]📋 MOTIVO: {escape(str(cached_signal.get('desc', '')))}[/cyan]")
                    
                    profit = smart_trader.execute_trade(cached_signal, cfg, log_msg)

                    # Se a ordem NÃO abriu (ex: ativo indisponível), não travar a vela inteira.
                    # Marca o par como falho nesta vela e tenta outro setup.
                    if not getattr(smart_trader, 'last_order_opened', False):
                        failed_pairs_this_candle.add(cached_signal.get('pair'))
                        cached_signal = None
                        worker_status = "⚠️ Ordem não abriu. Tentando outro ativo..."
                        time.sleep(0.5)
                        continue

                    # Ordem abriu: atualizar saldo e marcar a vela como operada.
                    current_profit += profit
                    cfg.balance = api.get_balance()
                    
                    last_candle_traded = current_candle
                    cached_signal = None
                    log_msg(f"[dim]Trade finalizado. Lucro: R${profit:.2f}[/dim]")
                    time.sleep(2)
                
                elif cached_signal:
                    worker_status = f"🎯 SINAL PRONTO! Disparando quando faltar 1s ({int(seconds_left)}s)"
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
                # VS Code terminal pode piscar com refresh muito agressivo
                time.sleep(0.35)
                
        console.print("\n[yellow]Sessão Encerrada. Pressione Enter para voltar...[/yellow]", style="on black")
        input()
        
    except KeyboardInterrupt:
        stop_threads = True
        console.print("\n[yellow]Parando...[/yellow]", style="on black")

def main():
    global stop_threads
    
    # 1. License Check - Sistema Simplificado
    if not verify_license():
        return
    
    # Set window title and icon AFTER console is ready
    import time
    from utils.window_manager import set_console_icon, set_console_title
    set_console_title("Dark Black Bot - AI Powered")
    time.sleep(0.1)  # Small delay to ensure console is ready
    set_console_icon("icon.ico")
    
    # Evitar "faixas" cinzas: imprimir espaçador com fundo preto
    black_spacer(1)

    # Cabeçalho limpo (apenas espaço)
    # print_panel(console, header_panel("v3.5 • Smart Execution • AI Assisted")) -> REMOVIDO PARA LIMPEZA
    
    # Modern Professional Startup Banner
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import time
    
    startup_banner = """
[bold bright_white]DARK[/][bold white]BLACK[/] [bold bright_magenta]AI[/]
[dim]Professional Trading Intelligence[/dim]
"""
    
    # Banner com fundo 100% preto (sem áreas cinzas fora do texto)
    banner_text = Text.from_markup(startup_banner.strip("\n"), justify="center")
    console.print(Align.center(banner_text), style="on black")
    black_spacer(1)
    
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
    
    print_panel(console, title_panel("CONEXÃO IQ OPTION", border_style="bright_cyan"))

    print_panel(
        console,
        menu_table(
            "TIPO DE CONTA",
            [
                ("1", "TREINAMENTO (PRACTICE)", "Modo seguro para testar configurações"),
                ("2", "CONTA REAL", "Use apenas com gestão e disciplina"),
            ],
            border_style="bright_magenta",
        ),
    )
    
    acc_choice = IntPrompt.ask("  Opção", choices=["1", "2"], default=1)
    cfg.account_type = "REAL" if acc_choice == 2 else "PRACTICE"
    
    cfg.email = os.getenv("IQ_EMAIL") or Prompt.ask("  📧 [bright_white]Email[/bright_white]")
    cfg.password = os.getenv("IQ_PASSWORD") or Prompt.ask("  🔑 [bright_white]Senha[/bright_white]", password=True)

    api = None
    try:
        # Connection with progress bar
        black_spacer(1)
        with Progress(
            SpinnerColumn("dots", style="bright_cyan"),
            TextColumn("[bright_cyan]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[bright_cyan]Conectando ao servidor IQ Option...", total=None)
            api = IQHandler(cfg)
            if not api.connect():
                console.print(Padding("[bold red]✗ Falha na autenticação![/bold red]", (0,0), style="on black", expand=True))
                return
            time.sleep(1.5)
            
        console.print(Padding("[bright_green]✓ Conectado com sucesso![/bright_green]", (0,0), style="on black", expand=True))
            
        cfg.balance = api.get_balance()
        
        # Show correct balance type
        # Show correct balance type
        acc_label = "REAL" if cfg.account_type == "REAL" else "TREINAMENTO"
        color = "bright_green" if cfg.account_type == "REAL" else "bright_cyan"
        
        console.print(Padding(f"[bright_white]  💰 Saldo ({acc_label}):[/bright_white] [{color}]R$ {cfg.balance:.2f}[/{color}]", (0,0), style="on black", expand=True))
        black_spacer(1)
        
        # 3. IA Setup
        ai_analyzer = None
        print_panel(console, title_panel("INTEGRAÇÃO COM IA", "Validação inteligente de entradas", border_style="bright_cyan"))
        black_spacer(1)
        console.print(Padding("  [dim]Validação inteligente de entradas com contexto gráfico.[/dim]", (0,0), style="on black", expand=True))
        
        # 1. Carregar configuração atual
        current_key = os.getenv("AI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
        current_provider = os.getenv("AI_PROVIDER", "openrouter")
        
        # Se achou chave específica antiga, tenta deduzir o provider
        if not os.getenv("AI_API_KEY"):
            if os.getenv("GROQ_API_KEY"): current_provider = "groq"
            elif os.getenv("GEMINI_API_KEY"): current_provider = "gemini"
        
        should_configure = False
        use_ai = "n"

        if current_key:
            display_prov = current_provider.upper() if current_provider else "IA"
            console.print(Padding(f"[dim]Configuração detectada: {display_prov}[/dim]", (0,0), style="on black", expand=True))
            
            print_panel(
                console,
                menu_table(
                    "IA • Opções",
                    [
                        ("1", f"Usar {display_prov}", "Manter a chave atual"),
                        ("2", "Configurar novo", "Inserir e validar uma nova API Key"),
                        ("3", "Desativar", "Continuar sem validação de IA"),
                    ],
                    border_style="bright_magenta",
                ),
            )
            
            action = Prompt.ask(
                "  🤖 [bright_white]Escolha uma opção[/bright_white]", 
                choices=["1", "2", "3"], 
                default="1"
            )
            
            if action == "2":
                should_configure = True
            elif action == "1":
                use_ai = "s"
            else: # action == "3"
                use_ai = "n"
        else:
            console.print(Padding("[yellow]Nenhuma chave de IA detectada.[/yellow]", (0,0), style="on black", expand=True))
            if Prompt.ask("  🤖 [bright_white]Deseja configurar a IA agora?[/bright_white]", choices=["s", "n"], default="s") == "s":
                should_configure = True

        # SETUP WIZARD
        if should_configure:
            black_spacer(1)
            black_spacer(1)
            print_panel(
                console,
                menu_table(
                    "Escolha o Provedor",
                    [
                        ("1", "OpenRouter", "Padrão • Llama 3.3"),
                        ("2", "Groq", "Ultra rápido • Llama 3"),
                        ("3", "Gemini", "Google • Flash 1.5"),
                    ],
                    border_style="bright_cyan",
                ),
            )
            
            p_map = {"1": "openrouter", "2": "groq", "3": "gemini"}
            choice = Prompt.ask("Opção", choices=["1", "2", "3"], default="1")
            current_provider = p_map[choice]
            
            while True:
                black_spacer(1)
                console.print(Padding(f"[bold]Cole sua API Key do {current_provider.upper()}:[/bold]", (0,0), style="on black", expand=True))
                console.print(Padding("[dim](Clique com botão direito para colar | ENTER para cancelar)[/dim]", (0,0), style="on black", expand=True))
                input_key = Prompt.ask("API Key", password=True)
                
                if not input_key:
                    should_configure = False
                    use_ai = "n"
                    break
                    
                input_key = input_key.strip()
                
                input_key = input_key.strip()
                
                console.print(Padding("\n[dim]Validando chave... aguarde[/dim]", (0,0), style="on black", expand=True))
                try:
                    # Validar chave antes de salvar
                    temp_analyzer = AIAnalyzer(input_key, provider=current_provider)
                    is_valid, msg = temp_analyzer.check_connection()
                    
                    if is_valid:
                        current_key = input_key
                        # Salvar no arquivo .env
                        try:
                            with open(".env", "a") as f:
                                f.write(f"\nAI_PROVIDER={current_provider}\nAI_API_KEY={current_key}\n")
                            os.environ["AI_PROVIDER"] = current_provider
                            os.environ["AI_API_KEY"] = current_key
                            console.print(Padding(f"[green]✓ Chave válida ({msg})! Configuração salva.[/green]\n", (0,0), style="on black", expand=True))
                            use_ai = "s"
                            break
                        except:
                            console.print(Padding("[red]Erro ao salvar .env (usando apenas nesta sessão)[/red]", (0,0), style="on black", expand=True))
                            use_ai = "s"
                            break
                    else:
                        console.print(Padding(f"[bold red]❌ CHAVE INVÁLIDA: {msg}[/bold red]", (0,0), style="on black", expand=True))
                        if Prompt.ask("Deseja tentar novamente?", choices=["s", "n"], default="s") == "n":
                            should_configure = False
                            use_ai = "n"
                            break
                except Exception as e:
                    console.print(Padding(f"[red]Erro na validação: {e}[/red]", (0,0), style="on black", expand=True))
                    if Prompt.ask("Deseja tentar novamente?", choices=["s", "n"], default="s") == "n":
                        use_ai = "n"
                        break

        if use_ai == "s" and current_key:
            try:
                with Progress(
                    SpinnerColumn("dots", style="bright_magenta"),
                    TextColumn("[bright_magenta]{task.description}"),
                    transient=True
                ) as progress:
                    task = progress.add_task(f"[bright_magenta]Conectando ao {current_provider.upper()}...", total=None)
                    ai_analyzer = AIAnalyzer(current_key, provider=current_provider)
                    time.sleep(1.5)
                
                console.print(Padding("[bright_green]✓ IA inicializada com sucesso![/bright_green]", (0,0), style="on black", expand=True))
                console.print(Padding(f"  [dim]Modelo: {ai_analyzer.model} | Status: Online[/dim]", (0,0), style="on black", expand=True))
            except Exception as e:
                console.print(Padding(f"\n[red]Erro ao conectar IA: {e}[/red]\n", (0,0), style="on black", expand=True))
                ai_analyzer = None
                console.print(Padding(f"[bright_red]  ✗ Falha ao inicializar IA: {e}[/bright_red]", (0,0), style="on black", expand=True))
                console.print(Padding("[bright_cyan]  ⚠️  Continuando sem validação de IA...[/bright_cyan]\n", (0,0), style="on black", expand=True))
        else:
            console.print(Padding("[dim]IA desativada para esta sessão.[/dim]\n", (0,0), style="on black", expand=True))

        # === MENU LOOP ===
        while True:
            print_panel(console, title_panel("MENU PRINCIPAL", border_style="white"))

            print_panel(
                console,
                menu_table(
                    "Escolha uma Ação",
                    [
                        ("1", "Iniciar Operações (Live Trading)", "Operar em tempo real (OTC)"),
                        ("2", "Simulador (Backtest)", "Testar estratégias com dados históricos"),
                        ("3", "Sair", "Encerrar com segurança"),
                    ],
                    border_style="bright_cyan",
                ),
            )
            
            mode = IntPrompt.ask("Opção", choices=["1", "2", "3"], default=1)
            
            if mode == 3: break
            
            if mode == 1: # LIVE TRADING
                from rich.table import Table

                strategies_table = Table(box=box.DOUBLE, expand=True, show_lines=True)
                strategies_table.style = "on black"
                strategies_table.add_column("#", justify="right", style="dim", width=4)
                strategies_table.add_column("Estratégia", style="bold white")
                strategies_table.add_column("Perfil", style="bright_cyan", width=16)
                strategies_table.add_column("Resumo", style="dim")

                strategies_table.add_row(
                    "1",
                    "🎯 FERREIRA TRADER",
                    "CONSERVADOR",
                    "Tendência + canais | WR: 65-70% | Sinais: Médio | Risco: ●●○○○",
                )
                strategies_table.add_row(
                    "2",
                    "🔄 PRICE ACTION REVERSAL",
                    "CONSERVADOR",
                    "Reversão em liquidez/SR | WR: 68-72% | Sinais: Baixo | Risco: ●○○○○",
                )
                strategies_table.add_row(
                    "3",
                    "📊 LÓGICA DO PREÇO",
                    "MODERADO",
                    "Candlestick | WR: 62-68% | Sinais: Alto | Risco: ●●●○○",
                )
                strategies_table.add_row(
                    "4",
                    "⚡ ANA TAVARES RETRACTION",
                    "MODERADO",
                    "Tendência + retração | WR: 65-70% | Sinais: Médio | Risco: ●●●○○",
                )
                strategies_table.add_row(
                    "5",
                    "🛡️ CONSERVADOR HIGH PRECISION",
                    "MODERADO",
                    "Ultra seletivo | WR: 75-80% | Sinais: Muito baixo | Risco: ●○○○○",
                )
                strategies_table.add_row(
                    "6",
                    "🧨 ALAVANCAGEM LTA/LTB",
                    "AGRESSIVO",
                    "Tendência + S/R | WR: 60-68% | Sinais: Alto | Risco: ●●●●○",
                )

                print_panel(console, title_panel("CENTRAL DE ESTRATÉGIAS", "Escolha seu perfil", border_style="bright_cyan"))

                strat_content = Group(
                    Text("Conservador • Moderado • Agressivo", style="dim"),
                    strategies_table,
                )
                print_panel(console, section("Estratégias Disponíveis", strat_content, border_style="bright_cyan"))
                
                sc = IntPrompt.ask("[bright_white]Selecione a Estratégia (1-6)[/bright_white]", choices=["1","2","3","4","5","6"])
                
                # Warning Risk
                if sc == 6:
                    risk_rows = [
                        ("Stakes", "[bold bright_magenta]Progressivos[/] (2% → 5% → 10% → 20%)"),
                        ("Gestão", "[bold]Agressiva[/] (até 20% da banca em 1 trade)"),
                        ("Risco", "[bold bright_red]Ruína elevada[/] em sequência de perdas"),
                        ("Ideal", "[dim]Traders experientes • Conta teste • Capital de risco[/]"),
                    ]
                    print_panel(console, info_kv(
                        "⚠️ Aviso de Risco Elevado",
                        risk_rows,
                        border_style="bright_red",
                    ))
                    if IntPrompt.ask("Aceitar risco? [1=Sim, 2=Não]", choices=["1", "2"], default=2) == 2:
                        console.print("[green]Decisão prudente! Retornando ao menu...[/green]", style="on black")
                        continue
                
                
                # Estratégia 6: escolher perfil de filtros/sinais
                if sc == 6:
                    print_panel(console, title_panel("ESTRATÉGIA 6 • MODO DE OPERAÇÃO", border_style="bright_red"))

                    print_panel(
                        console,
                        menu_table(
                            "Modo de Operação",
                            [
                                ("1", "Normal (Seletivo)", "Mais filtros • Menos sinais"),
                                ("2", "Flexível (Mais sinais)", "Menos filtros • Mais oportunidades"),
                                ("3", "Pitbull Bravo (Ultra agressivo)", "Máximo volume • Alto risco"),
                            ],
                            border_style="bright_red",
                        ),
                    )
                    mode_choice = IntPrompt.ask("Opção", choices=["1", "2", "3"], default=1)
                    
                    if mode_choice == 3:
                        cfg.alavancagem_mode = "PITBULL"
                    elif mode_choice == 2:
                        cfg.alavancagem_mode = "FLEX"
                    else:
                        cfg.alavancagem_mode = "NORMAL"

                    strategy = AlavancagemStrategy(api, ai_analyzer, mode=cfg.alavancagem_mode)
                else:
                    strategy = get_strategy(sc, api, ai_analyzer)
                print_panel(console, title_panel("RESUMO DA SELEÇÃO", border_style="white"))
                summary_rows = [("Estratégia", f"[cyan]{strategy.name}[/cyan]")]
                if sc == 6:
                    summary_rows.append(("Modo", f"{getattr(cfg, 'alavancagem_mode', '—')}"))
                print_panel(console, info_kv("Seleção", summary_rows, border_style="bright_cyan"))
                
                pairs = select_pairs(api)
                
                # Parametros
                print_panel(console, title_panel("CONFIGURAÇÃO DE PARÂMETROS", border_style="bright_magenta"))
                console.print(Padding("[dim]  Defina entrada, timeframe e gerenciamento.[/dim]", (0,0), style="on black", expand=True))
                
                console.print("\n[bold]1. Valor da Entrada Inicial[/bold]", style="on black")
                console.print(Padding("   [dim]Valor investido no primeiro trade (R$)[/dim]", (0,0), style="on black", expand=True))
                cfg.amount = FloatPrompt.ask("   Valor", default=10.0)

                console.print("\n[bold white]1. TIPO DE OPÇÃO[/]", style="on black") # Subtitulo simples
                
                op_menu = Group(
                    Text("  [1] ⚡ Binárias (Expiração fixa)"),
                    Text("  [2] 📈 Digitais (Payout variável)"),
                    Text("  [3] 🤖 Melhor Payout (Auto)")
                )
                console.print(Padding(op_menu, (0,0), style="on black", expand=True))
                op_type = IntPrompt.ask("   Opção", choices=["1", "2", "3"], default=3)
                
                if op_type == 1: cfg.option_type = "BINARY"
                elif op_type == 2: cfg.option_type = "DIGITAL"
                else: cfg.option_type = "BEST"
                
                console.print("\n[bold]2. Timeframe (Período de Análise)[/bold]", style="on black")
                console.print("   [dim]1 = M1 (1 min) | 5 = M5 (5 min) | 15 = M15 (15 min) | 30 = M30 (30 min)[/dim]", style="on black")
                console.print("   [bright_green]✨ Recomendado: M5 (melhor relação sinal/ruído)[/bright_green]", style="on black")
                
                while True:
                    cfg.timeframe = IntPrompt.ask("   Timeframe", default=5)
                    
                    # AVISO CRÍTICO PARA M1
                    if cfg.timeframe == 1:
                        warn_rows = [
                            ("Ruído", "[dim]Movimentos aleatórios e entradas falsas[/]"),
                            ("Latência", "[dim]Spread e atraso impactam mais o resultado[/]"),
                            ("Recomendado", "[bold bright_cyan]M5[/] • M15 • M30"),
                            ("Nota", "[bold bright_red]M1 é por sua conta e risco[/]"),
                        ]
                        print_panel(console, info_kv(
                            "⚠️ Aviso Importante (M1)",
                            warn_rows,
                            border_style="bright_magenta",
                        ))
                        
                        escolha = IntPrompt.ask(
                            "[bold]Deseja continuar mesmo assim?[/bold]\n   [1] Sim, aceito os riscos do M1\n   [2] Não, quero escolher outro timeframe",
                            choices=["1", "2"],
                            default=2
                        )
                        
                        if escolha == 2:
                            console.print("\n[green]✓ Decisão sábia! Escolha um timeframe mais adequado:[/green]\n", style="on black")
                            continue  # Volta para escolher outro timeframe
                        else:
                            console.print("\n[yellow]⚠️  Você escolheu prosseguir com M1. Boa sorte![/yellow]", style="on black")
                            console.print("[dim]Lembre-se: Discipline > Emoção | Stop Loss é seu amigo[/dim]\n", style="on black")
                            break
                    else:
                        # Timeframe válido (M5, M15, M30, etc)
                        break

                console.print("\n[bold]2.1 OTC: Restringir Timeframe (Opcional)[/bold]", style="on black")
                console.print("   [dim]Se ativado, o robô executa OTC apenas em M1/M5 para máxima compatibilidade.[/dim]", style="on black")
                console.print("   [dim]Se desativado, respeita M1/M5/M15/M30 e tenta fallback só se a corretora rejeitar.[/dim]", style="on black")
                otc_tf_mode = IntPrompt.ask("   Forçar OTC para M1/M5?", choices=["1", "2"], default=2)
                cfg.force_otc_m1m5 = (otc_tf_mode == 1)

                if cfg.force_otc_m1m5 and cfg.timeframe not in (1, 5):
                    console.print(
                        f"[yellow]⚠️ Forçando OTC para M1/M5: ajustando M{cfg.timeframe} → M5[/yellow]",
                        style="on black",
                    )
                    cfg.timeframe = 5
                
                console.print("\n[bold]3. Meta de Lucro Diária[/bold]", style="on black")
                console.print("   [dim]O robô para automaticamente ao atingir este valor (R$)[/dim]", style="on black")
                cfg.profit_goal = FloatPrompt.ask("   Meta", default=100.0)
                
                console.print("\n[bold]4. Stop Loss (Limite de Perda)[/bold]", style="on black")
                console.print("   [dim]O robô para automaticamente ao atingir este prejuízo (R$)[/dim]", style="on black")
                cfg.stop_loss = FloatPrompt.ask("   Stop Loss", default=50.0)
                
                console.print("\n[bold]5. Níveis de Martingale (Gales)[/bold]", style="on black")
                console.print("   [dim]Quantas tentativas de recuperação após perda[/dim]", style="on black")
                console.print("   [dim]Cada gale multiplica a entrada por 2.2x[/dim]", style="on black")
                console.print("   [bright_magenta]⚠️  Mais gales = maior risco[/bright_magenta]", style="on black")
                cfg.martingale_levels = IntPrompt.ask("   Gales", default=2)
                
                cfg.strategy_name = strategy.name
                cfg.stop_win = cfg.profit_goal  # Auto-sync
                
                print_panel(console, title_panel("CONFIGURAÇÃO FINALIZADA", border_style="bright_green"))
                
                final_config = Group(
                    Text(f"  ✓ Estratégia: {cfg.strategy_name}", style="bright_green"),
                    Text(f"  ✓ Timeframe: M{cfg.timeframe}", style="bright_green"),
                    Text(f"  ✓ Tipo: {cfg.option_type}", style="bright_green"),
                    Text(f"  ✓ OTC: {'M1/M5 (forçado)' if getattr(cfg, 'force_otc_m1m5', False) else 'Livre'}", style="bright_green")
                )
                console.print(Padding(final_config, (0,0), style="on black", expand=True))
                console.rule(style="bright_green on black")
                black_spacer(1)
                
                # Memory Link
                mem = TradingMemory()
                if ai_analyzer: ai_analyzer.set_memory(mem)
                
                run_trading_session(api, strategy, pairs, cfg, mem, ai_analyzer)
                
            elif mode == 2: # BACKTEST
                pairs = select_pairs(api)
                tf = IntPrompt.ask("Timeframe", default=1)

                print_panel(console, menu_table(
                    "Backtest",
                    [("", "Rodando simulação", "Testando estratégias em dados históricos")],
                    border_style="bright_magenta",
                ))
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
                console.print("\n[dim]Pressione ENTER para voltar...[/dim]", style="on black")
                input()
    finally:
        # Graceful shutdown da conexão com a corretora
        try:
            if 'api' in locals() and api:
                api.close()
                console.print("\n[dim]Conexão encerrada com segurança.[/dim]", style="on black")
        except Exception:
            pass

if __name__ == "__main__":
    main()