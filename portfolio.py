#!/usr/bin/env python3
"""Investment portfolio tracker.

Files used (all optional, kept in the same folder as this script):
  sp500.csv        S&P 500 constituents list (Symbol, Security, GICS Sector, ...).
                   Used to validate tickers and show company name / sector.
                   It has NO prices, so it is not a price source.
  sample_prices.csv  ticker,price  -> offline current prices.
Price lookup order: sample_prices.csv -> live via yfinance -> ask the user.
Output: appends each run to portfolio_summary.csv.
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

CONSTITUENTS_FILE = "sp500.csv"
PRICES_FILE = "sample_prices.csv"
SUMMARY_FILE = "portfolio_summary.csv"
SUMMARY_FIELDS = [
    "timestamp", "ticker", "company", "sector", "shares", "buy_price",
    "current_price", "invested", "market_value", "gain_loss", "gain_loss_pct",
]


# ---------- reference data ----------
def load_constituents(path=CONSTITUENTS_FILE):
    """Return {symbol: {"name":..., "sector":...}} from the S&P 500 CSV."""
    info = {}
    if not os.path.exists(path):
        return info
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = (row.get("Symbol") or "").strip().upper()
            if sym:
                info[sym] = {"name": row.get("Security", "").strip(),
                             "sector": row.get("GICS Sector", "").strip()}
    return info


def load_prices(path=PRICES_FILE):
    prices = {}
    if not os.path.exists(path):
        return prices
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                prices[row["ticker"].strip().upper()] = float(row["price"])
            except (KeyError, ValueError):
                continue
    return prices


def live_price(ticker):
    """Live price via yfinance (BRK.B -> BRK-B). None on any failure."""
    try:
        import yfinance as yf
        p = yf.Ticker(ticker.replace(".", "-")).fast_info["last_price"]
        return float(p) if p else None
    except Exception:
        return None


def get_price(ticker, csv_prices):
    if ticker in csv_prices:
        return csv_prices[ticker]
    price = live_price(ticker)
    if price is not None:
        return price
    return ask_float(f"  No price found for {ticker}. Enter current price: ")


# ---------- input ----------
def ask_float(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            print("  Value must be greater than 0.")
        except ValueError:
            print("  Please enter a valid number.")


def add_position(portfolio, ticker, shares, buy_price):
    """Repeat buys of one ticker merge at weighted-average cost."""
    if ticker in portfolio:
        old = portfolio[ticker]
        total = old["shares"] + shares
        avg = (old["shares"] * old["buy_price"] + shares * buy_price) / total
        portfolio[ticker] = {"shares": total, "buy_price": avg}
    else:
        portfolio[ticker] = {"shares": shares, "buy_price": buy_price}


def collect_positions(constituents):
    portfolio = {}
    print("Enter your holdings (leave ticker blank to finish).\n")
    while True:
        ticker = input("Ticker symbol: ").strip().upper()
        if not ticker:
            break
        if constituents:
            if ticker in constituents:
                c = constituents[ticker]
                print(f"  {c['name']} ({c['sector']})")
            else:
                ok = input(f"  {ticker} is not in the S&P 500 list. Add anyway? (y/n): ")
                if ok.strip().lower() != "y":
                    continue
        shares = ask_float("  Shares: ")
        buy_price = ask_float("  Buy price per share: ")
        add_position(portfolio, ticker, shares, buy_price)
    return portfolio


# ---------- calculations ----------
def analyze(portfolio, csv_prices, constituents):
    rows = []
    for ticker, pos in portfolio.items():
        current = get_price(ticker, csv_prices)
        invested = pos["shares"] * pos["buy_price"]
        value = pos["shares"] * current
        meta = constituents.get(ticker, {})
        rows.append({
            "ticker": ticker,
            "company": meta.get("name", ""),
            "sector": meta.get("sector", "Unknown"),
            "shares": pos["shares"],
            "buy_price": pos["buy_price"],
            "current_price": current,
            "invested": invested,
            "market_value": value,
            "gain_loss": value - invested,
            "gain_loss_pct": (value - invested) / invested * 100,
        })
    return rows


def print_report(rows):
    h = f"{'Ticker':<8}{'Shares':>9}{'Buy':>10}{'Now':>10}{'Invested':>12}{'Value':>12}{'Gain/Loss':>12}{'%':>9}"
    print("\n" + h + "\n" + "-" * len(h))
    for r in rows:
        print(f"{r['ticker']:<8}{r['shares']:>9.2f}{r['buy_price']:>10.2f}"
              f"{r['current_price']:>10.2f}{r['invested']:>12.2f}"
              f"{r['market_value']:>12.2f}{r['gain_loss']:>+12.2f}"
              f"{r['gain_loss_pct']:>+8.2f}%")
    invested = sum(r["invested"] for r in rows)
    value = sum(r["market_value"] for r in rows)
    gain = value - invested
    print("-" * len(h))
    print(f"Total invested:  {invested:,.2f}")
    print(f"Portfolio value: {value:,.2f}")
    print(f"Total gain/loss: {gain:+,.2f} ({gain / invested * 100:+.2f}%)")

    by_sector = defaultdict(float)
    for r in rows:
        by_sector[r["sector"]] += r["market_value"]
    if len(by_sector) > 1 or "Unknown" not in by_sector:
        print("\nAllocation by sector:")
        for sector, v in sorted(by_sector.items(), key=lambda x: -x[1]):
            print(f"  {sector:<25}{v:>12,.2f}  {v / value * 100:5.1f}%")


# ---------- logging ----------
def log_summary(rows, path=SUMMARY_FILE):
    is_new = not os.path.exists(path) or os.path.getsize(path) == 0
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        if is_new:
            w.writeheader()
        for r in rows:
            out = {"timestamp": stamp}
            out.update({k: round(v, 2) if isinstance(v, float) else v
                        for k, v in r.items()})
            w.writerow(out)
    print(f"\nSummary logged to {path}")


def main():
    constituents = load_constituents()
    csv_prices = load_prices()
    portfolio = collect_positions(constituents)
    if not portfolio:
        print("No positions entered.")
        return
    rows = analyze(portfolio, csv_prices, constituents)
    print_report(rows)
    log_summary(rows)


if __name__ == "__main__":
    main()
