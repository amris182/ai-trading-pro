# app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import time
import requests
import sys
import os

# === FUNGSI ANALISA (copy dari utils.py) ===
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

# === NOTIFIKASI TELEGRAM ===
TELEGRAM_BOT_TOKEN = "8533608567:AAGufuGiJfT3VkKVlKNHotHXmTM8Nk7A76M"  # GANTI DENGAN BOT TOKEN KAMU
TELEGRAM_CHAT_ID = "502261190"    # GANTI DENGAN CHAT ID KAMU

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("❌ Telegram token/ID belum diisi")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print(f"[INFO] Telegram: {message}")
            return True
        else:
            st.error(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        st.error(f"❌ Telegram exception: {e}")
        return False

def test_telegram():
    """Test koneksi Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ Test Notifikasi Berhasil!"}
        response = requests.post(url, data=data)
        return response.status_code == 200
    except:
        return False

# === DETEKSI POLA REVERSAL (copy dari pattern_detection.py) ===
def detect_double_top(prices, threshold=0.02):
    if len(prices) < 20:
        return False
    
    peaks = []
    for i in range(5, len(prices)-5):
        if (prices[i] > max(prices[max(0, i-5):i]) and 
            prices[i] > max(prices[i+1:min(len(prices), i+6)]) and
            prices[i] > np.mean(prices) * 1.05):
            peaks.append((i, prices[i]))
    
    if len(peaks) < 2:
        return False
    
    peak1_idx, peak1_price = peaks[-2]
    peak2_idx, peak2_price = peaks[-1]
    
    if peak2_idx - peak1_idx > 30:
        return False
    
    if abs(peak1_price - peak2_price) / max(peak1_price, peak2_price) < threshold:
        valley = min(prices[peak1_idx:peak2_idx])
        if valley < peak1_price * 0.97:
            return True
    
    return False

def detect_double_bottom(prices, threshold=0.02):
    if len(prices) < 20:
        return False
    
    bottoms = []
    for i in range(5, len(prices)-5):
        if (prices[i] < min(prices[max(0, i-5):i]) and 
            prices[i] < min(prices[i+1:min(len(prices), i+6)]) and
            prices[i] < np.mean(prices) * 0.95):
            bottoms.append((i, prices[i]))
    
    if len(bottoms) < 2:
        return False
    
    bottom1_idx, bottom1_price = bottoms[-2]
    bottom2_idx, bottom2_price = bottoms[-1]
    
    if bottom2_idx - bottom1_idx > 30:
        return False
    
    if abs(bottom1_price - bottom2_price) / max(bottom1_price, bottom2_price) < threshold:
        peak = max(prices[bottom1_idx:bottom2_idx])
        if peak > bottom1_price * 1.03:
            return True
    
    return False

def detect_head_and_shoulders(prices):
    if len(prices) < 30:
        return False
    
    peaks = []
    for i in range(10, len(prices)-10):
        if (prices[i] > max(prices[max(0, i-10):i]) and 
            prices[i] > max(prices[i+1:min(len(prices), i+11)])):
            peaks.append((i, prices[i]))
    
    if len(peaks) < 3:
        return False
    
    left_idx, left_price = peaks[-3]
    head_idx, head_price = peaks[-2]
    right_idx, right_price = peaks[-1]
    
    if head_price <= left_price or head_price <= right_price:
        return False
    
    if abs(left_price - right_price) / max(left_price, right_price) > 0.05:
        return False
    
    left_valley = min(prices[left_idx:head_idx])
    right_valley = min(prices[head_idx:right_idx])
    neckline = min(left_valley, right_valley)
    
    if prices[-1] < neckline:
        return True
    
    return False

def detect_inverse_head_and_shoulders(prices):
    if len(prices) < 30:
        return False
    
    bottoms = []
    for i in range(10, len(prices)-10):
        if (prices[i] < min(prices[max(0, i-10):i]) and 
            prices[i] < min(prices[i+1:min(len(prices), i+11)])):
            bottoms.append((i, prices[i]))
    
    if len(bottoms) < 3:
        return False
    
    left_idx, left_price = bottoms[-3]
    head_idx, head_price = bottoms[-2]
    right_idx, right_price = bottoms[-1]
    
    if head_price >= left_price or head_price >= right_price:
        return False
    
    if abs(left_price - right_price) / max(left_price, right_price) > 0.05:
        return False
    
    left_peak = max(prices[left_idx:head_idx])
    right_peak = max(prices[head_idx:right_idx])
    neckline = max(left_peak, right_peak)
    
    if prices[-1] > neckline:
        return True
    
    return False

# === MAIN DASHBOARD ===
st.set_page_config(page_title="AI Trading Pro - Telegram", layout="wide")
st.title("🤖 AI Trading Pro — Multi-Coin + Telegram")

# Daftar coin
TOP_COINS = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]

# Test Telegram (sekali saat app load)
if 'telegram_tested' not in st.session_state:
    st.session_state.telegram_tested = True
    if test_telegram():
        st.success("✅ Telegram connection OK")
    else:
        st.error("❌ Telegram connection FAILED - Check token/ID")

for symbol in TOP_COINS:
    st.subheader(f"🪙 {symbol}")
    
    # Ambil data
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="90d", interval="1h")
    if hist.empty:
        st.warning(f"Tidak bisa ambil data {symbol}")
        continue
    
    prices = hist['Close'].tolist()
    highs = hist['High'].tolist()
    lows = hist['Low'].tolist()
    volumes = hist['Volume'].tolist()
    
    # Hitung indikator
    atr_vals = calculate_atr(hist, 14)
    adx_vals, _, _ = calculate_adx(hist, 14)
    rsi_vals = calculate_rsi(prices)
    macd_line, signal_line, _ = calculate_macd(prices)
    
    if len(rsi_vals) == 0 or len(macd_line) < 3 or len(atr_vals) == 0 or len(adx_vals) == 0:
        continue
    
    # Deteksi kondisi pasar
    market_condition = detect_market_condition(prices, highs, lows, prices, atr_vals, adx_vals)
    strategy = get_trading_strategy(market_condition)
    
    # Deteksi pola reversal
    has_double_top = detect_double_top(prices)
    has_double_bottom = detect_double_bottom(prices)
    has_hns = detect_head_and_shoulders(prices)
    has_inv_hns = detect_inverse_head_and_shoulders(prices)
    
    reversal_patterns = []
    if has_double_top: reversal_patterns.append("Double Top")
    if has_double_bottom: reversal_patterns.append("Double Bottom")
    if has_hns: reversal_patterns.append("Head & Shoulders")
    if has_inv_hns: reversal_patterns.append("Inv Head & Shoulders")
    
    # Sinyal beli
    current_rsi = rsi_vals[-1]
    current_price = prices[-1]
    is_rsi_oversold = current_rsi < 30
    is_macd_bullish = (macd_line[-1] > signal_line[-1]) and (macd_line[-2] <= signal_line[-2])
    is_volume_spike = volumes[-1] > np.mean(volumes[-20:]) * 1.2
    
    # Untuk sideways, tambah filter support/resistance (sederhana)
    if market_condition == "SIDEWAYS":
        current_atr = atr_vals[-1]
        sr_levels = [np.min(prices[-20:]), np.max(prices[-20:])]  # Support/Resistance sederhana
        is_near_support = any(abs(current_price - level) < current_atr * 0.5 for level in sr_levels)
        buy_signal = is_rsi_oversold and is_macd_bullish and is_volume_spike and is_near_support
    else:
        buy_signal = is_rsi_oversold and is_macd_bullish and is_volume_spike
    
    # Tampilkan info
    col1, col2, col3 = st.columns(3)
    col1.metric("Kondisi", market_condition)
    col2.metric("Strategi", strategy['strategy'])
    col3.metric("Harga", f"${current_price:.2f}")
    
    # Tampilkan pola reversal
    if reversal_patterns:
        st.warning(f"⚠️ Pola Reversal: {', '.join(reversal_patterns)}")
    
    # Kirim notifikasi Telegram jika ada sinyal
    if buy_signal:
        message = f"🚨 BELI {symbol} @ ${current_price:.2f}\n"
        message += f"RSI: {current_rsi:.2f} | MACD: Bullish | Volume: Spike"
        message += f"\nKondisi: {market_condition} | Strategi: {strategy['strategy']}"
        
        if reversal_patterns:
            message += f"\n⚠️ Pola: {', '.join(reversal_patterns)}"
        
        send_telegram_message(message)
        st.success(f"✅ Sinyal BELI terkirim ke Telegram!")
    
    # Grafik harga
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=prices, name='Harga', line=dict(width=2)))
    fig.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")
    
    st.divider()

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh", True):
    time.sleep(300)
    st.rerun()
