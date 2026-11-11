from typing import Dict, Any, List
from config.settings import settings


class CrossExchangeSpreadScanner:
    """Detects immediate spatial price differences across Binance, Bybit, and OKX."""

    def __init__(self, min_spread_pct: float = settings.min_spread_pct):
        self.min_spread_pct = min_spread_pct

    def scan_spreads(self, order_books: Dict[str, Dict[str, Dict[str, float]]]) -> List[Dict[str, Any]]:
        spread_opportunities = []
        fee_pct = (settings.taker_fee_bps * 2.0 + settings.slippage_bps * 2.0) / 100.0  # e.g. 0.14%

        for sym, exchanges in order_books.items():
            ex_names = list(exchanges.keys())
            for i in range(len(ex_names)):
                for j in range(len(ex_names)):
                    if i == j:
                        continue
                    buy_ex = ex_names[i]
                    sell_ex = ex_names[j]

                    buy_ask = exchanges[buy_ex]["spot_ask"]
                    sell_bid = exchanges[sell_ex]["spot_bid"]

                    if buy_ask <= 0:
                        continue

                    raw_spread_pct = ((sell_bid - buy_ask) / buy_ask) * 100.0
                    net_spread_pct = raw_spread_pct - fee_pct

                    if net_spread_pct >= self.min_spread_pct:
                        est_profit_usd = (settings.max_position_usd * (net_spread_pct / 100.0))
                        spread_opportunities.append({
                            "symbol": sym,
                            "buy_exchange": buy_ex.upper(),
                            "sell_exchange": sell_ex.upper(),
                            "buy_price": buy_ask,
                            "sell_price": sell_bid,
                            "raw_spread_pct": round(raw_spread_pct, 3),
                            "net_spread_pct": round(net_spread_pct, 3),
                            "est_profit_usd": round(est_profit_usd, 2),
                            "allocation_usd": settings.max_position_usd
                        })

        spread_opportunities.sort(key=lambda x: x["net_spread_pct"], reverse=True)
        return spread_opportunities


spread_scanner = CrossExchangeSpreadScanner()

