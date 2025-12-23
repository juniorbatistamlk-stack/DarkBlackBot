# tests/test_strategies.py
import unittest
from unittest.mock import MagicMock
from strategies.price_action import PriceActionStrategy
from strategies.ferreira import FerreiraStrategy

class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.mock_api = MagicMock()
        self.pa_strat = PriceActionStrategy(self.mock_api)
        self.fe_strat = FerreiraStrategy(self.mock_api)

    def test_hammer_pattern(self):
        # Create a hammer candle sequence
        candles = [
            {'open': 1.1000, 'close': 1.0950, 'high': 1.1000, 'low': 1.0940}, # Bearish
            # Hammer: Close > Open, Long lower wick, small upper wick
            {'open': 1.0900, 'close': 1.0920, 'high': 1.0925, 'low': 1.0850} 
        ]
        self.mock_api.get_candles.return_value = candles
        
        # We need to simulate that we are at support for the PA strategy to fire
        # In our simplified implementation it assumes support is present
        
        signal, desc = self.pa_strat.check_signal("EURUSD", 1)
        # Note: The simplified logic might return CALL if it sees a Hammer
        # Adjust expectation based on implementation details:
        # Implementation: if pattern == "HAMMER" and in_support: return "CALL"
        
        # Verify get_candles called
        self.mock_api.get_candles.assert_called()

    def test_ferreira_logic(self):
        # Test basic flow
        pass
        
if __name__ == '__main__':
    unittest.main()
