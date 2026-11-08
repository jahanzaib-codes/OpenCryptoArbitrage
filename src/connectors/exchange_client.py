import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional
from config.settings import settings

logger = logging.getLogger("OpenCryptoArbitrage.Connector")

SUPPORTED_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT",
    "AVAX/USDT", "LINK/USDT", "SUI/USDT", "NEAR/USDT", "PEPE/USDT"
]

EXCHANGES = ["binance", "bybit", "okx"]


class MultiExchangeConnector:
    """Manages price and funding rate feeds across Binance, Bybit, and OKX."""

    def __init__(self, mode: str = settings.data_mode):
        self.mode = mode.lower()
        self._mock_base_prices = {
            "BTC/USDT": 88500.0,
            "ETH/USDT": 3150.0,
            "SOL/USDT": 195.0,
            "BNB/USDT": 640.0,
            "DOGE/USDT": 0.28,
            "AVAX/USDT": 36.50,
            "LINK/USDT": 14.80,
            "SUI/USDT": 3.20,
            "NEAR/USDT": 5.40,
            "PEPE/USDT": 0.0000185
        }

    async def get_funding_rates(self) -> List[Dict[str, Any]]:
        """Fetches current and predicted 8h funding rates across exchanges."""
        results = []
        now = time.time()
        # Next settlement in 8-hour UTC cycles (00:00, 08:00, 16:00 UTC)
        next_funding_sec = 28800 - (int(now) % 28800)

        for sym in SUPPORTED_SYMBOLS:
            base_p = self._mock_base_prices[sym]

            # In high-volatility regimes, funding rates vary between exchanges
            binance_rate = round(random.uniform(0.00008, 0.00065), 6)  # 0.008% to 0.065% per 8h
            bybit_rate = round(binance_rate + random.uniform(-0.00015, 0.00025), 6)
            okx_rate = round(binance_rate + random.uniform(-0.00012, 0.00020), 6)

            results.append({
                "symbol": sym,
                "next_settlement_seconds": next_funding_sec,
                "rates": {
                    "binance": {
                        "funding_rate": binance_rate,
                        "funding_rate_pct": round(binance_rate * 100.0, 4),
                        "predicted_rate_pct": round((binance_rate + random.uniform(-0.00005, 0.00005)) * 100.0, 4)
                    },
                    "bybit": {
                        "funding_rate": bybit_rate,
                        "funding_rate_pct": round(bybit_rate * 100.0, 4),
                        "predicted_rate_pct": round((bybit_rate + random.uniform(-0.00005, 0.00005)) * 100.0, 4)
                    },
                    "okx": {
                        "funding_rate": okx_rate,
                        "funding_rate_pct": round(okx_rate * 100.0, 4),
                        "predicted_rate_pct": round((okx_rate + random.uniform(-0.00005, 0.00005)) * 100.0, 4)
                    }
                },
                "timestamp": now
            })

        return results

    async def get_order_books(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Fetches best bid and best ask for both Spot and Perpetual contracts
        across all target exchanges.
        """
        data = {}
        for sym in SUPPORTED_SYMBOLS:
            base = self._mock_base_prices[sym]
            data[sym] = {}
            for ex in EXCHANGES:
                # Add micro price noise per exchange
                noise = random.uniform(-0.0018, 0.0018)
                spot_mid = base * (1.0 + noise)
                perp_mid = spot_mid * (1.0 + random.uniform(-0.0010, 0.0015))

                spread = max(0.0001, spot_mid * 0.0002)

                data[sym][ex] = {
                    "spot_bid": round(spot_mid - spread / 2.0, 6 if base < 1 else 2),
                    "spot_ask": round(spot_mid + spread / 2.0, 6 if base < 1 else 2),
                    "perp_bid": round(perp_mid - spread / 2.0, 6 if base < 1 else 2),
                    "perp_ask": round(perp_mid + spread / 2.0, 6 if base < 1 else 2),
                    "basis_spread_pct": round(((perp_mid - spot_mid) / spot_mid) * 100.0, 3)
                }
        return data


exchange_connector = MultiExchangeConnector()
