import pytest
import pandas as pd
import numpy as np
from backend.indicators.technical import calculate_vwap, calculate_atr, calculate_rsi, calculate_adx, calculate_ema
from backend.volatility.expected_move import calculate_iv_expected_move, calculate_atr_expected_move, calculate_expected_move_bounds

def test_indicators():
    np.random.seed(42)
    prices = 22000 + np.random.randn(50).cumsum() * 10
    df = pd.DataFrame({
        'high': prices + np.random.rand(50) * 10,
        'low': prices - np.random.rand(50) * 10,
        'close': prices,
        'volume': np.random.randint(100, 1000, size=50)
    })

    vwap = calculate_vwap(df)
    assert len(vwap) == 50
    assert vwap.iloc[-1] > 0

    atr = calculate_atr(df, 14)
    assert len(atr) == 50
    assert atr.iloc[-1] > 0

    rsi = calculate_rsi(df['close'], 14)
    assert 0 <= rsi.iloc[-1] <= 100

    adx = calculate_adx(df, 14)
    assert adx.iloc[-1] >= 0

    ema20 = calculate_ema(df['close'], 20)
    assert len(ema20) == 50

def test_expected_move():
    spot = 22000.0
    iv = 0.15
    atr = 120.0
    dte = 2.0

    iv_move = calculate_iv_expected_move(spot, iv, dte)
    assert iv_move > 0

    atr_move = calculate_atr_expected_move(atr, dte)
    assert atr_move > 0

    bounds = calculate_expected_move_bounds(spot, iv, atr, dte)
    assert bounds["upper_boundary"] > spot
    assert bounds["lower_boundary"] < spot
    assert bounds["prob_touch_boundary"] > 0
