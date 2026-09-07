import yfinance as yf
import pandas as pd
from datetime import datetime
import backtest

# Fetch today's Nifty 50 data (1-minute intervals)
print("Fetching today's live Nifty data...")
nifty = yf.download('^NSEI', period='1d', interval='1m', progress=False)

if nifty.empty:
    print("Market might be closed or data unavailable yet.")
else:
    # yfinance returns MultiIndex columns in recent versions, flatten it
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.droplevel(1)

    # Rename columns to match what our backtester expects
    nifty = nifty.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

    # We might not have volume for Nifty Index directly, so mock it if missing or 0
    if 'volume' not in nifty.columns or nifty['volume'].sum() == 0:
        import numpy as np
        nifty['volume'] = np.random.randint(10000, 150000, size=len(nifty))

    print(f"Loaded {len(nifty)} candles. Starting backtest on real today's data...")

    # Initialize and run our exact backtester logic on the live data
    tester = backtest.Backtester(nifty)
    tester.run()
