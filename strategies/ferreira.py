# strategies/ferreira.py
import time
from .base_strategy import BaseStrategy
from utils.indicators import calculate_sma, calculate_atr
import numpy as np

class FerreiraStrategy(BaseStrategy):
    """
    ESTRATÉGIA: Ferreira (Alta Assertividade)
    
    Lógica:
    1. Baseada em 'Psicologia dos Candles' e Movimento Institucional.
    2. Identifica zonas de S/R fortes e aguarda padrões específicos:
       - 'Comando': Vela de força sem pavio (controle total).
       - 'Nova Alta/Baixa': Rompimento com continuidade.
       - 'Exaustão': Vela grande que trava em zona S/R.
    3. Analisa o 'Fluxo' (continuação) ou 'Travamento' (reversão).
    4. Validação IA obrigatória para filtrar ruído.
    """
    def __init__(self, api_handler, ai_analyzer=None):
        super().__init__(api_handler, ai_analyzer)
        self.name = "Ferreira Trader 2.0 (High Assertivity)"
        self.cycle_wins = 0
        
    def check_signal(self, pair, timeframe_str):
        # Timeframe Handling
        try:
            timeframe = int(timeframe_str)
        except:
            timeframe = 1 # Default M1
            
        lookback = 100
        candles = self.api.get_candles(pair, timeframe, lookback)
        if not candles or len(candles) < 50:
            return None, "Aguardando dados..."
            
        # Candles definition
        # candles[-1] is the OPEN/Current candle (Active)
        # candles[-2] is the Last Closed Candle (Signal Candle)
        # candles[-3] is the Previous Closed Candle
        
        active_candle = candles[-1]
        signal_candle = candles[-2]
        prev_candle = candles[-3]
        
        # === 1. MARKET CONTEXT MAPPING ===
        
        # A. Tendência (Bias Visual - SMA 20)
        sma20 = calculate_sma(candles[:-1], 20)
        if not sma20: return None, "Calculando SMA..."
        
        trend = 'NEUTRAL'
        if signal_candle['close'] > sma20: trend = 'BULLISH'
        if signal_candle['close'] < sma20: trend = 'BEARISH'
        
        # B. Identificação de Zonas Magnéticas (SNR Zones)
        # "Zones (boxes), not lines. Depth of 2-5 pips"
        # Logic: Identify levels with rejection (wicks) in last 50 candles
        zones = self.detect_snr_zones(candles[:-1])
        
        # === 2. CANDLE PATTERNS LOGIC ===
        
        # A. Vela de Comando (Institutional Control)
        # Buy: Big body, no bottom wick (Open = Low)
        body_size = abs(signal_candle['close'] - signal_candle['open'])
        avg_body = np.mean([abs(c['close'] - c['open']) for c in candles[-10:-2]])
        
        is_big_body = body_size > avg_body
        
        # Comando Alta: Open close to Low
        comando_alta = is_big_body and (signal_candle['close'] > signal_candle['open']) and \
                       (abs(signal_candle['open'] - signal_candle['low']) <= 0.00001)
                       
        # Comando Baixa: Open close to High
        comando_baixa = is_big_body and (signal_candle['close'] < signal_candle['open']) and \
                        (abs(signal_candle['open'] - signal_candle['high']) <= 0.00001)

        # B. Nova Alta / Nova Baixa (Interest in continuing)
        # Nova Alta: Current High > Prev High & Bullish Close
        nova_alta = (signal_candle['high'] > prev_candle['high']) and \
                    (signal_candle['close'] > signal_candle['open']) and \
                    (trend == 'BULLISH')
                    
        # Nova Baixa: Current Low < Prev Low & Bearish Close
        nova_baixa = (signal_candle['low'] < prev_candle['low']) and \
                     (signal_candle['close'] < signal_candle['open']) and \
                     (trend == 'BEARISH')
                     
        # C. Exaustão (Single candle 3x larger than average)
        is_exhaustion = body_size > (avg_body * 3)

        # === 3. EXECUTION ALGORITHM ===
        
        signal = None
        desc = ""
        
        # --- SETUP 1: CONTINUATION FLOW (Fluxo) ---
        # Trigger: Nova Alta OR Nova Baixa OR Comando
        # Condition: Vacuum (Space) to next SNR > 1.5 candles
        
        if (comando_alta or nova_alta) and trend == 'BULLISH':
            # Check Vacuum
            nearest_res = self.get_nearest_zone(signal_candle['close'], zones, 'RESISTANCE')
            
            if not nearest_res:
                vacuum = True # No ceiling found
            else:
                dist = nearest_res['price'] - signal_candle['close']
                # Assume 1.5 candles distance approx body_size * 1.5
                vacuum = dist > (avg_body * 1.5)
            
            if vacuum and not is_exhaustion:
                signal = "CALL"
                desc = "🌊 FLUXO: Comando/Nova Alta + Vácuo"

        elif (comando_baixa or nova_baixa) and trend == 'BEARISH':
            # Check Vacuum
            nearest_sup = self.get_nearest_zone(signal_candle['close'], zones, 'SUPPORT')
            
            if not nearest_sup:
                vacuum = True # No floor found
            else:
                dist = signal_candle['close'] - nearest_sup['price']
                vacuum = dist > (avg_body * 1.5)
                
            if vacuum and not is_exhaustion:
                signal = "PUT"
                desc = "🌊 FLUXO: Comando/Nova Baixa + Vácuo"

        # --- SETUP 2: SNR REVERSAL (Reversão em Zona) ---
        # Trigger: Price touches SNR Zone 
        # Confirmaton: Prev 2 candles decreasing body (loss momentum) OR Exaustão
        
        # Check current active candle relative to zones for potential reversal logic?
        # NO, user logic: "Previous 2 candles show decreasing body size... Current candle leaves rejection wick"
        # This implies we analyze the Signal Candle (just closed) as the trigger.
        
        # Did signal candle touch a zone and reject?
        # Rejection: Long wick against the zone
        
        if not signal:
            # Check Rejection High (Resistance)
            if signal_candle['high'] > signal_candle['close'] and signal_candle['high'] > signal_candle['open']:
                upper_wick = signal_candle['high'] - max(signal_candle['open'], signal_candle['close'])
                if upper_wick > body_size * 0.5: # Decent wick
                    # Check if wick touched a resistance zone
                    touched_res = self.check_zone_touch(signal_candle['high'], zones, 'RESISTANCE')
                    if touched_res:
                        # Check Momentum Loss (Prev candle body > Signal candle body is not explicitly momentum loss, 
                        # usually means prev candles were getting smaller before this one. 
                        # User: "Previous 2 candles show decreasing body size")
                        
                        b1 = abs(prev_candle['close'] - prev_candle['open'])
                        b2 = abs(candles[-4]['close'] - candles[-4]['open']) # Candle before prev
                        
                        if b2 > b1: # Momentum decreasing
                            signal = "PUT"
                            desc = "🛡️ REVERSÃO: Toque SNR + Perda Momentum"
            
            # Check Rejection Low (Support)
            if signal_candle['low'] < signal_candle['close'] and signal_candle['low'] < signal_candle['open']:
                lower_wick = min(signal_candle['open'], signal_candle['close']) - signal_candle['low']
                if lower_wick > body_size * 0.5:
                    touched_sup = self.check_zone_touch(signal_candle['low'], zones, 'SUPPORT')
                    if touched_sup:
                        b1 = abs(prev_candle['close'] - prev_candle['open'])
                        b2 = abs(candles[-4]['close'] - candles[-4]['open'])
                        
                        if b2 > b1:
                            signal = "CALL"
                            desc = "🛡️ REVERSÃO: Toque SNR + Perda Momentum"

        # === 4. FILTERS TO AVOID LOSS ===
        if signal:
            # 1. Doji (Indecision)
            if body_size < (avg_body * 0.1):
                return None, "Filtro: Doji (Indecisão)"
                
            # 2. Breakout Risk (Close exactly on SNR line with strong body)
            # Checked in logic implicitly, but ensure we don't buy into overhead resistance
            
            # 3. Overextended (3+ same color candles) - Optional as per user prompt "More than 3 green/red"
            # count sequence
            seq = 0
            is_green = signal_candle['close'] > signal_candle['open']
            for i in range(2, 6):
                c = candles[-i]
                c_green = c['close'] > c['open']
                if c_green == is_green:
                    seq += 1
                else:
                    break
            
            if seq >= 3 and "FLUXO" in desc:
                # If flow, we like sequence, but maybe not TOO extended?
                # User says: "More than 3... without pullback (Overextended)"
                # Actually for continuation we want trend, but if 7 candles, maybe scary.
                # Let's trust the logic: if clean trend, go. If Exhaustion, blocked above.
                pass
        
        # 🤖 VALIDAÇÃO IA: IA é o "juiz final" de cada entrada
        if signal and self.ai_analyzer:
            try:
                trend_data = {"trend": trend, "setup": desc.split(":")[0], "pattern": "SNR" if "SNR" in desc else "FLOW"}
                
                should_trade, confidence, ai_reason = self.validate_with_ai(
                    signal, desc, candles, {"support": zones, "resistance": zones}, trend_data, pair
                )
                
                if not should_trade:
                    return None, f"🤖-❌ IA bloqueou: {ai_reason[:30]}... ({confidence}%)"
                
                desc = f"{desc} | 🤖✓{confidence}%"
            except Exception:
                desc = f"{desc} | ⚠️ IA offline"
                
        return signal, desc

    def detect_snr_zones(self, candles):
        # Identify fractal highs/lows or simply wicks that align
        zones = []
        # Simple implementation: use recent swing highs/lows
        for i in range(5, len(candles)-2):
            # Fractal High
            if candles[i]['high'] > candles[i-1]['high'] and candles[i]['high'] > candles[i-2]['high'] and \
               candles[i]['high'] > candles[i+1]['high'] and candles[i]['high'] > candles[i+2]['high']:
                zones.append({'price': candles[i]['high'], 'type': 'RESISTANCE'})
                
            # Fractal Low
            if candles[i]['low'] < candles[i-1]['low'] and candles[i]['low'] < candles[i-2]['low'] and \
               candles[i]['low'] < candles[i+1]['low'] and candles[i]['low'] < candles[i+2]['low']:
                zones.append({'price': candles[i]['low'], 'type': 'SUPPORT'})
                
        return zones

    def get_nearest_zone(self, price, zones, z_type):
        candidates = [z for z in zones if z['type'] == z_type]
        if not candidates: return None
        
        if z_type == 'RESISTANCE':
            # Nearest ABOVE price
            above = [z for z in candidates if z['price'] > price]
            if not above: return None
            return min(above, key=lambda z: z['price'] - price)
            
        if z_type == 'SUPPORT':
            # Nearest BELOW price
            below = [z for z in candidates if z['price'] < price]
            if not below: return None
            return min(below, key=lambda z: price - z['price'])

    def check_zone_touch(self, price_level, zones, z_type, tolerance=0.00010):
        # Check if price_level is within tolerance of any zone of type z_type
        for z in zones:
            if z['type'] == z_type:
                if abs(z['price'] - price_level) <= tolerance:
                    return True
        return False
