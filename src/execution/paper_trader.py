import time
from typing import Dict, Any, List
from src.execution.risk_manager import risk_manager


class PaperExecutionBlotter:
    """Tracks active simulated delta-neutral positions and funding cashflows."""

    def __init__(self, starting_balance_usd: float = 100000.0):
        self.balance_usd = starting_balance_usd
        self.active_positions: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []
        self.cumulative_funding_collected_usd = 0.0

    def open_arbitrage_position(
        self,
        symbol: str,
        long_exchange: str,
        short_exchange: str,
        position_usd: float,
        funding_rate_8h_pct: float
    ) -> Dict[str, Any]:
        # Validate through risk manager
        is_safe, reason = risk_manager.validate_execution(position_usd, position_usd)
        if not is_safe:
            return {"success": False, "error": reason}

        pos_id = f"ARB-{symbol.replace('/', '')}-{int(time.time())}"
        pos = {
            "position_id": pos_id,
            "symbol": symbol,
            "long_exchange": long_exchange,
            "short_exchange": short_exchange,
            "position_usd": position_usd,
            "funding_rate_8h_pct": funding_rate_8h_pct,
            "opened_at": time.time(),
            "accumulated_funding_usd": 0.0,
            "status": "OPEN_DELTA_NEUTRAL"
        }
        self.active_positions.append(pos)
        return {"success": True, "position": pos}

    def simulate_funding_settlement(self) -> float:
        """Simulates 8h settlement cycle across all active positions."""
        settled_usd = 0.0
        for pos in self.active_positions:
            rate = pos["funding_rate_8h_pct"] / 100.0
            payout = pos["position_usd"] * rate
            pos["accumulated_funding_usd"] += payout
            settled_usd += payout

        self.cumulative_funding_collected_usd += settled_usd
        self.balance_usd += settled_usd
        return round(settled_usd, 2)


paper_blotter = PaperExecutionBlotter()
