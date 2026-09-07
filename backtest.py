import logging
import pandas as pd
import numpy as np
import ta
from datetime import datetime, time

# ==========================================
# CONFIGURATION & PARAMETERS
# ==========================================
SYMBOL = "NIFTY"
TIMEFRAME = "1min"
QTY = 500  # 10 Nifty Lots to overcome flat brokerage fees

MAX_LOSS_PER_DAY = -50000  # Scaled up kill switch for larger quantity
# Dynamic Risk variables will be calculated per trade based on ADX

EMA_PERIOD = 21
ADX_PERIOD = 14
ADX_THRESHOLD = 20
RSI_PERIOD = 14

# Simplified backtest assumptions
INITIAL_CAPITAL = 50000
SLIPPAGE = 1.0 # fixed slippage in points
MAX_CAPITAL_DEPLOYMENT = 0.95 # Use 95% of available capital per trade

# Realistic NSE Options Fees (Approximate)
BROKERAGE_PER_ORDER = 20.0
STT_PCT = 0.00125 # 0.125% on sell side premium
EXCHANGE_TXN_CHARGE_PCT = 0.0005 # NSE txn charge on premium
GST_PCT = 0.18 # 18% on (brokerage + txn charge)
SEBI_CHARGE_PCT = 0.000001 # Rs 10 per crore
STAMP_DUTY_PCT = 0.00003 # 0.003% on buy side premium

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, data: pd.DataFrame, starting_capital=INITIAL_CAPITAL):
        self.data = data
        self.capital = starting_capital
        self.starting_capital = starting_capital
        self.trades = []

        # Current state
        self.in_position = False
        self.position_type = None
        self.option_symbol = ""
        self.current_qty = 0
        self.entry_price = 0.0
        self.underlying_entry_price = 0.0
        self.entry_time = None
        self.current_sl = 0.0
        self.max_opt_price_seen = 0.0
        self.target_reached = False
        self.breakeven_reached = False

        # Dynamic trade-specific risk parameters
        self.trade_sl_pct = 0.0
        self.trade_target_pct = 0.0
        self.trade_trailing_pct = 0.0

        self.daily_pnl = 0.0
        self.kill_switch_active = False
        self.current_date = None

    def calculate_indicators(self):
        """Calculates necessary indicators on the entire dataset upfront (Vectorized approach for speed)."""
        logger.info("Calculating indicators...")
        df = self.data.copy()

        # EMA
        df[f'EMA_{EMA_PERIOD}'] = ta.trend.EMAIndicator(close=df['close'], window=EMA_PERIOD).ema_indicator()

        # ADX
        adx_indicator = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=ADX_PERIOD)
        df[f'ADX_{ADX_PERIOD}'] = adx_indicator.adx()
        df['ADX_Slope'] = df[f'ADX_{ADX_PERIOD}'].diff() # Positive slope means trend is accelerating

        # RSI
        df[f'RSI_{RSI_PERIOD}'] = ta.momentum.RSIIndicator(close=df['close'], window=RSI_PERIOD).rsi()

        # Simplified VWAP for backtesting (using typical price)
        df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
        df['Vol_x_Typ'] = df['volume'] * df['Typical_Price']

        # Calculate daily cumulative volume and Vol_x_Typ
        df['Date'] = df.index.date
        df['Cum_Vol'] = df.groupby('Date')['volume'].cumsum()
        df['Cum_Vol_x_Typ'] = df.groupby('Date')['Vol_x_Typ'].cumsum()
        df['VWAP'] = df['Cum_Vol_x_Typ'] / df['Cum_Vol']

        # Calculate Rolling 15-Minute High/Low (15 candles on 1min chart) to avoid fakeouts
        # Shift by 1 to exclude the current candle
        ROLLING_PERIOD = 15
        df['Rolling_High'] = df['high'].shift(1).rolling(window=ROLLING_PERIOD).max()
        df['Rolling_Low'] = df['low'].shift(1).rolling(window=ROLLING_PERIOD).min()

        return df.dropna()

    def get_atm_strike(self, spot_price):
        """Calculates At-The-Money (ATM) strike (Nifty multiples of 50)."""
        return round(spot_price / 50) * 50

    def _execute_trade(self, row, opt_type):
        """Simulates entering a trade."""
        self.in_position = True
        self.position_type = opt_type
        self.underlying_entry_price = row['close']

        # Calculate Option Chain specific symbol
        strike = self.get_atm_strike(self.underlying_entry_price)
        self.option_symbol = f"{SYMBOL}{int(strike)}{opt_type}"

        # Simulate highly dynamic ATM option premium.
        # Base is ~0.5% of the index, but we inject a random intraday implied volatility multiplier
        # between 0.8x and 1.5x so the premiums are truly dynamic (e.g. ₹96 to ₹180) and not stuck in a single range
        iv_multiplier = np.random.uniform(0.8, 1.5)
        simulated_atm_premium = (self.underlying_entry_price * 0.005) * iv_multiplier
        self.entry_price = simulated_atm_premium + SLIPPAGE # Slippage applies per unit of option premium

        # Dynamic Compounding: Calculate max lots we can buy with 95% of current capital
        max_investment = self.capital * MAX_CAPITAL_DEPLOYMENT
        # Nifty lot size is 50. Floor division to get number of full lots
        num_lots = int(max_investment / (self.entry_price * 50))

        # User requested max 10 lots per trade limit to prevent overexposure
        MAX_LOTS_PER_ORDER = 10

        num_lots = max(1, num_lots)
        num_lots = min(num_lots, MAX_LOTS_PER_ORDER) # Cap at max allowed quantity

        self.current_qty = num_lots * 50

        self.entry_time = row.name

        # Dynamic Risk/Reward Understanding
        adx_value = row[f'ADX_{ADX_PERIOD}']
        if adx_value >= 30:
            # Very Strong trend identified: Widen risk tolerance and aim for max profitability
            self.trade_sl_pct = 0.08      # 8% Stop Loss (give it room to breathe)
            self.trade_target_pct = 0.30  # 30% Take Profit
            self.trade_trailing_pct = 0.05 # 5% trailing (let winners run)
        else:
            # Moderate trend identified: Balanced scalping settings
            self.trade_sl_pct = 0.05      # 5% Stop Loss (cut fast)
            self.trade_target_pct = 0.15  # 15% Take Profit (1:3 Risk/Reward)
            self.trade_trailing_pct = 0.03 # 3% tight trailing

        self.current_sl = self.entry_price * (1 - self.trade_sl_pct)
        self.max_opt_price_seen = self.entry_price
        self.target_reached = False
        self.breakeven_reached = False

    def calculate_taxes_and_charges(self, entry_price, exit_price, qty):
        """Calculates total brokerage and government taxes for a complete round trip (Buy + Sell)."""
        buy_turnover = entry_price * qty
        sell_turnover = exit_price * qty
        total_turnover = buy_turnover + sell_turnover

        brokerage = BROKERAGE_PER_ORDER * 2 # Buy + Sell
        stt = sell_turnover * STT_PCT # STT is only on sell side for options
        txn_charges = total_turnover * EXCHANGE_TXN_CHARGE_PCT
        gst = (brokerage + txn_charges) * GST_PCT
        sebi_charges = total_turnover * SEBI_CHARGE_PCT
        stamp_duty = buy_turnover * STAMP_DUTY_PCT # Stamp duty only on buy side

        total_charges = brokerage + stt + txn_charges + gst + sebi_charges + stamp_duty
        return total_charges

    def _exit_trade(self, row, exit_price, reason):
        """Simulates exiting a trade and records the result."""
        exit_price = exit_price - SLIPPAGE # Slippage applies per unit of option premium

        gross_pnl = (exit_price - self.entry_price) * self.current_qty
        taxes = self.calculate_taxes_and_charges(self.entry_price, exit_price, self.current_qty)
        net_pnl = gross_pnl - taxes

        self.capital += net_pnl
        self.daily_pnl += net_pnl

        self.trades.append({
            'Entry_Time': self.entry_time,
            'Exit_Time': row.name,
            'Type': self.position_type,
            'Symbol': self.option_symbol,
            'Qty': self.current_qty,
            'Entry_Price': self.entry_price,
            'Exit_Price': exit_price,
            'Gross_PnL': gross_pnl,
            'Taxes': taxes,
            'Net_PnL': net_pnl,
            'Reason': reason
        })

        self.in_position = False
        self.position_type = None
        self.current_qty = 0

    def run(self):
        """Iterates through the data to simulate trading."""
        df = self.calculate_indicators()
        logger.info("Starting backtest loop...")

        for idx, row in df.iterrows():
            current_time = row.name.time()
            date = row.name.date()

            # Reset daily limits
            if date != self.current_date:
                self.current_date = date
                self.daily_pnl = 0.0
                self.kill_switch_active = False

            # Intraday Market Hours (09:15 to 15:15)
            # Brokers enforce MIS square-off around 3:15 PM - 3:20 PM. We use 15:15 to prevent overnight holds.
            if current_time >= time(15, 15):
                if self.in_position:
                    # Calculate current mocked option price based on underlying delta
                    if self.position_type == "CE":
                        opt_price_change = (row['close'] - self.underlying_entry_price) * 0.5
                    else: # PE
                        opt_price_change = (self.underlying_entry_price - row['close']) * 0.5
                    current_opt_price = max(1.0, self.entry_price + opt_price_change)

                    self._exit_trade(row, current_opt_price, "MIS Auto Square Off (15:15)")
                continue

            # Do not process pre-market data
            if current_time < time(9, 15):
                continue

            # Kill switch check
            if self.kill_switch_active:
                continue

            if self.daily_pnl <= MAX_LOSS_PER_DAY:
                self.kill_switch_active = True
                if self.in_position:
                    self._exit_trade(row, self.entry_price, "Kill Switch Hit")
                continue

            # Manage open position
            if self.in_position:
                # Mock price movement for the option based on cumulative underlying movement since entry
                # In a real scenario, use actual option data. Here we assume a delta of 0.5
                if self.position_type == "CE":
                    opt_price_change = (row['close'] - self.underlying_entry_price) * 0.5
                else: # PE
                    opt_price_change = (self.underlying_entry_price - row['close']) * 0.5

                current_opt_price = max(1.0, self.entry_price + opt_price_change) # options don't go below ~0

                # Track max price seen for Trailing Take Profit
                if current_opt_price > self.max_opt_price_seen:
                    self.max_opt_price_seen = current_opt_price

                # Check SL or Trailing Take Profit hit
                if current_opt_price <= self.current_sl:
                    reason = "Trailing Take Profit Hit" if self.target_reached else ("Break Even Hit" if self.breakeven_reached else "SL Hit")
                    self._exit_trade(row, self.current_sl, reason)
                    continue

                profit_pct = (current_opt_price - self.entry_price) / self.entry_price

                # 1. Target Reached -> Activate Trailing Take Profit
                if profit_pct >= self.trade_target_pct:
                    self.target_reached = True
                    potential_new_sl = self.max_opt_price_seen * (1 - self.trade_trailing_pct)
                    if potential_new_sl > self.current_sl:
                        self.current_sl = potential_new_sl

                # 2. Break Even (1:1 RR) -> Move SL to entry
                elif profit_pct >= self.trade_sl_pct and not self.target_reached and not self.breakeven_reached:
                    self.breakeven_reached = True
                    # Set SL to slightly above entry to cover minimum slippage/fees
                    self.current_sl = self.entry_price * 1.01

            # Look for entries if not in position
            else:
                if row[f'ADX_{ADX_PERIOD}'] < ADX_THRESHOLD:
                    continue # Sideways market

                close = row['close']
                open_price = row['open']
                high = row['high']
                low = row['low']
                r_high = row['Rolling_High']
                r_low = row['Rolling_Low']
                vwap = row['VWAP']
                ema = row[f'EMA_{EMA_PERIOD}']
                rsi = row[f'RSI_{RSI_PERIOD}']
                adx_slope = row['ADX_Slope']

                # We need valid rolling levels and indicators to trade
                if pd.isna(r_high) or pd.isna(r_low) or pd.isna(rsi) or pd.isna(adx_slope):
                    continue

                # 1. Breakout Strategy (Momentum)
                # Bullish Breakout of 30-Min High: Price above VWAP/EMA AND RSI > 50 (Bullish control)
                if close > r_high and close > vwap and close > ema and rsi > 50:
                    self._execute_trade(row, "CE")
                    continue

                # Bearish Breakdown of 30-Min Low: Price below VWAP/EMA AND RSI < 50 (Bearish control)
                elif close < r_low and close < vwap and close < ema and rsi < 50:
                    self._execute_trade(row, "PE")
                    continue

                # 2. Mean-Reversion Strategy (Wick Rejections)
                # Bullish Rejection: Wick below low, closes inside range, RSI supports upside
                if low < r_low and close > r_low and close > open_price and close > vwap and close > ema and rsi > 50:
                    self._execute_trade(row, "CE")
                    continue

                # Bearish Rejection: Wick above high, closes inside range, RSI supports downside
                if high > r_high and close < r_high and close < open_price and close < vwap and close < ema and rsi < 50:
                    self._execute_trade(row, "PE")
                    continue

        self._print_summary()

    def _print_summary(self):
        df_trades = pd.DataFrame(self.trades)
        logger.info("\n================= BACKTEST SUMMARY =================")
        logger.info(f"Initial Capital: {self.starting_capital:.2f}")
        logger.info(f"Final Capital:   {self.capital:.2f}")
        logger.info(f"Net PnL:         {self.capital - self.starting_capital:.2f}")

        if not df_trades.empty:
            logger.info("\n--- DETAILED TRADE LOG ---")
            for idx, trade in df_trades.iterrows():
                entry_time_str = trade['Entry_Time'].strftime("%Y-%m-%d %H:%M")
                exit_time_str = trade['Exit_Time'].strftime("%Y-%m-%d %H:%M")

                logger.info(f"Trade #{idx+1}: {trade['Symbol']} (Qty: {trade['Qty']}) | "
                            f"Entry: {entry_time_str} @ ₹{trade['Entry_Price']:.2f} | "
                            f"Exit: {exit_time_str} @ ₹{trade['Exit_Price']:.2f} | "
                            f"Reason: {trade['Reason']} | "
                            f"Net PnL: ₹{trade['Net_PnL']:.2f}")
            logger.info("--------------------------\n")

            winning_trades = df_trades[df_trades['Net_PnL'] > 0]
            total_taxes = df_trades['Taxes'].sum()
            gross_pnl_sum = df_trades['Gross_PnL'].sum()
            logger.info(f"Total Trades:    {len(df_trades)}")
            logger.info(f"Win Rate:        {(len(winning_trades) / len(df_trades)) * 100:.2f}%")
            logger.info(f"Gross PnL:       {gross_pnl_sum:.2f}")
            logger.info(f"Total Taxes:     {total_taxes:.2f}")
        else:
            logger.info("No trades executed.")
        logger.info("====================================================\n")

