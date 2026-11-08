from typing import Tuple, Optional
from config.settings import settings


class ArbitrageRiskManager:
    """Enforces institutional delta-neutrality and margin safety guardrails."""

    def __init__(
        self,
        max_position_usd: float = settings.max_position_usd,
        delta_tolerance_pct: float = 1.0
    ):
        self.max_position_usd = max_position_usd
        self.delta_tolerance_pct = delta_tolerance_pct

    def validate_execution(
        self,
        long_value_usd: float,
        short_value_usd: float,
        current_margin_ratio_pct: float = 450.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates risk limits before initiating an arbitrage position.
        """
        # 1. Position size ceiling
        if long_value_usd > self.max_position_usd or short_value_usd > self.max_position_usd:
            return False, f"Position size (${max(long_value_usd, short_value_usd):,.2f}) exceeds maximum threshold (${self.max_position_usd:,.2f})"

        # 2. Delta neutrality check (Long and Short must offset within tolerance)
        drift_pct = abs(long_value_usd - short_value_usd) / (long_value_usd + 1e-9) * 100.0
        if drift_pct > self.delta_tolerance_pct:
            return False, f"Delta imbalance detected: {drift_pct:.2f}% exceeds {self.delta_tolerance_pct}% neutrality tolerance"

        # 3. Margin liquidation buffer
        if current_margin_ratio_pct < 250.0:
            return False, f"Dangerous margin ratio ({current_margin_ratio_pct:.1f}%): minimum 250% liquidation buffer required"

        return True, None


risk_manager = ArbitrageRiskManager()
