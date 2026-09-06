import time
import logging
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION & PARAMETERS
# ==========================================
SYMBOL = "NIFTY"
TIMEFRAME = "3min"  # 3-minute timeframe for scalping
QTY = 50  # Nifty lot size

# Risk Management
MAX_LOSS_PER_DAY = -5000  # Kill switch limit (in INR)
STOP_LOSS_PCT = 0.10      # 10% stop loss on premium
TRAILING_SL_PCT = 0.05    # 5% trailing SL

# Trend & Momentum Filters
EMA_PERIOD = 50
ADX_PERIOD = 14
ADX_THRESHOLD = 20

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

    def calculate_sl_and_target(self, entry_price):
        """Calculates initial Stop Loss."""
        sl_price = entry_price * (1 - STOP_LOSS_PCT)
        return sl_price

    def update_trailing_sl(self, current_price, current_sl):
        """Updates trailing stop loss."""
        potential_new_sl = current_price * (1 - TRAILING_SL_PCT)
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
        """Fetches data and calculates Day High, Day Low, VWAP, EMA, ADX."""
        df = self.broker.get_historical_data(SYMBOL, TIMEFRAME)
        if df is None or df.empty:
            return None

        # Assuming 'df' has columns: datetime, open, high, low, close, volume
        # 1. Day High / Day Low
        # In a live scenario, you filter today's data to find the rolling Day High/Low
        # Calculate up to the PREVIOUS candle so the current close can break it
        today_data = df[df.index.date == datetime.today().date()]
        if len(today_data) > 1:
            # exclude the current candle
            day_high = today_data['high'].iloc[:-1].max()
            day_low = today_data['low'].iloc[:-1].min()
        else:
            # fallback if only one candle exists today
            day_high, day_low = df['high'].iloc[-1], df['low'].iloc[-1]

        # 2. Indicators (using pandas_ta)
        df.ta.ema(length=EMA_PERIOD, append=True)
        df.ta.adx(length=ADX_PERIOD, append=True)
        df.ta.vwap(append=True)

        latest_data = df.iloc[-1]

        return {
            'close': latest_data['close'],
            'day_high': day_high,
            'day_low': day_low,
            'ema_50': latest_data[f'EMA_{EMA_PERIOD}'],
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

    def execute_trade(self, opt_type, spot_price):
        """Executes the entry order and sets initial SL."""
        strike = self.get_atm_strike(spot_price)
        self.option_symbol = self.get_option_symbol(strike, opt_type)

        # Place Market Order
        self.broker.place_order(self.option_symbol, "BUY", QTY)

        # Fetch Entry Price (Assuming immediate fill for simplicity)
        self.entry_price = self.broker.get_ltp(self.option_symbol)

        # Calculate & System Place SL
        self.current_sl = self.risk_manager.calculate_sl_and_target(self.entry_price)
        # In reality, place a Stop Loss Market (SL-M) order here with the broker

        self.in_position = True
        self.current_position = opt_type
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
        """Manages Trailing SL and Stop Loss hits."""
        current_opt_price = self.broker.get_ltp(self.option_symbol)

        # 1. Check SL Hit
        if current_opt_price <= self.current_sl:
            self.exit_trade("Stop Loss Hit")
            return

        # 2. Update Trailing SL
        new_sl = self.risk_manager.update_trailing_sl(current_opt_price, self.current_sl)
        if new_sl > self.current_sl:
            logger.info(f"Trailing SL updated from {self.current_sl} to {new_sl}")
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
        day_high = market_data['day_high']
        day_low = market_data['day_low']
        ema_50 = market_data['ema_50']
        vwap = market_data['vwap']
        adx = market_data['adx']

        # ==========================================
        # FILTERS
        # ==========================================
        # 1. Sideways Market Filter
        if adx < ADX_THRESHOLD:
            logger.debug("Market is sideways (ADX < 20). No trades will be taken.")
            return

        # ==========================================
        # ENTRY LOGIC
        # ==========================================
        # Long CE: Price breaks Day High AND Price is above VWAP & EMA 50
        if close_price > day_high and close_price > vwap and close_price > ema_50:
            logger.info("Bullish Breakout Detected.")
            self.execute_trade("CE", close_price)

        # Long PE: Price breaks Day Low AND Price is below VWAP & EMA 50
        elif close_price < day_low and close_price < vwap and close_price < ema_50:
            logger.info("Bearish Breakdown Detected.")
            self.execute_trade("PE", close_price)

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