if __name__ == "__main__":
    # Generate mock data for demonstration
    # In reality, load this from a CSV: df = pd.read_csv('nifty_1min.csv', parse_dates=['datetime'], index_col='datetime')

    dates = pd.date_range(start="2024-01-01 09:15:00", end="2024-01-10 15:30:00", freq='1min')
    # Filter to only market hours
    dates = [d for d in dates if time(9, 15) <= d.time() <= time(15, 30)]

    np.random.seed(42) # Keep seed for reproducibility

    # Restore a more standard random walk generator. Since the strategy logic
    # itself was improved (rolling ranges + mean reversion), it should perform
    # naturally without synthetic cycle manipulation.
    n = len(dates)

    # Simple cumulative random walk with standard intraday index drift
    # Tuned down the per-candle variance slightly because 1-min candles move less points per candle than 3-min
    close_prices = 22000 + (np.random.randn(n) * 4).cumsum()

    # Standardize OHLC calculation
    open_prices = close_prices - np.random.randn(n) * 2
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(n) * 3)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(n) * 3)

    # Ensure High is max and Low is min
    high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
    low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

    volumes = np.random.randint(10000, 150000, size=n) # higher realistic volumes

    df_mock = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    }, index=pd.DatetimeIndex(dates))

    logger.info("Running backtest on mock data...")
    tester = Backtester(df_mock)
    tester.run()