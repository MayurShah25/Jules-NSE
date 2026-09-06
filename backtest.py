import logging
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, time

# ==========================================
# CONFIGURATION & PARAMETERS
# ==========================================
SYMBOL = "NIFTY"
TIMEFRAME = "3min"
QTY = 50

MAX_LOSS_PER_DAY = -5000
STOP_LOSS_PCT = 0.10
TRAILING_SL_PCT = 0.05

EMA_PERIOD = 50
ADX_PERIOD = 14
ADX_THRESHOLD = 20

# Simplified backtest assumptions
INITIAL_CAPITAL = 100000
SLIPPAGE = 1.0 # fixed slippage in points
BROKERAGE = 40 # round trip brokerage in INR per trade

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.capital = INITIAL_CAPITAL
        self.trades = []

        # Current state
        self.in_position = False
        self.position_type = None
        self.entry_price = 0.0
        self.entry_time = None
        self.current_sl = 0.0
        self.max_profit_seen = 0.0

        self.daily_pnl = 0.0
        self.kill_switch_active = False
        self.current_date = None

    def calculate_indicators(self):
        """Calculates necessary indicators on the entire dataset upfront (Vectorized approach for speed)."""
        logger.info("Calculating indicators...")
        df = self.data.copy()

        # EMA, ADX, VWAP
        df.ta.ema(length=EMA_PERIOD, append=True)
        df.ta.adx(length=ADX_PERIOD, append=True)

        # Simplified VWAP for backtesting (using typical price)
        df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
        df['Vol_x_Typ'] = df['volume'] * df['Typical_Price']

        # Calculate daily cumulative volume and Vol_x_Typ
        df['Date'] = df.index.date
        df['Cum_Vol'] = df.groupby('Date')['volume'].cumsum()
        df['Cum_Vol_x_Typ'] = df.groupby('Date')['Vol_x_Typ'].cumsum()
        df['VWAP'] = df['Cum_Vol_x_Typ'] / df['Cum_Vol']

        # Calculate rolling Day High / Day Low (excluding current candle for breakout check)
        # Shift the high/low by 1 to get the high/low up to the previous candle within the same day
        df['Prev_High'] = df.groupby('Date')['high'].shift(1)
        df['Prev_Low'] = df.groupby('Date')['low'].shift(1)

        df['Day_High'] = df.groupby('Date')['Prev_High'].cummax()
        df['Day_Low'] = df.groupby('Date')['Prev_Low'].cummin()

        return df.dropna()

    def _execute_trade(self, row, opt_type):
        """Simulates entering a trade."""
        self.in_position = True
        self.position_type = opt_type
        # Assuming ATM option price is roughly 100 for simplicity in this structural outline
        # In a real backtest, you would need options data mapping
        self.entry_price = 100.0 + (SLIPPAGE / QTY)
        self.entry_time = row.name

        self.current_sl = self.entry_price * (1 - STOP_LOSS_PCT)
        self.max_profit_seen = 0.0

    def _exit_trade(self, row, exit_price, reason):
        """Simulates exiting a trade and records the result."""
        exit_price = exit_price - (SLIPPAGE / QTY)

        pnl = (exit_price - self.entry_price) * QTY
        pnl -= BROKERAGE

        self.capital += pnl
        self.daily_pnl += pnl

        self.trades.append({
            'Entry_Time': self.entry_time,
            'Exit_Time': row.name,
            'Type': self.position_type,
            'Entry_Price': self.entry_price,
            'Exit_Price': exit_price,
            'PnL': pnl,
            'Reason': reason
        })

        self.in_position = False
        self.position_type = None

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

            # Market Hours check (09:15 to 15:30)
            if not (time(9, 15) <= current_time <= time(15, 30)):
                if self.in_position:
                    # Intraday square off
                    self._exit_trade(row, self.entry_price, "EOD Square Off") # Using entry price as mock exit price for structural simplicity
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
                # Mock price movement for the option based on underlying movement
                # In a real scenario, use actual option data. Here we assume a delta of 0.5
                if self.position_type == "CE":
                    opt_price_change = (row['close'] - row['open']) * 0.5
                else: # PE
                    opt_price_change = (row['open'] - row['close']) * 0.5

                current_opt_price = self.entry_price + opt_price_change

                # Check SL hit
                if current_opt_price <= self.current_sl:
                    self._exit_trade(row, self.current_sl, "SL Hit")
                    continue

                # Update Trailing SL
                potential_new_sl = current_opt_price * (1 - TRAILING_SL_PCT)
                if potential_new_sl > self.current_sl:
                    self.current_sl = potential_new_sl

            # Look for entries if not in position
            else:
                if row[f'ADX_{ADX_PERIOD}'] < ADX_THRESHOLD:
                    continue # Sideways market

                close = row['close']
                day_high = row['Day_High']
                day_low = row['Day_Low']
                vwap = row['VWAP']
                ema = row[f'EMA_{EMA_PERIOD}']

                # We need valid day high/low to trade
                if pd.isna(day_high) or pd.isna(day_low):
                    continue

                # Bullish Breakout
                if close > day_high and close > vwap and close > ema:
                    self._execute_trade(row, "CE")

                # Bearish Breakdown
                elif close < day_low and close < vwap and close < ema:
                    self._execute_trade(row, "PE")

        self._print_summary()

    def _print_summary(self):
        df_trades = pd.DataFrame(self.trades)
        logger.info("\n================= BACKTEST SUMMARY =================")
        logger.info(f"Initial Capital: {INITIAL_CAPITAL}")
        logger.info(f"Final Capital:   {self.capital:.2f}")
        logger.info(f"Net PnL:         {self.capital - INITIAL_CAPITAL:.2f}")

        if not df_trades.empty:
            winning_trades = df_trades[df_trades['PnL'] > 0]
            logger.info(f"Total Trades:    {len(df_trades)}")
            logger.info(f"Win Rate:        {(len(winning_trades) / len(df_trades)) * 100:.2f}%")
            logger.info(f"Max Drawdown / Metrics can be added here.")
        else:
            logger.info("No trades executed.")
        logger.info("====================================================\n")

if __name__ == "__main__":
    # Generate mock data for demonstration
    # In reality, load this from a CSV: df = pd.read_csv('nifty_3min.csv', parse_dates=['datetime'], index_col='datetime')

    dates = pd.date_range(start="2024-01-01 09:15:00", end="2024-01-05 15:30:00", freq='3min')
    # Filter to only market hours
    dates = [d for d in dates if time(9, 15) <= d.time() <= time(15, 30)]

    np.random.seed(42)
    close_prices = 22000 + np.random.randn(len(dates)).cumsum() * 5
    high_prices = close_prices + np.random.rand(len(dates)) * 5
    low_prices = close_prices - np.random.rand(len(dates)) * 5
    open_prices = close_prices - np.random.randn(len(dates)) * 2
    volumes = np.random.randint(1000, 50000, size=len(dates))

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