import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import backtest

def run_multi_day_compounding():
    start_date_str = '2026-09-01'
    end_date_str = '2026-09-07'

    print(f"Fetching Nifty data from {start_date_str} to {end_date_str}...")
    # Fetch all data at once
    nifty = yf.download('^NSEI', start=start_date_str, end='2026-09-08', interval='1m', progress=False)

    if nifty.empty:
        print("Failed to download data.")
        return

    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.droplevel(1)

    nifty = nifty.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

    if 'volume' not in nifty.columns or nifty['volume'].sum() == 0:
        import numpy as np
        np.random.seed(42)
        nifty['volume'] = np.random.randint(10000, 150000, size=len(nifty))

    current_capital = 50000.0
    print(f"\n🚀 STARTING MULTI-DAY COMPOUNDING BACKTEST 🚀")
    print(f"Initial Starting Capital: ₹{current_capital:.2f}\n")

    # Iterate through each unique day in the dataset
    unique_dates = pd.Series(nifty.index.date).unique()

    for date in unique_dates:
        # Stop at the 7th
        if date > datetime.strptime('2026-09-07', '%Y-%m-%d').date():
            break

        print(f"\n{'='*50}")
        print(f"📅 Trading Day: {date.strftime('%Y-%m-%d')}")
        print(f"💰 Starting Capital Today: ₹{current_capital:.2f}")
        print(f"{'='*50}")

        # Extract just this day's data
        daily_data = nifty[nifty.index.date == date]

        if len(daily_data) < 50:
            print("Not enough candles for this day, skipping.")
            continue

        # Run the backtester with the rolling capital
        tester = backtest.Backtester(daily_data, starting_capital=current_capital)
        tester.run()

        # Update the rolling capital for the next day
        current_capital = tester.capital

    print(f"\n{'*'*50}")
    print(f"🏁 FINAL COMPOUNDING RESULTS 🏁")
    print(f"Total Return: {((current_capital - 50000.0) / 50000.0) * 100:.2f}%")
    print(f"Final Capital: ₹{current_capital:.2f}")
    print(f"{'*'*50}\n")

if __name__ == "__main__":
    run_multi_day_compounding()
