import pytest
from backend.data.models import OptionType, OptionChain, OptionQuote, GreeksData
from backend.options.greeks import black_scholes_price, calculate_greeks, calculate_iv
from backend.options.chain_analytics import calculate_pcr, calculate_max_pain, find_key_oi_levels, calculate_iv_skew

def test_black_scholes_and_greeks():
    S = 22000.0
    K = 22000.0
    T = 2 / 365.0  # 2 days to expiry
    r = 0.07
    sigma = 0.15

    call_price = black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
    put_price = black_scholes_price(S, K, T, r, sigma, OptionType.PUT)

    assert call_price > 0
    assert put_price > 0

    greeks_call = calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
    assert 0.45 <= greeks_call.delta <= 0.55
    assert greeks_call.gamma > 0
    assert greeks_call.theta < 0

    solved_iv = calculate_iv(call_price, S, K, T, r, OptionType.CALL)
    assert abs(solved_iv - sigma) < 0.01

def test_chain_analytics():
    chain = OptionChain(
        spot_price=22000.0,
        expiry_date="2025-03-04",
        days_to_expiry=2.0,
        time_to_expiry_hours=48.0,
        calls={
            22000.0: OptionQuote(strike=22000.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=100.0, bid=99.0, ask=101.0, bid_qty=500, ask_qty=500, volume=10000, open_interest=50000, change_in_oi=1000, iv=0.15),
            22200.0: OptionQuote(strike=22200.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=30.0, bid=29.0, ask=31.0, bid_qty=500, ask_qty=500, volume=20000, open_interest=100000, change_in_oi=5000, iv=0.14)
        },
        puts={
            22000.0: OptionQuote(strike=22000.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=90.0, bid=89.0, ask=91.0, bid_qty=500, ask_qty=500, volume=12000, open_interest=80000, change_in_oi=2000, iv=0.16),
            21800.0: OptionQuote(strike=21800.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=25.0, bid=24.0, ask=26.0, bid_qty=500, ask_qty=500, volume=25000, open_interest=120000, change_in_oi=6000, iv=0.17)
        }
    )

    pcr = calculate_pcr(chain)
    assert pcr == round((80000 + 120000) / (50000 + 100000), 2)

    call_res, put_sup = find_key_oi_levels(chain)
    assert call_res == 22200.0
    assert put_sup == 21800.0

    max_pain = calculate_max_pain(chain)
    assert max_pain in [21800.0, 22000.0, 22200.0]

    skew = calculate_iv_skew(chain)
    assert isinstance(skew, float)
