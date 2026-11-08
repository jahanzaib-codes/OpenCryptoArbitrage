from typing import Dict, Any, List
from config.settings import settings


class FundingArbitrageScanner:
    """Calculates risk-adjusted delta-neutral funding yields across exchanges."""

    def __init__(self, min_net_apy: float = settings.min_net_apy):
        self.min_net_apy = min_net_apy

    def calculate_compounded_apy(self, rate_8h: float) -> float:
        """
        Compounded Annualized Percentage Yield (APY) assuming 3 daily 8-hour settlements.
        Formula: (1 + rate)^1095 - 1
        """
        if rate_8h <= 0:
            return round(rate_8h * 3.0 * 365.0 * 100.0, 2)
        compounded = ((1.0 + rate_8h) ** 1095 - 1.0) * 100.0
        return round(min(9999.0, compounded), 2)

    def scan_opportunities(
        self,
        funding_data: List[Dict[str, Any]],
        order_books: Dict[str, Dict[str, Dict[str, float]]]
    ) -> List[Dict[str, Any]]:
        opportunities = []

        for item in funding_data:
            symbol = item["symbol"]
            rates = item["rates"]
            books = order_books.get(symbol, {})

            # 1. Spot-Perp Cash & Carry on each exchange
            for ex_name, ex_data in rates.items():
                r8h = ex_data["funding_rate"]
                if r8h <= 0:
                    continue  # Negative funding favors short-spot / long-perp (higher borrow cost)

                gross_apy = self.calculate_compounded_apy(r8h)

                # Amortized fee impact (entry + exit taker fees amortized over 14-day hold)
                total_friction_bps = (settings.taker_fee_bps * 2.0 + settings.slippage_bps * 2.0)
                fee_drag_apy = (total_friction_bps / 10000.0) * (365.0 / 14.0) * 100.0
                net_apy = round(gross_apy - fee_drag_apy, 2)

                if net_apy >= self.min_net_apy:
                    ex_book = books.get(ex_name, {})
                    opportunities.append({
                        "type": "CASH_AND_CARRY_DELTA_NEUTRAL",
                        "symbol": symbol,
                        "exchange": ex_name.upper(),
                        "long_leg": f"BUY SPOT ({ex_name.upper()})",
                        "short_leg": f"SHORT PERP ({ex_name.upper()})",
                        "funding_rate_8h_pct": ex_data["funding_rate_pct"],
                        "gross_apy_pct": gross_apy,
                        "net_apy_pct": net_apy,
                        "basis_spread_pct": ex_book.get("basis_spread_pct", 0.0),
                        "next_settlement_sec": item.get("next_settlement_seconds", 0),
                        "recommendation": "EXECUTE_CASH_AND_CARRY"
                    })

            # 2. Cross-Exchange Funding Discrepancy (Long low rate / Short high rate)
            ex_list = list(rates.keys())
            for i in range(len(ex_list)):
                for j in range(i + 1, len(ex_list)):
                    ex_a = ex_list[i]
                    ex_b = ex_list[j]
                    rate_a = rates[ex_a]["funding_rate"]
                    rate_b = rates[ex_b]["funding_rate"]

                    diff = abs(rate_a - rate_b)
                    if diff >= 0.00015:  # At least 1.5 bps diff per 8h
                        high_ex = ex_a if rate_a > rate_b else ex_b
                        low_ex = ex_b if rate_a > rate_b else ex_a

                        spread_apy = self.calculate_compounded_apy(diff)
                        net_spread_apy = round(spread_apy - fee_drag_apy, 2)

                        if net_spread_apy >= self.min_net_apy:
                            opportunities.append({
                                "type": "CROSS_EXCHANGE_FUNDING_SPREAD",
                                "symbol": symbol,
                                "exchange": f"{low_ex.upper()} vs {high_ex.upper()}",
                                "long_leg": f"LONG PERP ({low_ex.upper()})",
                                "short_leg": f"SHORT PERP ({high_ex.upper()})",
                                "funding_rate_8h_pct": round(diff * 100.0, 4),
                                "gross_apy_pct": spread_apy,
                                "net_apy_pct": net_spread_apy,
                                "basis_spread_pct": 0.0,
                                "next_settlement_sec": item.get("next_settlement_seconds", 0),
                                "recommendation": "EXECUTE_FUNDING_SPREAD"
                            })

        # Sort by Net APY descending
        opportunities.sort(key=lambda x: x["net_apy_pct"], reverse=True)
        return opportunities


funding_scanner = FundingArbitrageScanner()
