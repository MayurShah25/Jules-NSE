import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import backtest

def run_multi_day_compounding():
    start_date_str = '2024-08-01'
    end_date_str = '2024-08-30'

    print(f"Fetching Nifty data from {start_date_str} to {end_date_str} in chunks...")

    # yfinance only allows 7 days of 1-minute data per request, so we must fetch it in chunks
    df_list = []

    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    # yfinance requires end_date + 1 to include the final day in the download
    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)

    current_dt = start_dt
    while current_dt < end_dt:
        chunk_end = min(current_dt + timedelta(days=7), end_dt)
        print(f"Downloading chunk: {current_dt.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}...")
        chunk = yf.download('^NSEI', start=current_dt.strftime('%Y-%m-%d'), end=chunk_end.strftime('%Y-%m-%d'), interval='1m', progress=False)
        if not chunk.empty:
            df_list.append(chunk)
        current_dt = chunk_end

    if not df_list:
        print("Failed to download data.")
        return

    nifty = pd.concat(df_list)
    # yfinance sometimes returns duplicates when chunking
    nifty = nifty[~nifty.index.duplicated(keep='first')]

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
        # Stop at the end_date
        if date > datetime.strptime(end_date_str, '%Y-%m-%d').date():
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
