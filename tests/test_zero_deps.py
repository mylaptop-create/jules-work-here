import unittest
from run_nifty_bot import (
    norm_cdf, norm_pdf, black_scholes, calculate_greeks, solve_iv,
    create_demo_snapshot, generate_decision, format_signal
)

class TestZeroDependenciesBot(unittest.TestCase):
    def test_normal_distribution_and_bs(self):
        self.assertAlmostEqual(norm_cdf(0.0), 0.5, places=4)
        price_ce = black_scholes(22000.0, 22000.0, 2/365.0, 0.07, 0.15, "CE")
        self.assertGreater(price_ce, 0.0)

    def test_greeks_and_iv(self):
        g = calculate_greeks(22000.0, 22000.0, 2/365.0, 0.07, 0.15, "CE")
        self.assertTrue(0.45 <= g["delta"] <= 0.55)
        self.assertGreater(g["gamma"], 0.0)

        iv = solve_iv(100.0, 22000.0, 22000.0, 2/365.0, 0.07, "CE")
        self.assertGreater(iv, 0.0)

    def test_decision_and_formatter(self):
        snap = create_demo_snapshot()
        decision = generate_decision(snap, capital=50000.0, max_risk_pct=1.5)
        self.assertIn(decision["action"], ["BUY", "NO TRADE"])

        formatted = format_signal(decision)
        self.assertIn("NIFTY EXPIRY TRADE SIGNAL", formatted)

if __name__ == "__main__":
    unittest.main()
