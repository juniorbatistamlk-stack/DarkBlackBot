# ui/dashboard.py
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
        self.console = Console()
        self.config = config
        self.logs = []
        self.system_logs = []
        
        # Volatility Cache
        self._cached_vol = 50
        self._last_vol_update = 0
        
        self.layout = Layout()
        
        # Initial Layout Structuring
        self.layout.split_column(
            Layout(name="top_bar", size=3),
            Layout(name="main_grid", ratio=1),
            Layout(name="footer", size=14)
        )
        self.layout["main_grid"].split_row(
            Layout(name="left_panel", ratio=1),
            Layout(name="right_panel", ratio=1)
        )
        # Footer agora é um único layout sem divisão
        # A divisória central é feita manualmente na renderização

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Smart Filtering
        if any(x in message for x in ["TIMEOUT", "Reconectando", "tentativa", "Analisando", "Wait"]):
            return 
            
        # Strategy Logs
        if "[STRATEGY]" in message:
            if "resistências" in message or "suportes" in message:
                 # Extract useful info only
                clean = message.split("]")[-1].strip().replace("📊", "")
                self.system_logs.append(f"[{timestamp}] 📐 {clean}")
            return

        # AI Logs
        if "[AI]" in message:
            clean = message.split("]")[-1].strip().replace("🤖", "").replace("⚠️", "")
            icon = "🧠"
            color = "bright_cyan"
            if "Confirmado" in message: 
                icon = "✅"; color = "green"
            elif "Evitando" in message: 
                icon = "🛡️"; color = "yellow"
            
            self.system_logs.append(f"[{timestamp}] {icon} [{color}]{clean}[/]")
            return

        # IQ Logs
        if "[IQ]" in message or "IQ_HANDLER" in message:
            if "Falha" in message or "Erro" in message or "Socket" in message:
                 self.system_logs.append(f"[{timestamp}] 📡 [red]{message}[/]")
            return

        # Trade Logs
        clean_msg = message
        if "WIN" in message: clean_msg = f"[bold green]WIN 💵 {message}[/]"
        elif "LOSS" in message: clean_msg = f"[bold red]LOSS 💸 {message}[/]"
        elif "SINAL" in message: clean_msg = f"[bold yellow]🎯 SINAL DETECTADO: {message}[/]"
        
        self.logs.append(f"[{timestamp}] {clean_msg}")
        if len(self.logs) > 15: self.logs.pop(0)
        if len(self.system_logs) > 15: self.system_logs.pop(0)

    def _get_signal_strength(self):
        # Atualizar apenas a cada 3 segundos para evitar "pisca-pisca"
        import time
        import random
        
        now = time.time()
        if now - self._last_vol_update > 3:
            self._cached_vol = random.randint(30, 90)
            self._last_vol_update = now
            
        val = self._cached_vol
        color = "green" if val > 70 else "yellow" if val > 40 else "red"
        bars = "█" * (val // 10) + "░" * ((100-val)//10)
        return f"[{color}]{bars}[/] {val}%"

    def render(self, current_profit, time_to_close=0):
        # 1. Top Bar (Status Line)
        acc_type = "REAL" if self.config.account_type == "REAL" else "DEMO"
        acc_color = "bright_green" if acc_type == "REAL" else "bright_cyan"
        
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left")
        header_table.add_column(justify="center")
        header_table.add_column(justify="right")
        
        header_table.add_row(
            f" [bold white]ANTIGRAVITY[/] [bold bright_magenta]BOT[/] v3.5",
            f"[bold {acc_color}]● CONECTADO ({acc_type})[/]",
            f"[dim]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/] "
        )
        
        self.layout["top_bar"].update(Panel(header_table, style="on #0f0f0f", box=box.SIMPLE))

        # 2. Left Panel: Financials (Big Numbers)
        fin_table = Table.grid(expand=True, padding=(1, 2))
        fin_table.add_column("Label", justify="left")
        fin_table.add_column("Value", justify="right")
        
        # Balance
        fin_table.add_row("[dim]Banca Atual[/]", "")
        fin_table.add_row(f"[bold white]R$ {self.config.balance:.2f}[/]", "")
        fin_table.add_row("", "")
        
        # Profit
        p_color = "bright_green" if current_profit >= 0 else "bright_red"
        fin_table.add_row("[dim]Lucro Sessão[/]", "")
        fin_table.add_row(f"[bold {p_color}]R$ {current_profit:+.2f}[/]", "")
        
        # Meta Bar
        goal = getattr(self.config, 'profit_goal', 100)
        pct = min(100, max(0, (current_profit / goal) * 100)) if goal else 0
        bar_len = 20
        filled = int((pct / 100) * bar_len)
        bar = "━" * filled + "┄" * (bar_len - filled)
        
        fin_panel = Panel(
            Align.center(
                f"\n[bold white]R$ {self.config.balance:.2f}[/]\n[dim]SALDO TOTAL[/]\n\n"
                f"[bold {p_color} size=20]R$ {current_profit:+.2f}[/]\n[dim]RESULTADO HOJE[/]\n\n"
                f"[bold {p_color}]{pct:.1f}%[/]\n[{p_color}]{bar}[/]\n[dim]META: R$ {goal:.0f}[/]"
            ),
            title="[bold bright_cyan]FINANCEIRO[/]",
            border_style="bright_cyan",
            box=box.ROUNDED
        )
        self.layout["left_panel"].update(fin_panel)

        # 3. Right Panel: Market & Strategy
        strat_table = Table.grid(expand=True, padding=(0, 1))
        strat_table.add_column(ratio=1)
        strat_table.add_column(ratio=2)
        
        mins = int(time_to_close) // 60
        secs = int(time_to_close) % 60
        timer_color = "white" if time_to_close > 30 else "yellow" if time_to_close > 10 else "bold red"
        
        strat_panel = Panel(
            Align.left(
                f"[bold bright_magenta]Estratégia:[/]\n {self.config.strategy_name}\n\n"
                f"[bold bright_magenta]Ativo:[/]\n [bold yellow]{self.config.asset}[/] (OTC)\n\n"
                f"[bold bright_magenta]Timeframe:[/]\n M{self.config.timeframe}\n\n"
                f"[bold bright_magenta]Vela:[/]\n [{timer_color}]{mins:02d}:{secs:02d}[/] [dim]restantes[/]\n\n"
                f"[bold bright_magenta]Volatilidade:[/]\n {self._get_signal_strength()}"
            ),
            title="[bold bright_magenta]MERCADO[/]",
            border_style="bright_magenta",
            box=box.ROUNDED
        )
        self.layout["right_panel"].update(strat_panel)

        # 4. Footer Logs (sem bordas externas, apenas divisória central)
        log_txt = "\n".join(self.logs[-8:]) if self.logs else "[dim]Aguardando operações...[/]"
        op_content = f"[bold bright_yellow]━━━ EXECUÇÃO ━━━[/]\n{log_txt}"
        
        sys_txt = "\n".join(self.system_logs[-8:]) if self.system_logs else "[dim]Inicializando sistema...[/]"
        sys_content = f"[bold white]━━━ SISTEMA ━━━[/]\n{sys_txt}"
        
        # Criar uma tabela grid com divisória central
        from rich.columns import Columns
        footer_table = Table.grid(expand=True)
        footer_table.add_column(ratio=6)
        footer_table.add_column(width=1)  # Divisória central
        footer_table.add_column(ratio=4)
        
        # Divisória vertical
        divider = "\n".join(["│"] * 12)
        
        footer_table.add_row(
            Panel(op_content, box=box.SIMPLE, border_style="dim"),
            Text(divider, style="bright_white"),
            Panel(sys_content, box=box.SIMPLE, border_style="dim")
        )
        
        # Atualizar footer como um único painel sem bordas
        self.layout["footer"].update(Panel(footer_table, box=box.SIMPLE, style="on #0a0a0a"))

        return self.layout
