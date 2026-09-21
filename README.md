# NSE & MCX Scalping Bot Suite

An automated algorithmic trading suite for the Indian Stock Market (Nifty/BankNifty Options) and Commodities Market (Crude Oil/Natural Gas Mini Futures). It uses dynamic risk allocation based on intraday momentum (ADX & EMA) and hyper-scalping mechanics on the 1-minute timeframe to capture breakouts and mean-reversions.

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

Open the specific bot script (e.g., `options_scalping_bot.py` or `crude_scalping_bot.py`) and replace `"YOUR_ZERODHA_API_KEY"`. You do **not** need to touch the access token, as the bots will automatically read it from the `access_token.txt` file you generated in Step 2.

## 4. How to Run

### Run the Backtesters (Historical Data Simulation)
You can run the backtesters to verify strategy logic on historical data. For Crude Oil and Natural Gas, the backtesters automatically download recent data using yfinance.
```bash
python backtest.py                # For Nifty Options
python banknifty_backtest.py      # For BankNifty Options
python crude_backtest.py          # For Crude Oil Futures
python natgas_backtest.py         # For Natural Gas Futures
```

### Run the Live Bots (Paper Trading)
By default, `PAPER_TRADING = True` is set at the top of each script.
Once you have plugged in your broker's API keys so the bots can fetch the live ticker data, you can launch the bots via the provided starter scripts.

**For Windows:**
Double-click `start_bot.bat` or run:
```bash
start_bot.bat
```
*(This provides an interactive menu to choose which bot to run.)*

**For Mac/Linux:**
```bash
./start_bot.sh
```
*(This automatically deploys all bots in the background securely using the script.)*

*Note: The bot includes an auto-reconnect function. If the Zerodha socket drops during market hours, it will automatically attempt to reconnect without crashing.*

### Run the Live Bot (Real Capital)
Once you are confident in the bot's paper trading performance:
1. Change `PAPER_TRADING = False` at the top of the desired bot script.
2. Run the start script during market hours. The bot will execute live orders, manage dynamic stop losses, and strictly halt and auto-square-off all open positions at exactly **3:15 PM** for NSE and **11:15 PM** for MCX.