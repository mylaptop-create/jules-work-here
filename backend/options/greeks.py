import math
from scipy.stats import norm
from backend.data.models import OptionType, GreeksData

RISK_FREE_RATE = 0.07  # 7% Indian risk free rate proxy

def black_scholes_price(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
    """
    S: Spot price
    K: Strike price
    T: Time to expiry in years
    r: Risk-free rate
    sigma: Volatility (annualized)
    """
    if T <= 0:
        if option_type == OptionType.CALL:
            return max(0.0, S - K)
        else:
            return max(0.0, K - S)

    if sigma <= 0.0001:
        sigma = 0.0001

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == OptionType.CALL:
        price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return max(0.0, price)

def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> GreeksData:
    if T <= 0.0001 or sigma <= 0.0001:
        # Expiry or zero vol edge case
        d = 1.0 if (option_type == OptionType.CALL and S > K) or (option_type == OptionType.PUT and S < K) else 0.0
        return GreeksData(delta=d, gamma=0.0, theta=0.0, vega=0.0, implied_volatility=sigma)

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    # Delta
    if option_type == OptionType.CALL:
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1.0

    # Gamma
    gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

    # Theta (per calendar day)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    if option_type == OptionType.CALL:
        term2 = r * K * math.exp(-r * T) * norm.cdf(d2)
        theta_annual = term1 - term2
    else:
        term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
        theta_annual = term1 + term2
    theta = theta_annual / 365.0

    # Vega (per 1% change in vol)
    vega = (S * math.sqrt(T) * norm.pdf(d1)) / 100.0

    return GreeksData(
        delta=round(delta, 4),
        gamma=round(gamma, 6),
        theta=round(theta, 4),
        vega=round(vega, 4),
        implied_volatility=round(sigma, 4)
    )

def calculate_iv(market_price: float, S: float, K: float, T: float, r: float, option_type: OptionType) -> float:
    """
    Implied Volatility solver using Newton-Raphson method with Brent fallback.
    """
    intrinsic = max(0.0, S - K) if option_type == OptionType.CALL else max(0.0, K - S)
    if market_price <= intrinsic or T <= 0.0001:
        return 0.0

    sigma = 0.20  # initial guess
    for _ in range(50):
        price = black_scholes_price(S, K, T, r, sigma, option_type)
        vega = (S * math.sqrt(T) * norm.pdf((math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))))
        diff = price - market_price
        if abs(diff) < 1e-4:
            return sigma
        if vega < 1e-6:
            break
        sigma -= diff / vega
        if sigma <= 0.001 or sigma > 5.0:
            break

    # Fallback bisection
    low, high = 0.001, 5.0
    for _ in range(30):
        mid = (low + high) / 2.0
        price = black_scholes_price(S, K, T, r, mid, option_type)
        if abs(price - market_price) < 1e-3:
            return mid
        if price > market_price:
            high = mid
        else:
            low = mid

    return round((low + high) / 2.0, 4)
