# strategies/base_strategy.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, api_handler, ai_analyzer=None):
        self.api = api_handler
        self.name = "Base Strategy"
        self.ai_analyzer = ai_analyzer
        
    @abstractmethod
    def check_signal(self, pair, timeframe):
        """
        Analyzes candles and returns a signal.
        Returns: 
            tuple: (action, description) 
            action: 'CALL', 'PUT', or None
        """
        pass
    
    def validate_with_ai(self, signal, desc, candles, zones, trend, pair):
        """
        Valida sinal com IA se disponível
        Returns: (should_trade, confidence, ai_reason)
        """
        if not self.ai_analyzer:
            return True, 100, "AI desabilitada"
        
        return self.ai_analyzer.analyze_signal(signal, desc, candles, zones, trend, pair)
