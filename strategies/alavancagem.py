# strategies/alavancagem.py
# =============================================================================
# ESTRATÉGIA 6: ALAVANCAGEM INTELIGENTE COM ANÁLISE PRÉVIA
# =============================================================================
# REGRAS FUNDAMENTAIS:
# 1. NUNCA opera contra a tendência (LTA/LTB)
# 2. Só opera A FAVOR do fluxo de velas
# 3. Reversões APENAS em zonas S/R fortes com padrões de vela confirmados
# 4. Faz análise prévia do gráfico (200 velas) para identificar S/R
# 5. Modo AGRESSIVO - entradas frequentes a favor da tendência
# =============================================================================

from .base_strategy import BaseStrategy
from utils.indicators import calculate_ema, calculate_atr

class AlavancagemStrategy(BaseStrategy):
    def __init__(self, api_handler, ai_analyzer=None):
        super().__init__(api_handler, ai_analyzer)
        self.name = "ALAVANCAGEM (LTA/LTB + S/R)"
        self.consecutive_wins = 0
        self.sr_zones = {}  # Cache de zonas S/R por par
        self.analyzed_pairs = set()  # Pares já analisados
        self.pre_analysis_done = {}  # Timestamp da análise
        self._logger = None  # Callback para logs
    
    def set_logger(self, log_func):
        """Define callback para enviar logs ao dashboard"""
        self._logger = log_func
    
    def _log(self, msg):
        """Envia log para dashboard ou print como fallback"""
        if self._logger:
            self._logger(msg)
        else:
            print(msg)
        
    def pre_analyze(self, pair, timeframe=1):
        """
        PRÉ-ANÁLISE OBRIGATÓRIA: Roda antes de operar
        Analisa últimas 200 velas para encontrar níveis importantes de S/R
        
        Retorna: Dict com zonas de suporte e resistência detectadas
        """
        self._log(f"[STRATEGY] 📊 Pré-análise de {pair}...")
        
        candles = self.api.get_candles(pair, timeframe, 200)
        if not candles or len(candles) < 100:
            self._log(f"[STRATEGY] ⚠️ Dados insuficientes para {pair}")
            return None
        
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        
        # Encontrar topos e fundos (swing points)
        swing_highs = []
        swing_lows = []
        
        for i in range(5, len(candles) - 5):
            # Topo: máxima maior que 5 velas antes e depois
            if candles[i]['high'] == max([c['high'] for c in candles[i-5:i+6]]):
                swing_highs.append(candles[i]['high'])
            # Fundo: mínima menor que 5 velas antes e depois
            if candles[i]['low'] == min([c['low'] for c in candles[i-5:i+6]]):
                swing_lows.append(candles[i]['low'])
        
        # Agrupar níveis próximos (clusters)
        atr = calculate_atr(candles[:-1], 14) or 0.0001
        tolerance = atr * 1.5
        
        resistance_zones = self._cluster_levels(swing_highs, tolerance)
        support_zones = self._cluster_levels(swing_lows, tolerance)
        
        # Salvar no cache
        self.sr_zones[pair] = {
            'resistance': resistance_zones,
            'support': support_zones,
            'atr': atr
        }
        self.analyzed_pairs.add(pair)
        
        self._log(f"[STRATEGY] ✅ {pair}: {len(resistance_zones)} resistências | {len(support_zones)} suportes")
        
        return {
            'resistance': resistance_zones,
            'support': support_zones,
            'swing_highs': len(swing_highs),
            'swing_lows': len(swing_lows)
        }
    
    def _cluster_levels(self, levels, tolerance):
        """Agrupa níveis próximos em zonas"""
        if not levels:
            return []
        
        levels = sorted(levels)
        zones = []
        current_zone = [levels[0]]
        
        for level in levels[1:]:
            if level - current_zone[-1] <= tolerance:
                current_zone.append(level)
            else:
                # Criar zona com média
                zones.append({
                    'level': sum(current_zone) / len(current_zone),
                    'touches': len(current_zone)
                })
                current_zone = [level]
        
        # Última zona
        if current_zone:
            zones.append({
                'level': sum(current_zone) / len(current_zone),
                'touches': len(current_zone)
            })
        
        # Ordenar por número de toques (mais forte primeiro)
        zones.sort(key=lambda x: x['touches'], reverse=True)
        
        # Retornar top 5 mais fortes
        return zones[:5]
        
    def check_signal(self, pair, timeframe_str):
        try:
            timeframe = int(timeframe_str)
        except:
            timeframe = 1
        
        # PRÉ-ANÁLISE OBRIGATÓRIA: Se ainda não analisou, analisar agora
        if pair not in self.analyzed_pairs:
            self.pre_analyze(pair, timeframe)
            
        candles = self.api.get_candles(pair, timeframe, 50)
        if not candles or len(candles) < 25:
            return None, "Dados..."
        
        # === INDICADORES ===
        ema9 = calculate_ema(candles[:-1], 9)
        ema21 = calculate_ema(candles[:-1], 21)
        ema50 = calculate_ema(candles[:-1], 50) if len(candles) >= 51 else ema21
        atr = calculate_atr(candles[:-1], 14)
        
        if not all([ema9, ema21, atr]):
            return None, "Calculando..."
        
        # Vela atual e anterior
        current = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3]
        
        price = current['close']
        is_green = current['close'] > current['open']
        is_red = current['close'] < current['open']
        prev_green = prev['close'] > prev['open']
        prev_red = prev['close'] < prev['open']
        
        body = abs(current['close'] - current['open'])
        total_range = current['high'] - current['low']
        if total_range == 0:
            return None, "Doji fraco"
        
        upper_wick = current['high'] - max(current['open'], current['close'])
        lower_wick = min(current['open'], current['close']) - current['low']
        
        # === ANÁLISE DE TENDÊNCIA (LTA/LTB) ===
        # Calcular direção das últimas velas
        lows_recent = [c['low'] for c in candles[-10:-1]]
        highs_recent = [c['high'] for c in candles[-10:-1]]
        closes_recent = [c['close'] for c in candles[-10:-1]]
        
        # LTA: Fundos ascendentes (últimos 3 fundos subindo)
        lta_valid = lows_recent[-1] > lows_recent[-3] and lows_recent[-2] > lows_recent[-4]
        
        # LTB: Topos descendentes (últimos 3 topos caindo)
        ltb_valid = highs_recent[-1] < highs_recent[-3] and highs_recent[-2] < highs_recent[-4]
        
        # Fluxo de velas (momentum)
        green_count = sum(1 for c in candles[-5:-1] if c['close'] > c['open'])
        red_count = 4 - green_count
        bullish_flow = green_count >= 3
        bearish_flow = red_count >= 3
        
        # === TENDÊNCIA CONFIRMADA (MAIS AGRESSIVO) ===
        # Tendência básica: EMA9 vs EMA21 + preço
        is_uptrend = ema9 > ema21 and price > ema9
        is_downtrend = ema9 < ema21 and price < ema9
        
        # Tendência forte: inclui LTA/LTB
        strong_uptrend = is_uptrend and lta_valid
        strong_downtrend = is_downtrend and ltb_valid
        
        # Tendência simples: só EMAs
        simple_uptrend = ema9 > ema21
        simple_downtrend = ema9 < ema21
        
        # === ZONAS S/R (da pré-análise) ===
        sr_data = self.sr_zones.get(pair, {'resistance': [], 'support': [], 'atr': atr})
        resistance_zones = sr_data['resistance']
        support_zones = sr_data['support']
        
        tolerance = atr * 0.5
        
        # Verificar se está em zona FORTE (pelo menos 2 toques)
        at_resistance = any(
            abs(current['high'] - z['level']) <= tolerance and z['touches'] >= 2 
            for z in resistance_zones
        )
        at_support = any(
            abs(current['low'] - z['level']) <= tolerance and z['touches'] >= 2 
            for z in support_zones
        )
        
        # Força da zona
        resistance_strength = max([z['touches'] for z in resistance_zones if abs(current['high'] - z['level']) <= tolerance], default=0)
        support_strength = max([z['touches'] for z in support_zones if abs(current['low'] - z['level']) <= tolerance], default=0)
        
        # === PADRÕES DE REVERSÃO (confirmação obrigatória) ===
        is_hammer = lower_wick > body * 2.5 and upper_wick < body * 0.3 and is_green
        is_shooting = upper_wick > body * 2.5 and lower_wick < body * 0.3 and is_red
        is_engulf_bull = is_green and prev_red and current['close'] > prev['open'] and current['open'] < prev['close']
        is_engulf_bear = is_red and prev_green and current['close'] < prev['open'] and current['open'] > prev['close']
        is_pinbar_bull = lower_wick > total_range * 0.65 and is_green
        is_pinbar_bear = upper_wick > total_range * 0.65 and is_red
        
        # Doji após movimento forte
        is_doji = (body / total_range < 0.1) if total_range and total_range > 0 else False
        doji_at_top = is_doji and at_resistance and prev_green
        doji_at_bottom = is_doji and at_support and prev_red
        
        signal = None
        desc = ""
        
        # =====================================================
        # PRIORIDADE 1: FLUXO AGRESSIVO A FAVOR DA TENDÊNCIA
        # =====================================================
        
        # ALTA FORTE: EMA alinhadas + LTA + vela verde + fluxo
        if strong_uptrend and is_green:
            signal = "CALL"
            desc = f"🚀 FLUXO ALTA FORTE | LTA + EMAs alinhadas"
        
        # ALTA NORMAL: EMA + verde com momentum
        elif is_uptrend and is_green and bullish_flow:
            signal = "CALL"
            desc = f"📈 TENDÊNCIA ALTA | Fluxo comprador"
        
        # PULLBACK EM ALTA (não em resistência)
        elif is_uptrend and prev_red and is_green and not at_resistance:
            signal = "CALL"
            desc = f"🔄 PULLBACK ALTA | Retomada após correção"
        
        # BAIXA FORTE: EMA alinhadas + LTB + vela vermelha + fluxo
        elif strong_downtrend and is_red:
            signal = "PUT"
            desc = f"🚀 FLUXO BAIXA FORTE | LTB + EMAs alinhadas"
        
        # BAIXA NORMAL: EMA + vermelha com momentum
        elif is_downtrend and is_red and bearish_flow:
            signal = "PUT"
            desc = f"📉 TENDÊNCIA BAIXA | Fluxo vendedor"
        
        # PULLBACK EM BAIXA (não em suporte)
        elif is_downtrend and prev_green and is_red and not at_support:
            signal = "PUT"
            desc = f"🔄 PULLBACK BAIXA | Retomada após correção"
        
        # =====================================================
        # PRIORIDADE 3: ENTRADAS AGRESSIVAS (respeita tendência)
        # =====================================================
        
        # CALL AGRESSIVO: EMA9 > EMA21 + vela verde + preço acima EMA9
        elif simple_uptrend and is_green and price > ema9:
            signal = "CALL"
            desc = f"🔥 AGRESSIVO ALTA | EMA9 > EMA21 + verde"
        
        # PUT AGRESSIVO: EMA9 < EMA21 + vela vermelha + preço abaixo EMA9
        elif simple_downtrend and is_red and price < ema9:
            signal = "PUT"
            desc = f"🔥 AGRESSIVO BAIXA | EMA9 < EMA21 + vermelha"
        
        # =====================================================
        # PRIORIDADE 2: REVERSÃO EM S/R (apenas com padrão forte)
        # =====================================================
        
        if not signal:
            # Reversão em SUPORTE FORTE (pelo menos 3 toques)
            if at_support and support_strength >= 3:
                if is_hammer:
                    signal = "CALL"
                    desc = f"🔄 REVERSÃO SUPORTE | Hammer ({support_strength} toques)"
                elif is_engulf_bull:
                    signal = "CALL"
                    desc = f"🔄 REVERSÃO SUPORTE | Engolfo Alta ({support_strength} toques)"
                elif is_pinbar_bull:
                    signal = "CALL"
                    desc = f"🔄 REVERSÃO SUPORTE | Pin Bar Alta ({support_strength} toques)"
                elif doji_at_bottom:
                    signal = "CALL"
                    desc = f"⚠️ REVERSÃO SUPORTE | Doji ({support_strength} toques)"
            
            # Reversão em RESISTÊNCIA FORTE (pelo menos 3 toques)
            elif at_resistance and resistance_strength >= 3:
                if is_shooting:
                    signal = "PUT"
                    desc = f"🔄 REVERSÃO RESISTÊNCIA | Shooting Star ({resistance_strength} toques)"
                elif is_engulf_bear:
                    signal = "PUT"
                    desc = f"🔄 REVERSÃO RESISTÊNCIA | Engolfo Baixa ({resistance_strength} toques)"
                elif is_pinbar_bear:
                    signal = "PUT"
                    desc = f"🔄 REVERSÃO RESISTÊNCIA | Pin Bar Baixa ({resistance_strength} toques)"
                elif doji_at_top:
                    signal = "PUT"
                    desc = f"⚠️ REVERSÃO RESISTÊNCIA | Doji ({resistance_strength} toques)"
        
        if not signal:
            trend_txt = "ALTA" if is_uptrend else "BAIXA" if is_downtrend else "LATERAL"
            return None, f"⏳ {trend_txt} | Aguardando setup"
            
        return signal, desc

    def get_sr_zones(self, pair):
        """Retorna as zonas S/R analisadas para um par"""
        return self.sr_zones.get(pair, None)

    def on_win(self):
        self.consecutive_wins += 1

    def on_loss(self):
        self.consecutive_wins = 0
