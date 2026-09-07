import yfinance as yf
import pandas as pd
from datetime import datetime
import backtest

# Fetch Nifty 50 data for Sept 3rd, 2026
print("Fetching Nifty data for Sept 3rd, 2026...")
nifty = yf.download('^NSEI', start='2026-09-03', end='2026-09-04', interval='1m', progress=False)

if nifty.empty:
    print("Market might be closed or data unavailable for this date.")
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
        np.random.seed(42)
        nifty['volume'] = np.random.randint(10000, 150000, size=len(nifty))

    print(f"Loaded {len(nifty)} candles. Starting backtest on historical data...")

    # Initialize and run our exact backtester logic
    tester = backtest.Backtester(nifty)
    tester.run()
