#!/usr/bin/env python3
"""
==============================================================================
OpenCryptoArbitrage CLI — Cross-Exchange Arbitrage & Funding Rate Scanner
==============================================================================
"""

import asyncio
import argparse
import sys
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.connectors.exchange_client import exchange_connector
from src.strategies.funding_arbitrage import funding_scanner
from src.strategies.cross_exchange_spread import spread_scanner
from src.execution.paper_trader import paper_blotter
from config.settings import settings

console = Console()


async def run_scan():
    console.print(Panel.fit(
        "[bold cyan]⚡ OpenCryptoArbitrage — Cross-Exchange Scanner (Binance • Bybit • OKX)[/bold cyan]\n"
        "[dim]Perpetual Funding Rate Arbitrage • Spatial Spreads • Delta-Neutral Execution[/dim]",
        border_style="cyan"
    ))

    with console.status("[bold yellow]Querying live perpetual funding rates and order books...[/bold yellow]"):
        funding_data = await exchange_connector.get_funding_rates()
        order_books = await exchange_connector.get_order_books()

    # 1. Funding Rates Overview Table
    funding_table = Table(title="📊 Real-Time Perpetual Funding Rates (8h Settlement)", header_style="bold magenta")
    funding_table.add_column("Pair", style="bold cyan")
    funding_table.add_column("Binance Rate", justify="right")
    funding_table.add_column("Bybit Rate", justify="right")
    funding_table.add_column("OKX Rate", justify="right")
    funding_table.add_column("Next Cycle", justify="right", style="dim")

    for item in funding_data:
        sym = item["symbol"]
        r = item["rates"]
        next_min = int(item["next_settlement_seconds"] / 60)
        funding_table.add_row(
            sym,
            f"{r['binance']['funding_rate_pct']:+.4f}%",
            f"{r['bybit']['funding_rate_pct']:+.4f}%",
            f"{r['okx']['funding_rate_pct']:+.4f}%",
            f"{next_min} mins"
        )
    console.print(funding_table)

    # 2. Funding Arbitrage Opportunities
    opps = funding_scanner.scan_opportunities(funding_data, order_books)
    if opps:
        opp_table = Table(title=f"🔥 Top {min(8, len(opps))} Delta-Neutral Funding Opportunities (Min Net APY > {settings.min_net_apy}%)", header_style="bold green")
        opp_table.add_column("Pair", style="bold cyan")
        opp_table.add_column("Strategy Type", justify="left")
        opp_table.add_column("Long Leg", justify="left", style="green")
        opp_table.add_column("Short Leg", justify="left", style="red")
        opp_table.add_column("8h Rate", justify="right")
        opp_table.add_column("Gross APY", justify="right")
        opp_table.add_column("Net APY (Post-Fees)", justify="right", style="bold green")

        for o in opps[:8]:
            opp_table.add_row(
                o["symbol"],
                o["type"].replace("_", " "),
                o["long_leg"],
                o["short_leg"],
                f"{o['funding_rate_8h_pct']:+.4f}%",
                f"{o['gross_apy_pct']:.1f}%",
                f"[bold green]{o['net_apy_pct']:.1f}%[/bold green]"
            )
        console.print(opp_table)

    # 3. Spatial Cross-Exchange Spreads
    spreads = spread_scanner.scan_spreads(order_books)
    if spreads:
        spread_table = Table(title=f"💰 Top Immediate Cross-Exchange Spreads (Threshold > {settings.min_spread_pct}%)", header_style="bold yellow")
        spread_table.add_column("Pair", style="bold cyan")
        spread_table.add_column("Route", justify="left")
        spread_table.add_column("Buy Price", justify="right")
        spread_table.add_column("Sell Price", justify="right")
        spread_table.add_column("Net Spread", justify="right", style="bold green")
        spread_table.add_column("Est. Profit ($25k)", justify="right", style="bold green")

        for s in spreads[:6]:
            spread_table.add_row(
                s["symbol"],
                f"Buy {s['buy_exchange']} -> Sell {s['sell_exchange']}",
                f"${s['buy_price']:,.2f}",
                f"${s['sell_price']:,.2f}",
                f"[bold green]{s['net_spread_pct']:+.3f}%[/bold green]",
                f"[bold green]${s['est_profit_usd']:+,.2f}[/bold green]"
            )
        console.print(spread_table)
    else:
        console.print("[dim]No spatial spreads currently exceeding taker fee threshold.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="OpenCryptoArbitrage CLI")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring daemon mode")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in seconds")

    args = parser.parse_args()

    if args.watch:
        console.print(f"[bold yellow]Starting continuous scanner loop (Every {args.interval}s)... Press Ctrl+C to stop.[/bold yellow]")
        try:
            while True:
                asyncio.run(run_scan())
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("[bold red]Scanner daemon stopped.[/bold red]")
    else:
        asyncio.run(run_scan())


if __name__ == "__main__":
    main()

