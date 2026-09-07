# NSE Options Scalping Bot

An automated Options Buying Bot for the Indian Stock Market (Nifty/BankNifty). It uses dynamic risk allocation based on intraday momentum (ADX & EMA) and hyper-scalping mechanics on the 1-minute timeframe to capture breakouts and mean-reversions.

## 1. Environment Setup

To run this bot locally, you need Python installed on your machine.

1. Open your terminal or command prompt.
2. Install the required data handling, technical analysis, and broker libraries:
   ```bash
   pip install pandas numpy ta dhanhq yfinance
   ```
   *(Note: Do NOT install `pandas-ta` as it is incompatible with newer versions of Python. We use the pure Python `ta` library instead.)*

## 2. Configuring the Bot (`options_scalping_bot.py`)

Open `options_scalping_bot.py` in your code editor and look at the `BrokerAPI` class near the top.

1.  **Insert API Keys:** You must generate API Keys from your broker's developer portal.
    *   *Dhan:* Login to Dhan Web -> Profile -> DhanHQ API -> Generate Access Token.
    *   *Zerodha:* Create an app on Kite Connect developers portal (Note: Zerodha charges a monthly fee for API access).
2.  **Uncomment the SDK Code:** In the `BrokerAPI.__init__` method, uncomment the lines specific to your broker to initialize the connection.
3.  **Implement Data Fetching:** You will need to replace the `pass` in `get_historical_data` and the hardcoded return in `get_ltp` with the actual API calls for your broker (e.g., `self.kite.quote(symbol)`).

## 3. How to Run

### Run the Backtester (Historical Data Simulation)
The backtester includes built-in mock data generation so you can run it immediately without API keys to see how the mathematical logic and Indian broker fee structures work.
```bash
python backtest.py
```

### Run the Live Bot (Paper Trading)
By default, `PAPER_TRADING = True` is set at the top of `options_scalping_bot.py`.
Once you have plugged in your broker's API keys so the bot can fetch the live ticker data, you can run the bot. It will analyze the live market but **will only print the orders to your console** instead of actually risking your capital.
```bash
python options_scalping_bot.py
```

### Run the Live Bot (Real Capital)
Once you are confident in the bot's paper trading performance:
1. Change `PAPER_TRADING = False` at the top of the script.
2. Ensure you have uncommented the actual `place_order` execution method for your broker inside the `BrokerAPI.place_order()` function.
3. Run the script during market hours (09:15 AM to 03:15 PM). The bot will automatically halt and square-off all positions at 3:15 PM.