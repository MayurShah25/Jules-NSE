import time
import logging
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION & PARAMETERS
# ==========================================
SYMBOL = "NIFTY"
TIMEFRAME = "1min"  # 1-minute timeframe for hyper-scalping
QTY = 500  # 10 Nifty lots to increase net profitability against flat fees

# Risk Management
MAX_LOSS_PER_DAY = -50000  # Kill switch limit scaled for 10 lots
# Risk metrics are now calculated dynamically per trade

# Trend & Momentum Filters
EMA_PERIOD = 9
ADX_PERIOD = 14
ADX_THRESHOLD = 10

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# BROKER INTERFACE (Mocked for Structure)
# ==========================================
class BrokerAPI:
    """Mock interface for broker APIs like Zerodha KiteConnect, Dhan, or Fyers."""
    def __init__(self):
        self.connected = True

    def get_historical_data(self, symbol, timeframe):
        # Returns a pandas DataFrame with OHLCV data
        pass

    def get_ltp(self, symbol):
        # Returns Last Traded Price
        return 22000.0

    def place_order(self, symbol, side, qty, order_type="MARKET", price=0.0):
        # Places an order and returns order_id
        logger.info(f"Placing {side} order for {qty} of {symbol} at {order_type}")
        return "ORDER123"

    def get_pnl(self):
        # Returns today's realized/unrealized MTM
        return 0.0

# ==========================================
# RISK MANAGEMENT MODULE
# ==========================================
class RiskManager:
    def __init__(self, broker: BrokerAPI):
        self.broker = broker
        self.daily_pnl = 0.0
        self.kill_switch_active = False

    def check_kill_switch(self):
        """Checks if the daily max loss limit has been hit."""
        if self.kill_switch_active:
            return True

        self.daily_pnl = self.broker.get_pnl()
        if self.daily_pnl <= MAX_LOSS_PER_DAY:
            logger.error(f"KILL SWITCH TRIGGERED! Max Loss of {MAX_LOSS_PER_DAY} reached. Daily PnL: {self.daily_pnl}")
            self.kill_switch_active = True
            return True
        return False

    def calculate_sl(self, entry_price, sl_pct):
        """Calculates initial Stop Loss."""
        sl_price = entry_price * (1 - sl_pct)
        return sl_price

    def update_trailing_take_profit(self, current_price, current_sl, max_price_seen, trailing_pct):
        """Calculates Trailing Take Profit (TTP) locking in gains."""
        potential_new_sl = max_price_seen * (1 - trailing_pct)
        if potential_new_sl > current_sl:
            return potential_new_sl
        return current_sl

