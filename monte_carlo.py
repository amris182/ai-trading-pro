# monte_carlo.py
import numpy as np
import yfinance as yf

def run_monte_carlo(symbol, num_simulations=1000, days=7):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="180d", interval="1d")
    if hist.empty:
        return None
    
    returns = hist['Close'].pct_change().dropna()
    mean_return = returns.mean()
    std_return = returns.std()
    
    initial_price = hist['Close'].iloc[-1]
    simulated_prices = np.zeros((num_simulations, days))
    simulated_prices[:, 0] = initial_price
    
    for i in range(1, days):
        random_returns = np.random.normal(mean_return, std_return, num_simulations)
        simulated_prices[:, i] = simulated_prices[:, i-1] * (1 + random_returns)
    
    final_prices = simulated_prices[:, -1]
    profits = (final_prices - initial_price) / initial_price * 100
    
    mean_profit = np.mean(profits)
    std_profit = np.std(profits)
    prob_profitable = np.mean(profits > 0) * 100
    var_95 = np.percentile(profits, 5)
    
    return {
        'symbol': symbol,
        'mean_profit_pct': mean_profit,
        'std_profit_pct': std_return * 100,
        'prob_profitable_pct': prob_profitable,
        'var_95_pct': var_95
    }