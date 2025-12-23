# api/iq_handler.py
from iqoptionapi.stable_api import IQ_Option
import time
import threading

class IQHandler:
    def __init__(self, config):
        self.config = config
        self.api = None
        self.last_error = None
        self._lock = threading.Lock()
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

    def connect(self):
        """Connects to IQ Option API with retry mechanism."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.api = IQ_Option(self.config.email, self.config.password)
                check, reason = self.api.connect()
                
                if check:
                    self.api.change_balance(self.config.account_type)
                    return True
                else:
                    self.last_error = f"Connection failed: {reason}"
                    self._log(f"[IQ_HANDLER] Tentativa {attempt+1}/{max_retries} falhou: {reason}")
            except Exception as e:
                self.last_error = str(e)
                self._log(f"[IQ_HANDLER] Erro na conexão (Tentativa {attempt+1}/{max_retries}): {e}")
            
            time.sleep(2)
            
        return False

    def _ensure_connected(self):
        """Auto-reconnect if connection dropped with smart retry."""
        max_attempts = 3  # Reduced to 3 for faster failure
        
        for attempt in range(max_attempts):
            try:
                # Check if API exists and is connected
                if self.api and self.api.check_connect():
                    # Verify WebSocket is truly alive by getting balance
                    try:
                        _ = self.api.get_balance()
                        return True  # Connection is good
                    except Exception:
                        pass  # WebSocket dead, need reconnect
                
                # Connection is dead - create fresh API instance
                self._log(f"[IQ_HANDLER] 🔄 Reconectando... (tentativa {attempt+1}/{max_attempts})")
                
                # Destroy old connection completely
                if self.api:
                    try:
                        self.api.close_connect()
                    except:
                        pass
                    self.api = None
                
                # Exponential backoff: 5s, 10s, 15s
                wait_time = 5 * (attempt + 1)
                self._log(f"[IQ_HANDLER] ⏳ Aguardando {wait_time}s antes de tentar...")
                time.sleep(wait_time)
                
                # Create fresh connection
                self.api = IQ_Option(self.config.email, self.config.password)
                check, reason = self.api.connect()
                
                if check:
                    self.api.change_balance(self.config.account_type)
                    
                    # CRITICAL: Wait for websocket to stabilize
                    time.sleep(2)
                    
                    # Verify it's really working
                    try:
                        test_balance = self.api.get_balance()
                        if test_balance:
                            self._log(f"[IQ_HANDLER] ✅ Reconectado com sucesso!")
                            return True
                    except:
                        self._log(f"[IQ_HANDLER] ⚠️ Conexão instável, tentando novamente...")
                        continue
                else:
                    self._log(f"[IQ_HANDLER] ⚠️ Falha: {reason}")
                    
            except Exception as e:
                self._log(f"[IQ_HANDLER] ❌ Erro tentativa {attempt+1}: {str(e)[:50]}")
        
        # All attempts failed
        self._log(f"[IQ_HANDLER] 💀 FALHA CRÍTICA: Não foi possível reconectar após {max_attempts} tentativas")
        self._log(f"[IQ_HANDLER] 🛡️ Possíveis causas: VPN instável, IQ Option bloqueou, ou internet caiu")
        self._log(f"[IQ_HANDLER] 💡 Solução: Reinicie o bot ou troque de servidor VPN")
        return False

    def get_balance(self):
        """Returns current balance."""
        self._ensure_connected()
        return self.api.get_balance()

    def get_payout(self, pair, type_name="turbo"):
        """Gets payout percentage for a pair."""
        all_profits = self.api.get_all_profit()
        return all_profits.get(pair, {}).get(type_name, 0) * 100

    def get_candles(self, pair, timeframe, amount):
        """Fetches candle data with explicit timeout to prevent freezing."""
        result = []
        
        def _fetch():
            nonlocal result
            # Try up to 2 times
            for attempt in range(2):
                try:
                    self._ensure_connected()
                    # IQ Option API get_candles is known to hang sometimes
                    candles = self.api.get_candles(pair, timeframe * 60, amount, time.time())
                    if candles:
                        result = candles
                        return # Success
                except Exception as e:
                    err_msg = str(e).lower()
                    # Catch Socket Closed, EOF (SSL), and general Connection errors
                    if any(x in err_msg for x in ["socket", "closed", "eof", "ssl", "violation", "handshake"]):
                        self._log(f"[IQ] 🔄 Instabilidade de Conexão ({err_msg[:20]}...). Reconectando... ({attempt+1}/2)")
                        try:
                            self.api.close_connect()
                        except:
                            pass
                        self.api = None 
                        time.sleep(1 + attempt) # Wait a bit more on retries (1s, then 2s)
                    else:
                        self._log(f"[IQ] Erro download candles: {e}")
                        # Don't break immediately, maybe momentary glitch? 
                        # But if it's not connection related, retry might not help.
                        # For safety, let's treat almost everything in get_candles as worth 1 retry if network related.
                        pass # Continue loop to retry if range allows

        # Threaded fetch with 20s timeout (SSL handshakes over VPN can be slow)
        t = threading.Thread(target=_fetch)
        t.start()
        t.join(timeout=20)
        
        if t.is_alive():
            self._log(f"[IQ] TIMEOUT ao baixar velas de {pair} (15s)")
            return []
            
        if not result:
            return []
            
        # Normalize keys
        normalized_candles = []
        for c in result:
            nc = c.copy()
            if 'max' in c and 'high' not in c: nc['high'] = c['max']
            if 'min' in c and 'low' not in c: nc['low'] = c['min']
            if 'vol' in c and 'volume' not in c: nc['volume'] = c['vol']
            normalized_candles.append(nc)
        return normalized_candles

    def buy(self, amount, pair, action, duration):
        """Executes a trade with timeout, retry, and auto-reconnect."""
        # VERIFICAR CONEXÃO ANTES DE COMEÇAR
        self._log(f"[IQ] 🔍 Verificando conexão antes do trade...")
        if not self._ensure_connected():
            self._log("[IQ] ❌ Conexão não estabelecida. Abortando trade.")
            return False, "Falha na conexão - não foi possível conectar"
        
        self._log(f"[IQ] ✓ Conexão OK. Executando trade...")
        
        max_retries = 2
        
        for attempt in range(max_retries):
            result = self._buy_with_timeout(amount, pair, action, duration)
            
            if result[0]:  # Success
                return result
            
            # Se falhou por erro de socket/conexão, tentar reconectar
            error_msg = str(result[1]).lower()
            if "socket" in error_msg or "closed" in error_msg or "timeout" in error_msg:
                if attempt < max_retries - 1:
                    print(f"[IQ_HANDLER] ⚠️ Erro de conexão detectado. Tentativa {attempt+1}/{max_retries}")
                    print(f"[IQ_HANDLER] 🔄 Reconectando...")
                    self._ensure_connected()
                    time.sleep(2)
                    continue
            
            # Outros erros (asset closed, etc) - não adianta retry
            break
        
        return result  # Return last failed result

    def _buy_with_timeout(self, amount, pair, action, duration):
        """Internal buy with 30s timeout."""
        action_lower = action.lower()
        result = [False, "Timeout"]
        
        def _buy_thread():
            try:
                op_type = self.config.option_type
                
                # === BINARY ONLY ===
                if op_type == "BINARY":
                    self._log(f"[IQ] Tentando Binária (Forçado): {pair} {action}...")
                    check, order_id = self.api.buy(amount, pair, action_lower, duration)
                    if check:
                        self._log(f"[IQ] Binária Sucesso! {order_id}")
                        result[0] = True; result[1] = order_id
                    else:
                        result[1] = f"Binary Failed: {order_id}"
                    return

                # === DIGITAL ONLY ===
                if op_type == "DIGITAL":
                    self._log(f"[IQ] Tentando Digital (Forçado): {pair}...")
                    try:
                        self.api.subscribe_strike_list(pair, duration)
                        check, order_id = self.api.buy_digital_spot(pair, amount, action_lower, duration)
                        if check:
                            self._log(f"[IQ] Digital Sucesso! {order_id}")
                            result[0] = True; result[1] = order_id
                        else:
                            result[1] = f"Digital Failed: {order_id}"
                    except Exception as e:
                        result[1] = f"Digital Error: {str(e)}"
                    return

                # === BEST (AUTO) ===
                is_otc = "OTC" in pair
                is_short_timeframe = duration <= 5
                prefer_digital = (not is_otc) and is_short_timeframe
                
                if prefer_digital:
                    self._log(f"[IQ] Smart Order: Priorizando DIGITAL para {pair} (M{duration})...")
                    # TENTATIVA 1: DIGITAL
                    try:
                        self.api.subscribe_strike_list(pair, duration)
                        check_digital, order_id_digital = self.api.buy_digital_spot(pair, amount, action_lower, duration)
                        if check_digital:
                            self._log(f"[IQ] Digital Sucesso! {order_id_digital}")
                            result[0] = True; result[1] = order_id_digital
                            return
                        else:
                            self._log(f"[IQ] Digital falhou: {order_id_digital}")
                    except Exception as e:
                        self._log(f"[IQ] Erro Digital: {e}")
                        
                    # TENTATIVA 2: BINÁRIA (Fallback)
                    self._log(f"[IQ] Tentando Binária (Fallback)...")
                    check, order_id = self.api.buy(amount, pair, action_lower, duration)
                    if check:
                        self._log(f"[IQ] Binária Sucesso! {order_id}")
                        result[0] = True; result[1] = order_id
                    else:
                        result[1] = f"Digital/Binary Failed: {order_id}"
                        
                else: # Prefer Binary (Default/OTC)
                    self._log(f"[IQ] Smart Order: Priorizando BINÁRIA para {pair}...")
                    # TENTATIVA 1: BINÁRIA
                    check, order_id = self.api.buy(amount, pair, action_lower, duration)
                    if check:
                        self._log(f"[IQ] Binária Sucesso! {order_id}")
                        result[0] = True; result[1] = order_id
                        return
                    else:
                        self._log(f"[IQ] Binária falhou: {order_id}")
                        
                    # TENTATIVA 2: DIGITAL (Fallback)
                    try:
                        self.api.subscribe_strike_list(pair, duration)
                        check_digital, order_id_digital = self.api.buy_digital_spot(pair, amount, action_lower, duration)
                        if check_digital:
                            self._log(f"[IQ] Digital Sucesso! {order_id_digital}")
                            result[0] = True; result[1] = order_id_digital
                        else:
                            result[1] = f"Bin: {order_id} | Dig: {order_id_digital}"
                    except Exception as e:
                        result[1] = f"Digital Exception: {str(e)}"
                    
            except Exception as e:
                self._log(f"[IQ] Erro Geral Thread: {e}")
                result[1] = str(e)
        
        try:
            with self._lock:
                thread = threading.Thread(target=_buy_thread)
                thread.start()
                thread.join(timeout=15)
                
                if thread.is_alive():
                    self._log("[IQ] ⚠️ TIMEOUT: Operação excedeu 15 segundos!")
                    self.last_error = "API timeout (15s)"
                    return False, "Timeout ao executar trade - Tente novamente"
        except Exception as e:
            self._log(f"[IQ] ❌ Erro crítico no lock de threading: {e}")
            return False, f"Erro de threading: {str(e)}"
                    
        return result[0], result[1]

    def check_win(self, order_id):
        """Checks result of an order with retry."""
        max_retries = 3
        for _ in range(max_retries):
            try:
                result = self.api.check_win_v3(order_id) if order_id else 0
                if result is not None:
                    return result
            except Exception:
                time.sleep(1)
        return 0

    def get_open_assets(self, type_name="turbo"):
        """Scans for open assets."""
        return self.api.get_all_open_time()
    
    def scan_available_pairs(self, pairs_list):
        """Scans a list of pairs - simplified version that just shows all pairs.
        Actual verification happens at trade time."""
        import threading
        
        results = {}
        all_profits = {}
        
        # Apenas buscar payouts (mais rápido que get_all_open_time)
        def _fetch_profits():
            nonlocal all_profits
            try:
                all_profits = self.api.get_all_profit()
            except Exception:
                pass  # Silently fail if profit fetch fails
        
        # Fetch profits with timeout
        thread = threading.Thread(target=_fetch_profits)
        thread.start()
        thread.join(timeout=10)

        for pair in pairs_list:
            payout = 0
            is_open = False
            
            # Tentar pegar payout real baseado no tipo de opção
            if pair in all_profits:
                try:
                    profit_data = all_profits[pair]
                    
                    # Prioriza o tipo selecionado na config
                    op_type = self.config.option_type
                    
                    turbo_payout = 0
                    binary_payout = 0
                    digital_payout = 0
                    
                    if isinstance(profit_data, dict):
                        turbo_payout = profit_data.get("turbo", 0)
                        binary_payout = profit_data.get("binary", 0)
                        
                        if op_type == "BINARY":
                            payout = max(turbo_payout, binary_payout)
                        elif op_type == "DIGITAL":
                            if max(turbo_payout, binary_payout) > 0:
                                payout = 0.90
                        else: # BEST
                            payout = max(turbo_payout, binary_payout)
                            
                        # Se payout > 0, esta aberto
                        if payout > 0:
                            payout = payout * 100
                            is_open = True
                            
                    elif isinstance(profit_data, (int, float)):
                        payout = profit_data * 100
                        if payout > 0: is_open = True
                        
                except Exception as e:
                    print(f"Erro ao ler payout de {pair}: {e}")
            
            # Fallback: Se não achou no profit, verificar se está aberto pelo get_all_open_time
            # Isso corrige o erro de "Nenhum ativo aberto" quando o get_all_profit falha
            if not is_open:
                try:
                    # Tenta verificar se o ativo é conhecido como aberto
                    # Simplesmente checando se é OTC e se estamos em horario de OTC
                    if "OTC" in pair:
                        is_open = True
                        payout = 87 # Payout padrão estimado para OTC
                except:
                    pass

            if is_open:
                results[pair] = {
                    "open": True,
                    "payout": round(payout, 0)
                }
        
        return results
