"""Teste local do Dashboard (sem IQ Option).

Objetivo: validar se a UI (Rich Live) fica responsiva e se o timer de vela
conta corretamente (segundos restantes), sem depender de rede/credenciais.

Execute:
  python debug_dashboard.py
"""

import time
from dataclasses import dataclass

from rich.live import Live

from ui.dashboard import Dashboard


@dataclass
class DummyConfig:
    account_type: str = "DEMO"
    profit_goal: float = 600
    stop_loss: float = 1000
    balance: float = 26361.28
    strategy_name: str = "BLACK FLEX - Alavancagem LTA/LTB (BLACK)"
    asset: str = "EURUSD-OTC, GBPUSD-OTC, EURJPY-OTC"
    timeframe: int = 1


def main() -> None:
    cfg = DummyConfig()
    dashboard = Dashboard(cfg)

    current_profit = 0.0
    worker_status = "Iniciando teste de UI..."

    # Simula vela M1 (60s) contando regressivo
    candle_duration = cfg.timeframe * 60
    candle_start = int(time.time())

    with Live(
        dashboard.render(current_profit, candle_duration, worker_status),
        auto_refresh=False,
        screen=True,
        console=dashboard.console,
    ) as live:
        while True:
            now = int(time.time())
            elapsed = now - candle_start
            remaining = max(0, candle_duration - (elapsed % candle_duration))

            # Simula variacao de lucro e logs
            if elapsed % 7 == 0:
                current_profit += 3.5
                dashboard.log(f"WIN simulado +R$3.50 (t={elapsed}s)")
            if elapsed % 11 == 0:
                worker_status = "Analisando pares..."
            elif elapsed % 11 == 5:
                worker_status = "SINAL PRONTO!"

            live.update(dashboard.render(current_profit, int(remaining), worker_status))
            time.sleep(0.2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
