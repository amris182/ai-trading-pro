# utils.py
import numpy as np
import pandas as pd
import yfinance as yf

def calculate_rsi(prices, window=14):
    if len(prices) < window + 1:
        return np.array([])
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=window, min_periods=1).mean()
    avg_loss = pd.Series(loss).rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.dropna().values

def calculate_macd(prices, fast=8, slow=17, signal=9):
    if len(prices) < max(fast, slow) + signal + 5:
        return np.array([]), np.array([]), np.array([])
    prices_series = pd.Series(prices)
    exp1 = prices_series.ewm(span=fast, adjust=False).mean()
    exp2 = prices_series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.values, signal_line.values, histogram.values

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges.values, axis=1)
    return pd.Series(true_range).rolling(period).mean().values

def calculate_adx(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift())
    df['L-PC'] = abs(df['Low'] - df['Close'].shift())
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['DMplus'] = np.where((df['High'] - df['High'].shift()) > (df['Low'].shift() - df['Low']), 
                           np.maximum(df['High'] - df['High'].shift(), 0), 0)
    df['DMminus'] = np.where((df['Low'].shift() - df['Low']) > (df['High'] - df['High'].shift()), 
                            np.maximum(df['Low'].shift() - df['Low'], 0), 0)
    
    tr = df['TR'].rolling(period).sum()
    dm_plus = df['DMplus'].rolling(period).sum()
    dm_minus = df['DMminus'].rolling(period).sum()
    
    di_plus = 100 * dm_plus / tr
    di_minus = 100 * dm_minus / tr
    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
    adx = dx.rolling(period).mean()
    return adx.values, di_plus.values, di_minus.values