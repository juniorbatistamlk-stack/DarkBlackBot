# utils/patterns.py
"""
Price Action Pattern Detection
Implements: Pin Bar, Engulfing, Fakeout, Inside Bar
"""

def is_pin_bar(candle, direction='any'):
    """
    Detect Pin Bar (Hammer or Shooting Star)
    
    Args:
        candle: Dict with OHLC
        direction: 'bullish' (hammer), 'bearish' (shooting star), or 'any'
    
    Returns:
        str or None: 'HAMMER', 'SHOOTING_STAR', or None
    """
    range_total = candle['high'] - candle['low']
    if range_total == 0:
        return None
    
    body = abs(candle['close'] - candle['open'])
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    
    # Body must be small
    if body > 0.35 * range_total:
        return None
    
    # HAMMER (Bullish Pin Bar)
    if direction in ['bullish', 'any']:
        if lower_wick >= 0.55 * range_total and upper_wick <= 0.25 * range_total:
            # Prefer green candle
            if candle['close'] >= candle['open']:
                return 'HAMMER'
    
    # SHOOTING STAR (Bearish Pin Bar)
    if direction in ['bearish', 'any']:
        if upper_wick >= 0.55 * range_total and lower_wick <= 0.25 * range_total:
            # Prefer red candle
            if candle['close'] <= candle['open']:
                return 'SHOOTING_STAR'
    
    return None

def is_engulfing(prev_candle, curr_candle):
    """
    Detect Engulfing Pattern
    
    Returns:
        str or None: 'BULLISH_ENGULFING', 'BEARISH_ENGULFING', or None
    """
    prev_body_top = max(prev_candle['open'], prev_candle['close'])
    prev_body_bot = min(prev_candle['open'], prev_candle['close'])
    
    curr_body_top = max(curr_candle['open'], curr_candle['close'])
    curr_body_bot = min(curr_candle['open'], curr_candle['close'])
    
    # BULLISH ENGULFING
    if curr_candle['close'] > curr_candle['open']:  # Current is green
        if prev_candle['close'] < prev_candle['open']:  # Previous was red
            # Current engulfs previous
            if curr_body_top >= prev_body_top and curr_body_bot <= prev_body_bot:
                return 'BULLISH_ENGULFING'
    
    # BEARISH ENGULFING
    if curr_candle['close'] < curr_candle['open']:  # Current is red
        if prev_candle['close'] > prev_candle['open']:  # Previous was green
            # Current engulfs previous
            if curr_body_top >= prev_body_top and curr_body_bot <= prev_body_bot:
                return 'BEARISH_ENGULFING'
    
    return None

def is_fakeout(zone, candle, direction):
    """
    Detect Fakeout (False Breakout)
    
    Args:
        zone: Dict with 'type', 'upper', 'lower'
        candle: Current candle
        direction: Expected fakeout direction ('support' or 'resistance')
    
    Returns:
        bool: True if fakeout detected
    """
    if direction == 'support':
        # Wick went below zone but closed above
        if candle['low'] < zone['lower'] and candle['close'] > zone['lower']:
            return True
    
    elif direction == 'resistance':
        # Wick went above zone but closed below
        if candle['high'] > zone['upper'] and candle['close'] < zone['upper']:
            return True
    
    return False

def is_inside_bar(prev_candle, curr_candle):
    """
    Detect Inside Bar (compression pattern)
    
    Returns:
        bool: True if inside bar
    """
    if curr_candle['high'] <= prev_candle['high'] and curr_candle['low'] >= prev_candle['low']:
        return True
    return False

def validate_confirmation(pattern_candle, confirmation_candle, pattern_type, direction):
    """
    Validate N+1 confirmation candle
    
    Args:
        pattern_candle: The candle where pattern was detected
        confirmation_candle: The next candle (N+1)
        pattern_type: Type of pattern detected
        direction: Expected direction ('CALL' or 'PUT')
    
    Returns:
        bool: True if confirmed
    """
    if direction == 'CALL':
        # For buy, confirmation must close above pattern high or above midpoint
        pattern_mid = (pattern_candle['high'] + pattern_candle['low']) / 2
        if confirmation_candle['close'] > pattern_candle['high']:
            return True
        if confirmation_candle['close'] > pattern_mid and confirmation_candle['close'] > confirmation_candle['open']:
            return True
    
    elif direction == 'PUT':
        # For sell, confirmation must close below pattern low or below midpoint
        pattern_mid = (pattern_candle['high'] + pattern_candle['low']) / 2
        if confirmation_candle['close'] < pattern_candle['low']:
            return True
        if confirmation_candle['close'] < pattern_mid and confirmation_candle['close'] < confirmation_candle['open']:
            return True
    
    return False
