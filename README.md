# NSE Options Scalping Bot

An automated Options Buying Bot for the Indian Stock Market (Nifty/BankNifty). It uses dynamic risk allocation based on intraday momentum (ADX & EMA) and hyper-scalping mechanics on the 1-minute timeframe to capture breakouts and mean-reversions.

## 1. Environment Setup

To run this bot locally, you need Python installed on your machine.

1. Open your terminal or command prompt.
2. Install the required data handling, technical analysis, and broker libraries:
   ```bash
   pip install pandas numpy ta kiteconnect yfinance
   ```
   *(Note: Do NOT install `pandas-ta` as it is incompatible with newer versions of Python. We use the pure Python `ta` library instead.)*

## 2. Daily Authentication (Zerodha)

Zerodha's API regulations require you to manually authenticate your account once per day to receive a daily access token.

1. Open `zerodha_login.py` in your text editor.
2. Replace `"YOUR_ZERODHA_API_KEY"` and `"YOUR_ZERODHA_API_SECRET"` with your actual app credentials from the Kite Connect portal.
3. Every morning (after 7:30 AM), run this script:
   ```bash
   python zerodha_login.py
   ```
4. The script will give you a login URL. Click it, log in to Zerodha using your normal password + TOTP PIN.
5. You will be redirected to a blank page. Look at the URL in your browser; it will contain `request_token=XXXXX`.
6. Copy the `XXXXX` part and paste it back into your terminal.
7. The script will automatically fetch your Daily Access Token and save it to `access_token.txt`.

## 3. Configuring the Bot

Open `options_scalping_bot.py` and replace `"YOUR_ZERODHA_API_KEY"` on Line 44. You do **not** need to touch the access token, as the bot will automatically read it from the `access_token.txt` file you generated in Step 2.

## 4. How to Run

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