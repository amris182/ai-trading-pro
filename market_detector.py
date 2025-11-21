# market_detector.py
import numpy as np
import pandas as pd
from utils import calculate_atr, calculate_adx

def detect_market_condition(prices, highs, lows, closes, atr_vals, adx_vals):
    ema50 = pd.Series(prices).ewm(span=50, adjust=False).mean().values
    ema200 = pd.Series(prices).ewm(span=200, adjust=False).mean().values
    
    current_ema50 = ema50[-1]
    current_ema200 = ema200[-1]
    current_adx = adx_vals[-1] if len(adx_vals) > 0 else 0
    
    if current_adx > 20:
        if current_ema50 > current_ema200:
            return "BULLISH"
        else:
            return "BEARISH"
    else:
        return "SIDEWAYS"

def get_trading_strategy(condition):
    if condition == "BULLISH":
        return {
            "strategy": "Trend Following",
            "hold_time": 24,
            "tp_multiplier": 3.0,
            "sl_multiplier": 1.0,
            "max_positions": 1
        }
    elif condition == "BEARISH":
        return {
            "strategy": "Wait & See",
            "hold_time": 0,
            "tp_multiplier": 0,
            "sl_multiplier": 0,
            "max_positions": 0
        }
    elif condition == "SIDEWAYS":
        return {
            "strategy": "Scalping",
            "hold_time": 2,
            "tp_multiplier": 0.8,
            "sl_multiplier": 0.8,
            "max_positions": 2
        }
    else:
        return {
            "strategy": "Unknown",
            "hold_time": 6,
            "tp_multiplier": 2.0,
            "sl_multiplier": 1.5,
            "max_positions": 1
        }