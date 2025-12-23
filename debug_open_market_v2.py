import os
import time
from api.iq_handler import IQHandler
from config import Config

# Force output unbuffer
import sys
sys.stdout.reconfigure(encoding='utf-8')

def debug_open_market():
    print("=== DEBUG OPEN MARKET ===")
    
    # 1. Setup
    cfg = Config()
    cfg.email = os.getenv("IQ_EMAIL") or input("Email: ")
    cfg.password = os.getenv("IQ_PASSWORD") or input("Senha: ")
    cfg.account_type = "PRACTICE" # FORCE PRACTICE
    cfg.option_type = "BEST"
    
    print("\n1. Conectando...")
    api = IQHandler(cfg)
    if not api.connect():
        print("Erro ao conectar.")
        return

    print("Conectado! Saldo:", api.get_balance())
    
    pair = "EURUSD"
    print(f"\n2. Verificando {pair}...")
    
    # Check Payouts
    all_profits = api.api.get_all_profit()
    if pair in all_profits:
        print(f"Info do par: {all_profits[pair]}")
    else:
        print("Par não encontrado em get_all_profit!")
        
    # Check Open Time
    print("Verificando se está aberto (is_open_v2)...")
    # This might use turbo internally
    is_open = api.api.get_all_open_time().get("turbo", {}).get(pair, {}).get("open", False)
    print(f"Turbo Open: {is_open}")
    
    is_open_bin = api.api.get_all_open_time().get("binary", {}).get(pair, {}).get("open", False)
    print(f"Binary Open: {is_open_bin}")

    # 3. Test Trade
    print("\n3. Tentando abrir ordem de TESTE (R$ 1.00)...")
    
    print("--- Tentativa 1: API BUY Padrão (M1) ---")
    start = time.time()
    check, id = api.buy(1.0, pair, "call", 1)
    end = time.time()
    print(f"Resultado: Check={check}, ID={id}")
    print(f"Tempo de execução: {end - start:.2f}s")
    
    if not check:
        print("\n--- Tentativa 2: Digital Spot (M1) ---")
        start = time.time()
        try:
            api.api.subscribe_strike_list(pair, 1)
            check, id = api.api.buy_digital_spot(pair, 1.0, "call", 1)
            end = time.time()
            print(f"Resultado Digital: Check={check}, ID={id}")
            print(f"Tempo de execução: {end - start:.2f}s")
        except Exception as e:
            print(f"Erro Digital: {e}")

if __name__ == "__main__":
    debug_open_market()
