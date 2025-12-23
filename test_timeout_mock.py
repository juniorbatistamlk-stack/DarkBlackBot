
import time
import threading
from api.iq_handler import IQHandler

# Mock Config
class MockConfig:
    def __init__(self):
        self.email = "test"
        self.password = "test"
        self.account_type = "PRACTICE"

# Mock API
class MockAPI:
    def get_candles(self, pair, timeframe, amount, now):
        print(f"Mock: requesting candles for {pair} (wait 12s)...")
        time.sleep(12) # Simula travamento maior que o timeout (10s)
        return [{"open": 1, "close": 2}] # Se retornar isso, falhou o teste

class MockIQHandler(IQHandler):
    def __init__(self):
        self.config = MockConfig()
        self.api = MockAPI()
        self.last_error = None
        self._lock = threading.Lock()
    
    def _ensure_connected(self):
        pass # Skip connect

def test_timeout():
    handler = MockIQHandler()
    print("Iniciando teste de timeout (expectativa: falha em 10s)...")
    start = time.time()
    
    # Chama get_candles que tem o wrapper de timeout
    params = handler.get_candles("EURUSD", 1, 100)
    
    elapsed = time.time() - start
    print(f"Tempo decorrido: {elapsed:.2f}s")
    print(f"Resultado: {params}")
    
    if elapsed < 11 and params == []:
        print("✅ SUCESSO: Timeout funcionou (retornou vazio em ~10s)")
    else:
        print("❌ FALHA: Não respeitou o timeout ou retornou dados")

if __name__ == "__main__":
    test_timeout()
