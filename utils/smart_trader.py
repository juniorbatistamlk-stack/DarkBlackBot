# utils/smart_trader.py
"""
Sistema de Trading Inteligente - Profissional
Analisa multiplos pares e prioriza o melhor sinal
COM VALIDAÇÃO DE IA INTEGRADA E APRENDIZADO
"""
import time
from datetime import datetime
from utils.trade_history import TradeHistory

class SmartTrader:
    def __init__(self, api, strategy, pairs, memory, pair_rankings=None, ai_analyzer=None):
        """
        Args:
            api: IQHandler
            strategy: Instancia da estrategia
            pairs: Lista de paridades
            memory: TradingMemory
            pair_rankings: Dict com win_rate por par (do backtest)
            ai_analyzer: AIAnalyzer para validacao com IA
        """
        self.api = api
        self.strategy = strategy
        self.pairs = pairs
        self.memory = memory
        self.pair_rankings = pair_rankings or {}
        self.ai_analyzer = ai_analyzer
        self.is_trading = False  # Lock para 1 trade por vez
        self.current_trade = None
        self.system_log_func = None  # Função para logs do sistema (IA/IQ)
        
        # Sistema de aprendizado
        self.trade_history = TradeHistory()
    
    def set_system_logger(self, log_func):
        """Define função para logar mensagens do sistema (IA, IQ)"""
        self.system_log_func = log_func
    
    def _log_system(self, msg):
        """Loga no painel de sistema"""
        if self.system_log_func:
            self.system_log_func(msg)
        else:
            pass # Evitar print direto para não quebrar UI

        
    def analyze_all_pairs(self, timeframe):
        """
        Analisa todos os pares e retorna o melhor sinal
        
        Returns:
            dict: {pair, signal, desc, confidence} ou None
        """
        signals = []
        
        for pair in self.pairs:
            signal, desc = self.strategy.check_signal(pair, timeframe)
            
            if signal:
                # Calcular confianca baseado em:
                # 1. Backtest win rate (40%)
                # 2. Memoria historica (30%)
                # 3. Forca do padrao (30%)
                
                base_confidence = 50
                
                # Bonus do backtest
                backtest_rate = self.pair_rankings.get(pair, 50)
                if backtest_rate is None: backtest_rate = 50
                backtest_bonus = (backtest_rate - 50) * 0.4  # +/- 20 pontos max
                
                # Bonus da memoria
                pattern = desc.split("|")[0].strip() if "|" in desc else desc
                memory_rate = self.memory.get_pattern_confidence(pattern)
                memory_bonus = (memory_rate - 50) * 0.3  # +/- 15 pontos max
                
                # Bonus do padrao (extrair do desc se possivel)
                pattern_bonus = 0
                if "REVERSAO" in desc.upper():
                    pattern_bonus = 10  # Reversoes tendem a ser mais confiaveis
                elif "TENDENCIA" in desc.upper():
                    pattern_bonus = 5
                
                final_confidence = base_confidence + backtest_bonus + memory_bonus + pattern_bonus
                final_confidence = max(20, min(95, final_confidence))
                
                signals.append({
                    "pair": pair,
                    "signal": signal,
                    "desc": desc,
                    "pattern": pattern,
                    "confidence": final_confidence,
                    "backtest_rate": backtest_rate
                })
        
        if not signals:
            return None
        
        # Ordenar por confianca (maior primeiro)
        signals.sort(key=lambda x: x["confidence"], reverse=True)
        
        best = signals[0]
        
        # VERIFICAR APRENDIZADO - Evitar padrões que dão loss
        pattern = best.get("pattern", best.get("desc", ""))
        if self.trade_history.should_avoid_pattern(pattern):
            self._log_system(f"[AI] ⚠️ Padrão '{pattern[:20]}' tem histórico ruim - pulando...")
            if len(signals) > 1:
                best = signals[1]
            else:
                return None
        
        # VALIDAÇÃO COM IA (se disponível)
        if self.ai_analyzer:
            # Obter contexto de aprendizado
            learning = self.trade_history.get_learning_summary()
            self._log_system(f"[AI] Analisando gráfico de {best['pair']}...")
            self._log_system(f"[AI] Histórico: {learning['total_trades']} trades | WR: {learning['win_rate']:.0f}%")
            
            if learning['avoid_patterns']:
                self._log_system(f"[AI] ⚠️ Evitando: {', '.join(learning['avoid_patterns'][:3])}")
            
            candles = self.api.get_candles(best["pair"], 1, 30)
            zones = []  # Zonas S/R
            trend = "UPTREND" if best.get("trend") == "BULLISH" else "DOWNTREND"
            
            # Chamar IA para validar
            ai_confirm, ai_confidence, ai_reason = self.ai_analyzer.analyze_signal(
                best["signal"], best["desc"], candles, zones, trend, best["pair"]
            )
            
            if not ai_confirm:
                self._log_system(f"[AI] ❌ Rejeitado: {ai_reason}")
                # IA rejeitou - tentar próximo sinal
                if len(signals) > 1:
                    best = signals[1]
                    best["ai_rejected"] = True
                    best["ai_reason"] = ai_reason
                else:
                    return None  # Sem sinais válidos
            else:
                self._log_system(f"[AI] ✅ Confirmado ({ai_confidence}%): {ai_reason}")
                # IA confirmou - usar confiança da IA
                best["confidence"] = (best["confidence"] + ai_confidence) / 2
                best["ai_reason"] = ai_reason
        
        return best
    
    def execute_trade(self, trade_info, cfg, log_func):
        """
        Executa um trade e aguarda resultado
        
        Args:
            trade_info: Dict com pair, signal, desc, confidence
            cfg: Config
            log_func: Funcao de log
            
        Returns:
            float: Lucro/prejuizo
        """
        # Garantir que lock sempre seja liberado
        try:
            # Reset lock no início para evitar travamento
            self.is_trading = False
            
            # VERIFICAR CONEXÃO ANTES DE EXECUTAR
            self._log_system("[IQ] 🔍 Verificando saúde da conexão...")
            if not self.api._ensure_connected():
                log_func("[bold red]❌ FALHA: Não foi possível estabelecer conexão[/bold red]")
                log_func("[yellow]⚠️ Verifique sua internet e tente novamente[/yellow]")
                return 0
            
            self._log_system("[IQ] ✓ Conexão verificada: OK")
            
            self.is_trading = True
            self.current_trade = trade_info
            
            pair = trade_info["pair"]
            signal = trade_info["signal"]
            desc = trade_info.get("desc", "")
            confidence = trade_info.get("confidence", 50)
            pattern = trade_info.get("pattern", desc)
            
            log_func(f"[green]💰 Executando ordem [{cfg.option_type}]: {signal} em {pair} (R${cfg.amount:.2f})[/green]")
            
            try:
                # Executar trade
                self._log_system(f"[IQ] Tentando: {pair} {signal}...")
                check, order_id = self.api.buy(cfg.amount, pair, signal, cfg.timeframe)
                
                self._log_system(f"[IQ] Resposta: check={check}, id={order_id}")
                
                if check:
                    log_func(f"[green]✓ Ordem {order_id} aberta em {pair}. Aguardando resultado...[/green]")
                    
                    # Aguardar resultado
                    result = self.api.check_win(order_id)
                    
                    if result > 0:
                        log_func(f"[bold green]✅ WIN +R${result:.2f} | {pair}[/bold green]")
                        self.memory.record_trade(pair, signal, pattern, "WIN", result, "UNKNOWN")
                        
                        # Salvar para aprendizado da IA
                        self.trade_history.add_trade(trade_info, "win", result)
                        
                        return result
                        
                    elif result < 0:
                        log_func(f"[red]❌ LOSS -R${abs(result):.2f} | {pair}[/red]")
                        self.memory.record_trade(pair, signal, pattern, "LOSS", result, "UNKNOWN")
                        
                        # Salvar para aprendizado da IA
                        self.trade_history.add_trade(trade_info, "loss", result)
                        log_func(f"[magenta]🧠 IA aprendendo com este loss...[/magenta]")
                        
                        # Martingale
                        martingale_profit = self._execute_martingale(
                            cfg, pair, signal, pattern, log_func
                        )
                        
                        return result + martingale_profit
                    else:
                        log_func(f"[yellow]🤝 EMPATE | {pair}[/yellow]")
                        return 0
                else:
                    log_func(f"[bold red]❌ FALHA AO ABRIR ORDEM[/bold red]")
                    log_func(f"[red]Motivo: {order_id}[/red]")
                    
                    # Mensagens específicas para erros comuns
                    error_lower = str(order_id).lower()
                    if "socket" in error_lower or "closed" in error_lower:
                        log_func(f"[yellow]🔄 Erro de conexão detectado. O sistema tentará reconectar...[/yellow]")
                    elif "timeout" in error_lower:
                        log_func(f"[yellow]⏱️ Timeout: Operação demorou muito. Tente novamente.[/yellow]")
                    else:
                        log_func(f"[yellow]Verifique: Saldo, Ativo aberto, Limite de trades[/yellow]")
                    
                    return 0
                    
            except ConnectionError as e:
                log_func(f"[bold red]❌ ERRO DE CONEXÃO: {str(e)}[/bold red]")
                log_func(f"[yellow]🔄 Tentando reconectar...[/yellow]")
                self.api._ensure_connected()
                return 0
            except Exception as e:
                log_func(f"[bold red]❌ ERRO CRÍTICO: {str(e)}[/bold red]")
                import traceback
                error_trace = traceback.format_exc()
                
                # Logar apenas se for erro de socket
                if "socket" in error_trace.lower():
                    log_func(f"[yellow]🔄 Erro de WebSocket detectado. Reconectando...[/yellow]")
                    self.api._ensure_connected()
                else:
                    log_func(f"[dim]{error_trace}[/dim]")
                
                return 0
        finally:
            # SEMPRE liberar o lock, mesmo se der erro
            self.is_trading = False
    
    def _execute_martingale(self, cfg, pair, signal, pattern, log_func):
        """Executa martingale com timing preciso (Server Side)"""
        total_profit = 0
        curr_amount = cfg.amount
        
        for level in range(cfg.martingale_levels):
            # Calcular valor do Gale (Fator 2.2 padrão)
            curr_amount *= 2.2
            
            log_func(f"[yellow]🔄 GALE {level+1}: R${curr_amount:.2f} | Aguardando ponto de entrada...[/yellow]")
            
            # === SMART TIMING LOGIC ===
            # Tentar entrar na vela IMEDIATA se ainda estiver no início (Tolerance 0s-4s)
            # Se perdeu a entrada (delay > 4s), esperar a proxima vela cheia.
            
            candle_duration = cfg.timeframe * 60
            server_time = self.api.api.get_server_timestamp()
            
            # Normalizar para tempo decorrido na vela atual
            # Ex: 10:05:02 -> elapsed = 2
            current_elapsed = server_time % candle_duration
            
            if current_elapsed <= 4:
                # Estamos no início da vela (Janela de Tolerância) -> Entrar JÁ!
                log_func(f"[green]⚡ GALE IMEDIATO (Janela {current_elapsed}s)[/green]")
            else:
                # Passou do tempo, esperar a próxima vela
                seconds_remaining = candle_duration - current_elapsed
                wait_time = seconds_remaining # Espera até bater 00 da próxima
                
                log_func(f"[dim]Janela perdida ({current_elapsed}s). Aguardando {wait_time}s para próxima vela...[/dim]")
                
                # Loop de espera preciso (Server Side)
                target_timestamp = server_time + wait_time
                while True:
                    now = self.api.api.get_server_timestamp()
                    rem = target_timestamp - now
                    if rem <= 0:
                        break
                    # Log periódico se for longo
                    if rem > 10 and rem % 10 == 0:
                         log_func(f"[dim]Gale em {rem}s...[/dim]")
                    time.sleep(0.5)
                    
                log_func(f"[green]⚡ GALE DISPARADO (Nova Vela)[/green]")
            
            # Executar gale
            check, order_id = self.api.buy(curr_amount, pair, signal, cfg.timeframe)
            
            if check:
                log_func(f"[dim]Gale {level+1} executado ({order_id}). Aguardando...[/dim]")
                result = self.api.check_win(order_id)
                
                if result > 0:
                    log_func(f"[bold green]✅ GALE WIN +R${result:.2f}[/bold green]")
                    self.memory.record_trade(pair, signal, f"GALE_{level+1}_{pattern}", "WIN", result, "UNKNOWN")
                    total_profit += result
                    break
                else:
                    log_func(f"[red]❌ GALE LOSS -R${abs(result):.2f}[/red]")
                    self.memory.record_trade(pair, signal, f"GALE_{level+1}_{pattern}", "LOSS", result, "UNKNOWN")
                    total_profit += result
                    # Continua para o próximo nível do loop
            else:
                log_func(f"[red]Erro ao entrar no Gale[/red]")
                break
        
        return total_profit
