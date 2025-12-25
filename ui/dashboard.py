# ui/dashboard.py - Dashboard Premium Profissional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from datetime import datetime
import math


class Dashboard:
    def __init__(self, config):
        self.console = Console(style="white on black")
        self.config = config
        self.logs = []
        self.system_logs = []

        # UI State
        self.ai_state = "OFF"  # OFF | ONLINE | DEGRADED
        
        # Volatility & Performance Cache
        self._cached_vol = 55
        self._last_vol_update = 0
        
        self.layout = Layout()

        # Ratio de layout
        self._grid_left_ratio = 1
        self._grid_right_ratio = 1
        
        # Estrutura do layout
        self.layout.split_column(
            Layout(name="top_bar", size=3),
            Layout(name="main_grid", ratio=1),
            Layout(name="footer", size=15)
        )
        self.layout["main_grid"].split_row(
            Layout(name="left_panel", ratio=self._grid_left_ratio),
            Layout(name="right_panel", ratio=self._grid_right_ratio)
        )
        self.layout["footer"].split_row(
            Layout(name="footer_left", ratio=self._grid_left_ratio),
            Layout(name="footer_right", ratio=self._grid_right_ratio),
        )

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Filter repetição desnecessária
        if any(x in message for x in ["Wait", "Aguardando próxima"]):
            return 
            
        # Strategy Logs
        if "[STRATEGY]" in message or "[FIA]" in message:
            if "resistências" in message or "suportes" in message:
                clean = message.split("]")[-1].strip()
                self.system_logs.append(f"[{timestamp}] 📐 {clean}")
            return

        # AI Logs
        if "[AI]" in message:
            clean = message.split("]")[-1].strip()
            icon = "◎"
            color = "bright_cyan"
            
            if "conectada" in message.lower() or "ativa" in message.lower() or "online" in message.lower():
                self.ai_state = "ONLINE"
            if "desativ" in message.lower() or "chave" in message.lower():
                self.ai_state = "OFF"
            if "timeout" in message.lower() or "rate" in message.lower():
                self.ai_state = "DEGRADED"

            if "Confirmado" in message or "✅" in message:
                icon = "▲"; color = "green"
            elif "Rejeitado" in message or "❌" in message:
                icon = "▼"; color = "red"
            elif "Evitando" in message or "⚠️" in message:
                icon = "■"; color = "yellow"
            
            self.system_logs.append(f"[{timestamp}] {icon} [{color}]{clean}[/]")
            return

        # IQ Handler Logs
        if "[IQ]" in message or "IQ_HANDLER" in message:
            if "Falha" in message or "Erro" in message:
                self.system_logs.append(f"[{timestamp}] 📡 [red]{message}[/]")
            return

        # Trade Logs (WIN/LOSS/SIGNAL)
        clean_msg = message
        if "WIN" in message:
            clean_msg = f"[bold green]✓ WIN[/] {message}"
        elif "LOSS" in message:
            clean_msg = f"[bold red]✗ LOSS[/] {message}"
        elif "SINAL" in message or "CALL" in message or "PUT" in message:
            clean_msg = f"[bold bright_cyan]◆ SINAL[/] {message}"
        
        self.logs.append(f"[{timestamp}] {clean_msg}")
        if len(self.logs) > 15: 
            self.logs.pop(0)
        if len(self.system_logs) > 15: 
            self.system_logs.pop(0)

    def _get_signal_strength(self):
        """Barra de volatilidade com animação suave"""
        import time

        now = time.time()
        if now - self._last_vol_update > 2:
            phase = (now / 12.0) % (2 * math.pi)
            target = 55 + int(30 * math.sin(phase))
            self._cached_vol = max(20, min(92, target))
            self._last_vol_update = now

        val = int(self._cached_vol)
        color = "green" if val > 70 else "bright_yellow" if val > 40 else "red"

        bar_len = 20
        filled = int((val / 100) * bar_len)
        empty = bar_len - filled

        filled_bar = "█" * filled
        empty_bar = "░" * empty

        return f"[{color}]{filled_bar}[/][dim]{empty_bar}[/] [{color}]{val:>3d}%[/]"

    def _render_ai_badge(self):
        """Badge de status da IA com cores premium"""
        badges = {
            "ONLINE": "[bold green]● ONLINE[/bold green]",
            "DEGRADED": "[bold bright_magenta]⚠ LIMITADO[/bold bright_magenta]",
            "OFF": "[dim]◯ OFF[/dim]"
        }
        return badges.get(self.ai_state, "[dim]◯ OFF[/dim]")

    def _render_candle_progress(self, time_to_close):
        """Barra de progresso da vela com porcentagem"""
        duration = max(1, int(getattr(self.config, 'timeframe', 1)) * 60)
        remaining = max(0, min(duration, int(time_to_close)))
        elapsed = max(0, duration - remaining)
        pct = int((elapsed / duration) * 100)

        bar_len = 18
        filled = int((pct / 100) * bar_len)
        empty = bar_len - filled

        filled_bar = "█" * filled
        empty_bar = "░" * empty

        color = "bright_cyan" if remaining > 10 else "bright_magenta"
        return f"[{color}]{filled_bar}[/][dim]{empty_bar}[/] [{color}]{pct:>3d}%[/]"

    def _render_profit_bar(self, current_profit, goal):
        """Barra de progresso de lucro com gradiente de cores"""
        if goal <= 0:
            pct = 0
        else:
            pct = min(100, max(0, (current_profit / goal) * 100))

        if current_profit >= goal:
            color = "bold green"
            symbol = "━"
        elif current_profit >= goal * 0.5:
            color = "bright_cyan"
            symbol = "━"
        elif current_profit > 0:
            color = "bright_yellow"
            symbol = "━"
        else:
            color = "red"
            symbol = "━"

        bar_len = 18
        filled = int((pct / 100) * bar_len)
        empty = bar_len - filled

        bar_filled = symbol * filled
        bar_empty = "┄" * empty

        return f"[{color}]{bar_filled}[/][dim]{bar_empty}[/]"

    def _render_risk_meter(self, current_loss, stop_loss):
        """Medidor de risco (quanto longe está do stop)"""
        if stop_loss <= 0:
            return "[dim]N/A[/dim]"
        
        pct = abs(current_loss / stop_loss) * 100
        color = "green" if pct < 33 else "bright_yellow" if pct < 66 else "red"
        
        bar_len = 12
        filled = int((pct / 100) * bar_len)
        empty = bar_len - filled
        
        bar_filled = "▮" * filled
        bar_empty = "▯" * empty
        
        return f"[{color}]{bar_filled}[/][dim]{bar_empty}[/] [{color}]{pct:.0f}%[/]"

    def render(self, current_profit, time_to_close=0):
        """Renderiza o dashboard premium completo"""
        
        # ==================== TOP BAR ====================
        acc_type = "REAL" if self.config.account_type == "REAL" else "DEMO"
        acc_color = "bold bright_green" if acc_type == "REAL" else "bright_cyan"
        
        header_table = Table.grid(expand=True, padding=(0, 1))
        header_table.add_column(style="dim")
        header_table.add_column(justify="center")
        header_table.add_column(justify="right", style="dim")
        
        # Logo premium
        logo = "[bold bright_magenta]⬢[/] [bold white]ANTIGRAVITY[/] [bold bright_cyan]FIA[/] [dim]v3.5[/dim]"
        status = f"[{acc_color}]● {acc_type}[/] • {self._render_ai_badge()}"
        clock = datetime.now().strftime('%d/%m %H:%M:%S')
        
        header_table.add_row(logo, status, clock)
        
        self.layout["top_bar"].update(
            Panel(header_table, border_style="bright_magenta", box=box.ROUNDED, style="on black")
        )

        # ==================== LEFT PANEL: FINANCEIRO ====================
        goal = getattr(self.config, 'profit_goal', 100)
        stop_loss = getattr(self.config, 'stop_loss', 0)
        
        fin_table = Table.grid(expand=True, padding=(0, 1))
        fin_table.add_column(min_width=18)
        fin_table.add_column(justify="right")
        
        # Saldo
        balance_val = f"[bold white]R$ {self.config.balance:,.2f}[/]"
        fin_table.add_row("[bright_cyan]█[/] Saldo", balance_val)
        
        # Resultado da sessão
        p_color = "bright_green" if current_profit >= 0 else "bright_red"
        profit_val = f"[bold {p_color}]R$ {current_profit:+,.2f}[/]"
        fin_table.add_row("[bright_magenta]█[/] Resultado", profit_val)
        
        # Progresso
        pct = min(100, max(0, (current_profit / goal) * 100)) if goal > 0 else 0
        fin_table.add_row("[yellow]█[/] Progresso", f"[bold {p_color}]{pct:.1f}%[/]")
        fin_table.add_row("", self._render_profit_bar(current_profit, goal))
        
        fin_table.add_row("", "")
        
        # Meta e Stop
        fin_table.add_row("[dim]Meta diária[/]", f"[bold]R$ {goal:,.0f}[/]")
        fin_table.add_row("[dim]Stop loss[/]", f"[bold]R$ {stop_loss:,.0f}[/]")
        
        fin_table.add_row("", "")
        
        # Risco
        fin_table.add_row("[red]█[/] Risco", self._render_risk_meter(current_profit, stop_loss))
        
        fin_panel = Panel(
            fin_table,
            title="[bold bright_cyan]FINANCEIRO[/]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
            style="on black",
        )
        self.layout["left_panel"].update(fin_panel)

        # ==================== RIGHT PANEL: MERCADO ====================
        mins = int(time_to_close) // 60
        secs = int(time_to_close) % 60
        timer_color = "white" if time_to_close > 30 else "bright_magenta" if time_to_close > 10 else "bold red"

        market_table = Table.grid(expand=True, padding=(0, 1))
        market_table.add_column(min_width=18)
        market_table.add_column(justify="right")
        
        market_table.add_row("[bright_magenta]█[/] Estratégia", f"[bold]{self.config.strategy_name}[/]")
        market_table.add_row("[bright_cyan]█[/] Ativo(s)", f"[bold white]{self.config.asset}[/]")
        market_table.add_row("[white]█[/] IA", self._render_ai_badge())
        market_table.add_row("[yellow]█[/] Timeframe", f"[bold bright_cyan]M{self.config.timeframe}[/]")
        
        market_table.add_row("", "")
        
        market_table.add_row("[{0}]█[/] Fechamento".format(timer_color), 
                            f"[{timer_color}]{mins:02d}:{secs:02d}[/] [dim]restantes[/]")
        market_table.add_row("", self._render_candle_progress(time_to_close))
        
        market_table.add_row("", "")
        
        market_table.add_row("[green]█[/] Volatilidade", self._get_signal_strength())
        
        strat_panel = Panel(
            market_table,
            title="[bold bright_magenta]MERCADO[/]",
            border_style="bright_magenta",
            box=box.ROUNDED,
            padding=(1, 2),
            style="on black",
        )
        self.layout["right_panel"].update(strat_panel)

        # ==================== FOOTER LEFT: EXECUÇÃO ====================
        log_txt = "\n".join(self.logs[-9:]) if self.logs else "[dim]Aguardando operações...[/]"
        
        exec_panel = Panel(
            log_txt,
            title="[bold bright_cyan]► EXECUÇÃO[/]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
            style="on black",
        )
        self.layout["footer_left"].update(exec_panel)

        # ==================== FOOTER RIGHT: SISTEMA ====================
        sys_txt = "\n".join(self.system_logs[-9:]) if self.system_logs else "[dim]Inicializando...[/]"
        
        sys_panel = Panel(
            sys_txt,
            title="[bold bright_white]⚙ SISTEMA[/]",
            border_style="bright_white",
            box=box.ROUNDED,
            padding=(1, 2),
            style="on black",
        )
        self.layout["footer_right"].update(sys_panel)

        return self.layout
