"""
Script de teste para diagnosticar problema de sinais
"""
import sys
sys.path.insert(0, '.')

from api.iq_handler import IQHandler
from strategies.alavancagem import AlavancagemStrategy
from config import Config

# Configuração de teste
cfg = Config()
cfg.email = input("Email IQ Option: ")
cfg.password = input("Senha: ")
cfg.account_type = "PRACTICE"

# Conectar
api = IQHandler(cfg)
print("Conectando...")
if not api.connect():
    print("ERRO: Falha na conexão!")
    exit()

print(f"✓ Conectado! Banca: ${api.get_balance()}")

# Testar get_candles
print("\n=== TESTE 1: Buscar Velas ===")
pairs_to_test = ["EURUSD", "EURUSD-OTC", "USDCAD-OTC"]

for pair in pairs_to_test:
    print(f"\nTestando {pair}...")
    candles = api.get_candles(pair, 1, 10)
    
    if not candles:
        print(f"  ❌ ERRO: Nenhuma vela retornada!")
        continue
    
    print(f"  ✓ {len(candles)} velas recebidas")
    
    # Mostrar última vela
    last = candles[-1]
    body = abs(last['close'] - last['open'])
    range_total = last['high'] - last['low']
    body_ratio = (body / range_total * 100) if range_total > 0 else 0
    
    print(f"  Última vela:")
    print(f"    Open: {last['open']:.5f}")
    print(f"    Close: {last['close']:.5f}")
    print(f"    High: {last['high']:.5f}")
    print(f"    Low: {last['low']:.5f}")
    print(f"    Corpo: {body_ratio:.1f}%")
    print(f"    Verde: {last['close'] > last['open']}")

# Testar estratégia
print("\n=== TESTE 2: Estratégia ===")
strategy = AlavancagemStrategy(api)

for pair in pairs_to_test:
    print(f"\nTestando estratégia em {pair}...")
    signal, desc = strategy.check_signal(pair, 1)
    
    if signal:
        print(f"  🚀 SINAL: {signal}")
        print(f"  Descrição: {desc}")
    else:
        print(f"  ⏳ Sem sinal: {desc}")

print("\n=== FIM DOS TESTES ===")
