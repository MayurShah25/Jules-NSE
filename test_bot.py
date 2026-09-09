from options_scalping_bot import ScalpingStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MockBroker:
    def __init__(self):
        self.connected = True

    def get_historical_data(self, symbol, timeframe):
        # Create mock data with 100 candles
        now = datetime.now()
        dates = [now - timedelta(minutes=i) for i in range(100, 0, -1)]
        df = pd.DataFrame({
            'datetime': dates,
            'open': np.random.rand(100) * 100 + 10000,
            'high': np.random.rand(100) * 100 + 10100,
            'low': np.random.rand(100) * 100 + 9900,
            'close': np.random.rand(100) * 100 + 10000,
            'volume': np.random.randint(100, 1000, size=100)
        })
        df.set_index('datetime', inplace=True)
        return df

broker = MockBroker()
bot = ScalpingStrategy(broker)
data = bot.fetch_and_calculate_indicators()
print("Returned indicators:")
for k, v in data.items():
    print(f"{k}: {v}")