# ==========================================
# STRATEGY LOGIC
# ==========================================
class ScalpingStrategy:
    def __init__(self, broker: BrokerAPI):
        self.broker = broker
        self.risk_manager = RiskManager(broker)
        self.in_position = False
        self.current_position = None  # 'CE' or 'PE'
        self.entry_price = 0.0
        self.current_sl = 0.0
        self.option_symbol = ""

    def fetch_and_calculate_indicators(self):
        """Fetches data and calculates Rolling High/Low, VWAP, EMA, ADX."""
        df = self.broker.get_historical_data(SYMBOL, TIMEFRAME)
        if df is None or len(df) < 20:
            return None

        # Assuming 'df' has columns: datetime, open, high, low, close, volume
        # 1. Rolling 5-Minute High / Low (5 candles on 1min chart)
        # Exclude the current live, unclosed candle (-1)
        rolling_data = df.iloc[-6:-1]
        rolling_high = rolling_data['high'].max()
        rolling_low = rolling_data['low'].min()

        # 2. Indicators (using pandas_ta)
        df.ta.ema(length=EMA_PERIOD, append=True)
        df.ta.adx(length=ADX_PERIOD, append=True)
        df.ta.vwap(append=True)

        latest_data = df.iloc[-1]

        return {
            'close': latest_data['close'],
            'open': latest_data['open'],
            'high': latest_data['high'],
            'low': latest_data['low'],
            'rolling_high': rolling_high,
            'rolling_low': rolling_low,
            'ema': latest_data[f'EMA_{EMA_PERIOD}'],
            'adx': latest_data[f'ADX_{ADX_PERIOD}'],
            'vwap': latest_data['VWAP_D']
        }

    def get_atm_strike(self, spot_price):
        """Calculates At-The-Money (ATM) strike."""
        return round(spot_price / 50) * 50

    def get_option_symbol(self, strike, opt_type):
        """Constructs option trading symbol. (Format depends on broker)"""
        # Example format: NIFTY24MAY22000CE
        return f"{SYMBOL}_ATM_{opt_type}" # Simplified placeholder

    def execute_trade(self, opt_type, spot_price, adx_value):
        """Executes the entry order and sets dynamic initial SL."""
        strike = self.get_atm_strike(spot_price)
        self.option_symbol = self.get_option_symbol(strike, opt_type)

        # Place Market Order
        self.broker.place_order(self.option_symbol, "BUY", QTY)

        # Fetch Entry Price (Assuming immediate fill for simplicity)
        self.entry_price = self.broker.get_ltp(self.option_symbol)

        # Dynamic Risk Allocation based on trend strength
        if adx_value >= 25:
            self.trade_sl_pct = 0.08
            self.trade_target_pct = 0.32
            self.trade_trailing_pct = 0.05
            logger.info("Strong Trend Detected. Engaging Max Profitability settings (1:4 RR).")
        else:
            self.trade_sl_pct = 0.05
            self.trade_target_pct = 0.10
            self.trade_trailing_pct = 0.02
            logger.info("Weak Trend Detected. Engaging Tight Scalp settings (1:2 RR).")

        # Calculate & System Place SL
        self.current_sl = self.risk_manager.calculate_sl(self.entry_price, self.trade_sl_pct)
        # In reality, place a Stop Loss Market (SL-M) order here with the broker

        self.in_position = True
        self.current_position = opt_type
        self.max_opt_price_seen = self.entry_price
        self.target_reached = False
        self.breakeven_reached = False
        logger.info(f"Entered {opt_type} at {self.entry_price}. Initial SL: {self.current_sl}")

    def exit_trade(self, reason):
        """Exits current position."""
        self.broker.place_order(self.option_symbol, "SELL", QTY)
        logger.info(f"Exited position {self.current_position}. Reason: {reason}")
        self.in_position = False
        self.current_position = None
        self.entry_price = 0.0
        self.current_sl = 0.0

    def manage_open_position(self):
        """Manages Trailing Take Profit, Breakeven SL, and Stop Loss hits."""
        current_opt_price = self.broker.get_ltp(self.option_symbol)

        if current_opt_price > self.max_opt_price_seen:
            self.max_opt_price_seen = current_opt_price

        # 1. Check SL / TTP Hit
        if current_opt_price <= self.current_sl:
            reason = "Trailing Take Profit Hit" if self.target_reached else ("Break Even Hit" if self.breakeven_reached else "Stop Loss Hit")
            self.exit_trade(reason)
            return

        profit_pct = (current_opt_price - self.entry_price) / self.entry_price

        # 2. Update Trailing Take Profit (Target Reached)
        if profit_pct >= self.trade_target_pct:
            if not self.target_reached:
                logger.info(f"Target Reached! Activating Trailing Take Profit.")
                self.target_reached = True

            new_sl = self.risk_manager.update_trailing_take_profit(current_opt_price, self.current_sl, self.max_opt_price_seen, self.trade_trailing_pct)
            if new_sl > self.current_sl:
                logger.info(f"Trailing Take Profit updated to {new_sl}")
                self.current_sl = new_sl
                # In reality, modify the pending SL-M order with the broker here

        # 3. Update to Break Even (1:1 RR Reached)
        elif profit_pct >= self.trade_sl_pct and not self.target_reached and not self.breakeven_reached:
            self.breakeven_reached = True
            new_sl = self.entry_price * 1.01 # Slightly above entry to cover fees
            logger.info(f"1:1 R:R Reached. Moving SL to Break Even: {new_sl}")
            self.current_sl = new_sl
            # In reality, modify the pending SL-M order with the broker here

    def run_cycle(self):
        """Main strategy loop executed every tick/candle."""
        if self.risk_manager.check_kill_switch():
            if self.in_position:
                self.exit_trade("Kill Switch Triggered")
            return

        if self.in_position:
            self.manage_open_position()
            return

        # Fetch market data and indicators
        market_data = self.fetch_and_calculate_indicators()
        if not market_data:
            return

        close_price = market_data['close']
        open_price = market_data['open']
        high_price = market_data['high']
        low_price = market_data['low']
        r_high = market_data['rolling_high']
        r_low = market_data['rolling_low']
        ema = market_data['ema']
        vwap = market_data['vwap']
        adx = market_data['adx']

        # ==========================================
        # FILTERS
        # ==========================================
        # 1. Sideways Market Filter
        if adx < ADX_THRESHOLD:
            logger.debug(f"Market is sideways (ADX < {ADX_THRESHOLD}). No trades will be taken.")
            return

        # ==========================================
        # ENTRY LOGIC
        # ==========================================
        # 1. Breakout Strategy
        # Long CE: Price breaks Rolling High AND Price is above VWAP & EMA
        if close_price > r_high and close_price > vwap and close_price > ema:
            logger.info("Bullish Breakout Detected.")
            self.execute_trade("CE", close_price, adx)
            return

        # Long PE: Price breaks Rolling Low AND Price is below VWAP & EMA
        elif close_price < r_low and close_price < vwap and close_price < ema:
            logger.info("Bearish Breakdown Detected.")
            self.execute_trade("PE", close_price, adx)
            return

        # 2. Mean-Reversion Strategy
        # Bullish Rejection: Wick poked below rolling low, closed above, in an uptrend
        if low_price < r_low and close_price > r_low and close_price > open_price and close_price > vwap and close_price > ema:
            logger.info("Bullish Mean-Rejection Detected.")
            self.execute_trade("CE", close_price, adx)
            return

        # Bearish Rejection: Wick poked above rolling high, closed below, in a downtrend
        if high_price > r_high and close_price < r_high and close_price < open_price and close_price < vwap and close_price < ema:
            logger.info("Bearish Mean-Rejection Detected.")
            self.execute_trade("PE", close_price, adx)
            return

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    broker = BrokerAPI()
    bot = ScalpingStrategy(broker)

    logger.info("Starting Options Scalping Bot...")

    try:
        while True:
            now = datetime.now().time()
            # Indian Market Hours check (09:15 AM to 03:30 PM)
            if datetime.strptime("09:15", "%H:%M").time() <= now <= datetime.strptime("15:30", "%H:%M").time():
                bot.run_cycle()
            else:
                logger.info("Market Closed.")
                if now > datetime.strptime("15:30", "%H:%M").time():
                    break

            # Wait for next cycle (e.g., check every 1 second or based on websocket stream)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
        if bot.in_position:
            bot.exit_trade("Manual Stop")
