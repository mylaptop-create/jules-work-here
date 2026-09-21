import pandas as pd
import numpy as np

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    df requires 'high', 'low', 'close', 'volume'
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0
    tp_vol = typical_price * df['volume']
    cum_tp_vol = tp_vol.cumsum()
    cum_vol = df['volume'].cumsum()
    return cum_tp_vol / np.maximum(cum_vol, 1)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    df requires 'high', 'low', 'close'
    """
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()

    rs = gain / np.maximum(loss, 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = calculate_atr(df, period)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period, min_periods=1).mean() / np.maximum(atr, 1e-6))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period, min_periods=1).mean() / np.maximum(atr, 1e-6))

    dx = 100 * (plus_di - minus_di).abs() / np.maximum(plus_di + minus_di, 1e-6)
    adx = dx.rolling(period, min_periods=1).mean()
    return adx

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()
