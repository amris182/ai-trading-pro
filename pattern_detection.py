# pattern_detection.py
import numpy as np

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