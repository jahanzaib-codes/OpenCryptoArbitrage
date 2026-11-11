from typing import Dict, Any, List
from config.settings import settings


class TriangularArbitrageScanner:
    """Evaluates intra-exchange 3-legged synthetic arbitrage loops."""

    def __init__(self, fee_bps_per_leg: float = settings.taker_fee_bps):
        self.fee_per_leg = fee_bps_per_leg / 10000.0  # e.g. 0.0005 (0.05%)

    def check_triangular_loop(
        self,
        usdt_btc_ask: float,
        btc_eth_ask: float,
        eth_usdt_bid: float,
        start_capital_usdt: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Simulates:
        1. USDT -> Buy BTC (at USDT/BTC ask)
        2. BTC -> Buy ETH (at BTC/ETH ask)
        3. ETH -> Sell to USDT (at ETH/USDT bid)
        """
        # Leg 1: USDT -> BTC
        btc_acquired = (start_capital_usdt / usdt_btc_ask) * (1.0 - self.fee_per_leg)

        # Leg 2: BTC -> ETH
        eth_acquired = (btc_acquired / btc_eth_ask) * (1.0 - self.fee_per_leg)

        # Leg 3: ETH -> USDT
        final_usdt = (eth_acquired * eth_usdt_bid) * (1.0 - self.fee_per_leg)

        profit_usd = final_usdt - start_capital_usdt
        profit_pct = (profit_usd / start_capital_usdt) * 100.0

        return {
            "path": "USDT -> BTC -> ETH -> USDT",
            "initial_capital_usdt": start_capital_usdt,
            "final_capital_usdt": round(final_usdt, 2),
            "net_profit_usd": round(profit_usd, 2),
            "net_profit_pct": round(profit_pct, 4),
            "is_profitable": profit_usd > 0
        }


triangular_scanner = TriangularArbitrageScanner()

