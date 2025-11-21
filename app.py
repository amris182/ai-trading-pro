# app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import time

# Import fungsi dari file lain
from utils import calculate_rsi, calculate_macd, calculate_atr, calculate_adx
from market_detector import detect_market_condition, get_trading_strategy
from pattern_detection import (
    detect_double_top, detect_double_bottom,
    detect_head_and_shoulders, detect_inverse_head_and_shoulders
)
from monte_carlo import run_monte_carlo

st.set_page_config(page_title="AI Trading Pro", layout="wide")
st.title("🤖 AI Trading Pro — Multi-Coin")

# Daftar coin
TOP_COINS = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]

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
    
    # Deteksi kondisi pasar
    market_condition = detect_market_condition(prices, highs, lows, prices, atr_vals, adx_vals)
    strategy = get_trading_strategy(market_condition)
    
    # Deteksi pola reversal
    has_double_top = detect_double_top(prices)
    has_double_bottom = detect_double_bottom(prices)
    has_hns = detect_head_and_shoulders(prices)
    has_inv_hns = detect_inverse_head_and_shoulders(prices)
    
    # Monte Carlo
    mc_result = run_monte_carlo(symbol)
    
    # Tampilkan info
    col1, col2, col3 = st.columns(3)
    col1.metric("Kondisi", market_condition)
    col2.metric("Strategi", strategy['strategy'])
    col3.metric("Harga", f"${prices[-1]:.2f}")
    
    # Tampilkan pola reversal
    reversal_patterns = []
    if has_double_top: reversal_patterns.append("Double Top")
    if has_double_bottom: reversal_patterns.append("Double Bottom")
    if has_hns: reversal_patterns.append("Head & Shoulders")
    if has_inv_hns: reversal_patterns.append("Inv Head & Shoulders")
    
    if reversal_patterns:
        st.warning(f"⚠️ Pola Reversal: {', '.join(reversal_patterns)}")
    
    # Tampilkan Monte Carlo
    if mc_result:
        col1, col2, col3 = st.columns(3)
        col1.metric("Profit Rata-rata (7 hari)", f"{mc_result['mean_profit_pct']:.2f}%")
        col2.metric("Probabilitas Profit", f"{mc_result['prob_profitable_pct']:.1f}%")
        col3.metric("Risk 95%", f"{mc_result['var_95_pct']:.2f}%")
    
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