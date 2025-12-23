# config.py

class Config:
    def __init__(self):
        self.email = ""
        self.password = ""
        self.account_type = "PRACTICE"  # PRACTICE or REAL
        self.option_type = "BINARY"     # BINARY, DIGITAL, or BEST
        self.balance = 0.0
        
        # Trading Settings
        self.asset = "EURUSD"
        self.timeframe = 5  # 1 for M1, 5 for M5, etc. (Default: M5 - Recommended)
        self.amount = 10.0
        self.martingale_levels = 2
        self.stop_win = 50.0
        self.stop_loss = 50.0
        
        # Active Strategy
        self.strategy_name = "Ferreira Trader"
        
        # System
        self.check_interval = 1 # Seconds to wait in loop
        self.anti_delay = 0 # Seconds to wait before entry (Anti-Gap)
        
        # Goals
        self.profit_goal = 0.0  # Meta de lucro (0 = sem meta)
        
        # AI Configuration
        self.use_ai = True  # Usar IA para validar sinais
        self.groq_api_key = ""  # API Key da Groq
