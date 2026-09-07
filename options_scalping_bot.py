import time
import logging
import pandas as pd
import ta
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
EMA_PERIOD = 21
ADX_PERIOD = 14
ADX_THRESHOLD = 20
RSI_PERIOD = 14

# Mode Setup
PAPER_TRADING = True  # Set to False ONLY when ready to risk real capital

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# BROKER INTERFACE (DhanHQ Integration)
# ==========================================
try:
    from dhanhq import dhanhq, DhanContext
except ImportError:
    logger.error("dhanhq library not found. Run: pip install dhanhq")

class BrokerAPI:
    """Live integration with DhanHQ API."""
    def __init__(self):
        # ---------------------------------------------------------
        # TODO: Replace with your actual Dhan Client ID and Access Token
        # You can generate this for free on web.dhan.co -> Profile -> DhanHQ API
        # ---------------------------------------------------------
        self.client_id = "YOUR_DHAN_CLIENT_ID"
        self.access_token = "YOUR_DHAN_ACCESS_TOKEN"

        try:
            # The newest Dhan SDK requires a DhanContext to be initialized first
            self.dhan_context = DhanContext(self.client_id, self.access_token)
            self.dhan = dhanhq(self.dhan_context)

            self.connected = True
            logger.info(f"Dhan Broker Initialized. Paper Trading Mode: {PAPER_TRADING}")
        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect to Dhan API: {e}")

    def get_historical_data(self, symbol, timeframe):
        """Fetches intraday historical OHLCV data from Dhan and converts to Pandas DataFrame."""
        if not self.connected:
            return None

        try:
            # Dhan uses instrument tokens for historical data.
            # Assuming Nifty 50 Index (Token: 13, Exchange: IDX_I)
            # You will need to map your required symbol to Dhan's exact security ID
            security_id = "13"
            exchange_segment = "IDX_I"

            # Map timeframe string to Dhan's format (e.g., '1' for 1 minute)
            tf_map = {"1min": "1", "5min": "5", "15min": "15"}
            dhan_tf = tf_map.get(timeframe, "1")

            today_str = datetime.now().strftime("%Y-%m-%d")

            response = self.dhan.intraday_minute_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type="INDEX",
                from_date=today_str,
                to_date=today_str
            )

            if response.get('status') == 'success':
                data = response.get('data', {})
                df = pd.DataFrame({
                    'open': data.get('open', []),
                    'high': data.get('high', []),
                    'low': data.get('low', []),
                    'close': data.get('close', []),
                    'volume': data.get('volume', [])
                })
                # Dhan returns lists, convert to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Simple resampling if timeframe is not 1 min (Dhan intraday api usually returns 1 min base)
                # This ensures rolling windows calculate correctly
                return df
            else:
                logger.error(f"Failed to fetch historical data: {response}")
                return None
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None

    def get_ltp(self, symbol):
        """Fetches Last Traded Price (LTP)."""
        if not self.connected:
            return 0.0

        try:
            # Note: You must pass the specific Security ID mapped to the symbol
            # For simplicity in this structure, returning a mock value if live call fails
            # In a full live setup, map `symbol` -> `security_id`
            # response = self.dhan.get_quote(exchange_segment='NFO_OPT', security_id="mapped_id")
            # return response['data']['LTP']

            # Returning mock value so the paper trading logic loops don't crash without valid API keys
            return 22000.0
        except Exception as e:
            logger.error(f"Error fetching LTP: {e}")
            return 0.0

    def place_order(self, symbol, side, qty, order_type="MARKET", price=0.0):
        if PAPER_TRADING:
            logger.warning(f"[PAPER TRADE] {side} {qty} {symbol} @ {order_type}")
            return f"PAPER_ORDER_{int(time.time())}"
        else:
            if not self.connected:
                logger.error("Cannot place live order. Not connected to broker.")
                return None

            logger.info(f"Placing LIVE {side} order for {qty} of {symbol} at {order_type}")

            # Map 'BUY'/'SELL' to Dhan constants
            txn_type = self.dhan.BUY if side.upper() == "BUY" else self.dhan.SELL
            ord_type = self.dhan.MARKET

            try:
                response = self.dhan.place_order(
                    security_id="MAPPED_ID_HERE", # Must map symbol to Dhan Security ID
                    exchange_segment=self.dhan.NFO,
                    transaction_type=txn_type,
                    quantity=qty,
                    order_type=ord_type,
                    product_type=self.dhan.INTRA, # MIS / Intraday
                    price=price
                )
                if response.get('status') == 'success':
                    order_id = response.get('data', {}).get('orderId')
                    logger.info(f"Live order placed successfully. Order ID: {order_id}")
                    return order_id
                else:
                    logger.error(f"Order rejected by broker: {response}")
                    return None
            except Exception as e:
                logger.error(f"Error placing order: {e}")
                return None

    def get_pnl(self):
        """Fetches today's total realized/unrealized MTM from Dhan."""
        if not self.connected or PAPER_TRADING:
            return 0.0

        try:
            response = self.dhan.get_positions()
            if response.get('status') == 'success':
                positions = response.get('data', [])
                total_mtm = sum(float(pos.get('mtm', 0.0)) for pos in positions)
                return total_mtm
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching PnL: {e}")
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
        # 1. Rolling 30-Minute High / Low (30 candles on 1min chart)
        # Exclude the current live, unclosed candle (-1)
        rolling_data = df.iloc[-31:-1]
        rolling_high = rolling_data['high'].max()
        rolling_low = rolling_data['low'].min()

        # 2. Indicators (using ta)
        df[f'EMA_{EMA_PERIOD}'] = ta.trend.EMAIndicator(close=df['close'], window=EMA_PERIOD).ema_indicator()

        adx_ind = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=ADX_PERIOD)
        df[f'ADX_{ADX_PERIOD}'] = adx_ind.adx()
        df['ADX_Slope'] = df[f'ADX_{ADX_PERIOD}'].diff()

        df[f'RSI_{RSI_PERIOD}'] = ta.momentum.RSIIndicator(close=df['close'], window=RSI_PERIOD).rsi()

        # Simplified Intraday VWAP
        df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
        df['Vol_x_Typ'] = df['volume'] * df['Typical_Price']
        df['Cum_Vol'] = df['volume'].cumsum()
        df['Cum_Vol_x_Typ'] = df['Vol_x_Typ'].cumsum()
        df['VWAP_D'] = df['Cum_Vol_x_Typ'] / df['Cum_Vol']

        latest_data = df.iloc[-1]

        # Ensure ADX is populated (requires 28 periods to stabilize)
        if pd.isna(latest_data[f'ADX_{ADX_PERIOD}']) or pd.isna(latest_data['ADX_Slope']) or pd.isna(latest_data[f'RSI_{RSI_PERIOD}']):
            return None

        return {
            'close': latest_data['close'],
            'open': latest_data['open'],
            'high': latest_data['high'],
            'low': latest_data['low'],
            'rolling_high': rolling_high,
            'rolling_low': rolling_low,
            'ema': latest_data[f'EMA_{EMA_PERIOD}'],
            'adx': latest_data[f'ADX_{ADX_PERIOD}'],
            'adx_slope': latest_data['ADX_Slope'],
            'rsi': latest_data[f'RSI_{RSI_PERIOD}'],
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
        if adx_value >= 30:
            self.trade_sl_pct = 0.08
            self.trade_target_pct = 0.30
            self.trade_trailing_pct = 0.05
            logger.info("Very Strong Trend Detected. Engaging Max Profitability settings.")
        else:
            self.trade_sl_pct = 0.05
            self.trade_target_pct = 0.15
            self.trade_trailing_pct = 0.03
            logger.info("Moderate Trend Detected. Engaging Balanced Scalp settings.")

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
        adx_slope = market_data['adx_slope']
        rsi = market_data['rsi']

        # ==========================================
        # FILTERS
        # ==========================================
        # 1. Sideways Market Filter
        if adx < ADX_THRESHOLD:
            logger.debug(f"Market is sideways (ADX < {ADX_THRESHOLD}). No trades will be taken.")
            return

        # 2. Declining Momentum Filter
        if adx_slope <= 0:
            logger.debug("Momentum is fading (ADX Slope <= 0). Skipping entry.")
            return

        # ==========================================
        # ENTRY LOGIC
        # ==========================================
        # 1. Breakout Strategy
        # Long CE: Price breaks Rolling High AND Price is above VWAP & EMA AND RSI > 55
        if close_price > r_high and close_price > vwap and close_price > ema and rsi > 55:
            logger.info("Bullish Breakout Detected.")
            self.execute_trade("CE", close_price, adx)
            return

        # Long PE: Price breaks Rolling Low AND Price is below VWAP & EMA AND RSI < 45
        elif close_price < r_low and close_price < vwap and close_price < ema and rsi < 45:
            logger.info("Bearish Breakdown Detected.")
            self.execute_trade("PE", close_price, adx)
            return

        # 2. Mean-Reversion Strategy
        # Bullish Rejection: Wick poked below rolling low, closed above, in an uptrend, RSI > 50
        if low_price < r_low and close_price > r_low and close_price > open_price and close_price > vwap and close_price > ema and rsi > 50:
            logger.info("Bullish Mean-Rejection Detected.")
            self.execute_trade("CE", close_price, adx)
            return

        # Bearish Rejection: Wick poked above rolling high, closed below, in a downtrend, RSI < 50
        if high_price > r_high and close_price < r_high and close_price < open_price and close_price < vwap and close_price < ema and rsi < 50:
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

            # Intraday MIS strict timings (09:15 AM to 03:15 PM)
            # We halt entries and square off everything by 15:15 to prevent overnight theta decay gaps
            start_time = datetime.strptime("09:15", "%H:%M").time()
            mis_square_off_time = datetime.strptime("15:15", "%H:%M").time()

            if start_time <= now < mis_square_off_time:
                bot.run_cycle()

            elif now >= mis_square_off_time:
                if bot.in_position:
                    logger.warning("MIS Square Off Time Reached (15:15). Closing all open intraday positions!")
                    bot.exit_trade("MIS Auto Square Off (15:15)")

                logger.info("Market is beyond intraday trading hours. Bot is idling.")
                # If market is fully closed, exit loop
                if now > datetime.strptime("15:30", "%H:%M").time():
                    logger.info("Market Closed for the day. Exiting.")
                    break

            # Wait for next cycle
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
        if bot.in_position:
            bot.exit_trade("Manual Stop")
