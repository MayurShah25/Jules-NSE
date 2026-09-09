import yfinance as yf
import pandas as pd
from datetime import datetime
import backtest

# Fetch 5 days of Nifty 50 data to "warm up" the indicators
# (e.g. 21-EMA and 30-min rolling breakouts need prior data if run right at market open)
print("Fetching live Nifty data to warm up indicators...")
nifty = yf.download('^NSEI', period='5d', interval='1m', progress=False)

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
        np.random.seed(42)
        nifty['volume'] = np.random.randint(10000, 150000, size=len(nifty))

    # We only want to execute trades for TODAY, but we pass the full 5-day dataset
    # to the Backtester so the indicators (like 30-min rolling highs) calculate correctly.
    # To do this, we intercept the 'current_date' logic in Backtester by slicing the execution.

    today_date = nifty.index[-1].date()
    today_candles = len(nifty[nifty.index.date == today_date])

    print(f"Loaded {len(nifty)} total candles. Today has {today_candles} candles.")
    if today_candles < 2:
        print("Market just opened. Waiting for more data...")
    else:
        print("Starting backtest on today's live data...")
        # Initialize and run our exact backtester logic on the live data
        tester = backtest.Backtester(nifty)

        # We temporarily inject a filter into the tester so it only takes trades TODAY
        # We override the _execute_trade method dynamically for this specific script:
        original_execute = tester._execute_trade
        def proxy_execute_trade(row, opt_type):
            if row.name.date() == today_date:
                original_execute(row, opt_type)
        tester._execute_trade = proxy_execute_trade

        tester.run()
