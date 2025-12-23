# strategies/conservador.py
# -----------------------------------------------------------------------------
# ⛔ PROTECTED FILE - DO NOT EDIT WITHOUT EXPLICIT USER PERMISSION
# Strategy 5: Conservador
# -----------------------------------------------------------------------------

from .base_strategy import BaseStrategy
from utils.indicators import calculate_sma, calculate_atr
import json

class ConservadorStrategy(BaseStrategy):
    def __init__(self, api_handler, ai_analyzer=None):
        super().__init__(api_handler, ai_analyzer)
        self.name = "Trader Conservador"
        self.state = "WAITING_CHANNEL"
        
        # State Variables
        self.ref_channel = None
        self.neutral_zone = None
        self.trend = "UNDEFINED"
        
        # CONFIGURAÇÕES CONSERVADORAS
        self.lookback_periods = 30  # Maior que FIMATHE padrão (20)
        self.min_atr_multiplier = 1.5  # Canal precisa ser 1.5x maior que ATR
        self.sma_trend = 200  # Tendência macro

    def calculate_atr_safe(self, candles, period=14):
        try:
            return calculate_atr(candles, period)
        except:
            return 0.0001

    def check_signal(self, pair, timeframe):
        # Precisa de mais dados por causa do lookback maior
        lookback = 250  # 200 SMA + 30 lookback + buffer
        candles = self.api.get_candles(pair, timeframe, lookback)
        
        if not candles or len(candles) < 200:
            return None, "Aguardando dados (min 200 velas)..."

        last_closed_candle = candles[-2]
        current_price = last_closed_candle['close']
        
        if self.state == "WAITING_CHANNEL":
            return self.scan_for_channel(candles)
            
        elif self.state == "CHANNEL_LOCKED":
            return self.monitor_breakout(last_closed_candle, candles)
            
        return None, "Estado desconhecido"

    def scan_for_channel(self, candles):
        # Canal com lookback MAIOR (30 velas)
        subset = candles[-(self.lookback_periods+1):-1]
        highs = [c['high'] for c in subset]
        lows = [c['low'] for c in subset]
        
        highest = max(highs)
        lowest = min(lows)
        height = highest - lowest
        
        # FILTRO ATR MAIS RIGOROSO (1.5x ao invés de 1x)
        atr = self.calculate_atr_safe(candles, 14)
        min_height = atr * self.min_atr_multiplier
        
        if height < min_height:
            return None, f"Volatilidade insuficiente (Canal {height:.5f} < {min_height:.5f})"
            
        # Tendência Macro (SMA 200)
        sma200 = calculate_sma(candles[:-1], self.sma_trend)
        current_close = candles[-2]['close']
        
        self.trend = "BULLISH" if current_close > sma200 else "BEARISH"
        
        # FILTRO ADICIONAL: Verificar se a tendência é FORTE
        # Preço deve estar pelo menos 0.1% acima/abaixo da SMA
        distance_from_sma = abs(current_close - sma200) / sma200
        if distance_from_sma < 0.001:  # Menos de 0.1%
            return None, f"Tendência fraca (preço muito próximo da SMA 200)"
        
        # Lock Channel
        self.ref_channel = {
            'high': highest,
            'low': lowest,
            'height': height
        }
        
        # Zona Neutra
        if self.trend == "BULLISH":
            self.neutral_zone = {
                'top': lowest,
                'bottom': lowest - height
            }
        else:
            self.neutral_zone = {
                'top': highest + height,
                'bottom': highest
            }
            
        self.state = "CHANNEL_LOCKED"
        return None, f"[CONSERVADOR] Canal Travado! Tendência: {self.trend} | ATR: {atr:.5f}"

    def monitor_breakout(self, candle, candles):
        close = candle['close']
        
        ref_top = self.ref_channel['high']
        ref_bot = self.ref_channel['low']
        nz_top = self.neutral_zone['top']
        nz_bot = self.neutral_zone['bottom']
        
        # Filtro Anti-Oscilação
        if ref_bot <= close <= ref_top:
            return None, f"Aguardando rompimento [{ref_bot:.5f} - {ref_top:.5f}]"
        if nz_bot <= close <= nz_top:
            return None, f"Preço na Zona Neutra (sem sinal)"
        
        signal = None
        desc = "Monitorando..."
        
        # LÓGICA CONSERVADORA: Só entra A FAVOR da tendência
        # NÃO faz reversões (mais arriscado)
        
        if self.trend == "BULLISH":
            # Só compra se romper o topo (pro-trend)
            if close > ref_top:
                # CONFIRMAÇÃO ADICIONAL: Vela deve ser verde
                if candle['close'] > candle['open']:
                    signal = "CALL"
                    desc = "[CONSERVADOR] Rompimento confirmado (Vela Verde)"
                    self.reset_state()
                else:
                    return None, "Rompimento com vela vermelha (aguardando confirmação)"
        
        if self.trend == "BEARISH":
            # Só vende se romper o fundo (pro-trend)
            if close < ref_bot:
                # CONFIRMAÇÃO ADICIONAL: Vela deve ser vermelha
                if candle['close'] < candle['open']:
                    signal = "PUT"
                    desc = "[CONSERVADOR] Rompimento confirmado (Vela Vermelha)"
                    self.reset_state()
                else:
                    return None, "Rompimento com vela verde (aguardando confirmação)"
        
        if not signal:
            return None, f"Aguardando rompimento válido | Preço: {close:.5f}"
            
        return signal, desc

    def reset_state(self):
        self.state = "WAITING_CHANNEL"
        self.ref_channel = None
        self.neutral_zone = None
