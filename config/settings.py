import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class ArbitrageSettings(BaseModel):
    """Configuration settings for OpenCryptoArbitrage."""

    data_mode: str = Field(default_factory=lambda: os.getenv("DATA_MODE", "simulator"))

    # API Keys
    binance_key: str = Field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    binance_secret: str = Field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    bybit_key: str = Field(default_factory=lambda: os.getenv("BYBIT_API_KEY", ""))
    bybit_secret: str = Field(default_factory=lambda: os.getenv("BYBIT_API_SECRET", ""))
    okx_key: str = Field(default_factory=lambda: os.getenv("OKX_API_KEY", ""))
    okx_secret: str = Field(default_factory=lambda: os.getenv("OKX_API_SECRET", ""))
    okx_passphrase: str = Field(default_factory=lambda: os.getenv("OKX_PASSPHRASE", ""))

    # Strategy Thresholds
    min_net_apy: float = Field(default_factory=lambda: float(os.getenv("MIN_NET_APY_THRESHOLD", "15.0")))
    min_spread_pct: float = Field(default_factory=lambda: float(os.getenv("MIN_SPREAD_PCT", "0.25")))
    max_position_usd: float = Field(default_factory=lambda: float(os.getenv("MAX_POSITION_USD", "25000.0")))
    default_leverage: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_LEVERAGE", "1.0")))

    # Frictions
    taker_fee_bps: float = Field(default_factory=lambda: float(os.getenv("TAKER_FEE_BPS", "5.0")))
    maker_fee_bps: float = Field(default_factory=lambda: float(os.getenv("MAKER_FEE_BPS", "2.0")))
    slippage_bps: float = Field(default_factory=lambda: float(os.getenv("ESTIMATED_SLIPPAGE_BPS", "2.0")))

    scan_interval: int = Field(default_factory=lambda: int(os.getenv("SCAN_INTERVAL_SECONDS", "10")))
    auto_paper_execute: bool = Field(default_factory=lambda: os.getenv("AUTO_PAPER_EXECUTE", "false").lower() in ("true", "1", "yes"))


settings = ArbitrageSettings()

