# Portfolio Tracker

A simple Python command-line utility for tracking a stock portfolio. Enter your tickers, buy prices and share quantities, and it calculates total invested capital, current market value, and the percentage gain or loss for each holding. Every run is logged to a CSV file.

## Features

- Enter holdings interactively (ticker, shares, buy price)
- Repeat buys of the same ticker are merged at weighted-average cost
- Validates tickers against an S&P 500 constituents list and shows company name and sector
- Current prices from a local CSV, live via `yfinance`, or manual entry
- Per-holding and total gain/loss in money and percent
- Allocation breakdown by sector
- Appends a timestamped summary to `portfolio_summary.csv`

## Requirements

- Python 3.8+
- Optional, for live prices: `pip install yfinance`

The core features use only the standard library (`csv`, `os`, `datetime`).

## Files

| File | Purpose |
|------|---------|
| `portfolio.py` | Main program |
| `sp500.csv` | S&P 500 constituents (Symbol, Security, GICS Sector, ...) used to validate tickers |
| `sample_prices.csv` | Sample current prices (`ticker,price`) for offline use |
| `portfolio_summary.csv` | Output log, created on first run |

## Usage

```bash
python3 portfolio.py
```

Example session:

```
Ticker symbol: AAPL
  Apple Inc. (Information Technology)
  Shares: 10
  Buy price per share: 200
Ticker symbol: MSFT
  Microsoft (Information Technology)
  Shares: 5
  Buy price per share: 450
Ticker symbol:            <- press Enter to finish

Ticker     Shares       Buy       Now    Invested       Value   Gain/Loss        %
AAPL        10.00    200.00    228.50     2000.00     2285.00     +285.00  +14.25%
MSFT         5.00    450.00    425.10     2250.00     2125.50     -124.50   -5.53%
Total invested:  4,250.00
Portfolio value: 4,410.50
Total gain/loss: +160.50 (+3.78%)
```

## Price lookup order

1. `sample_prices.csv`
2. Live price via `yfinance`
3. Manual entry if neither is available

The sample prices are placeholders. Edit them or use `yfinance` for real data.

## Output format

`portfolio_summary.csv` columns: `timestamp, ticker, company, sector, shares, buy_price, current_price, invested, market_value, gain_loss, gain_loss_pct`

## Disclaimer

For educational purposes only. Not financial advice.
