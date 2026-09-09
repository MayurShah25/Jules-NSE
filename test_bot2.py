from options_scalping_bot import ScalpingStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MockBroker:
    def __init__(self):
        self.connected = True
        self.call_count = 0

    def get_historical_data(self, symbol, timeframe):
        self.call_count += 1
        now = datetime.now()
        # Mock gap down
        dates = [now - timedelta(days=1, minutes=i) for i in range(100, 0, -1)]
        df1 = pd.DataFrame({
            'datetime': dates,
            'open': np.random.rand(100) * 100 + 10000,
            'high': np.random.rand(100) * 100 + 10100,
            'low': np.random.rand(100) * 100 + 9900,
            'close': np.random.rand(100) * 100 + 10000,
            'volume': np.random.randint(100, 1000, size=100)
        })

        # Today's data (gap down)
        dates2 = [now.replace(hour=9, minute=15) + timedelta(minutes=i) for i in range(self.call_count)]
        df2 = pd.DataFrame({
            'datetime': dates2,
            'open': np.random.rand(self.call_count) * 100 + 9000,
            'high': np.random.rand(self.call_count) * 100 + 9100,
            'low': np.random.rand(self.call_count) * 100 + 8900,
            'close': np.random.rand(self.call_count) * 100 + 9000,
            'volume': np.random.randint(100, 1000, size=self.call_count)
        })

        df = pd.concat([df1, df2])
        df.set_index('datetime', inplace=True)
        return df

broker = MockBroker()
bot = ScalpingStrategy(broker)

print("--- First Minute ---")
data1 = bot.fetch_and_calculate_indicators()
print(f"Rolling High: {data1['rolling_high']}, Rolling Low: {data1['rolling_low']}")

print("--- Second Minute ---")
data2 = bot.fetch_and_calculate_indicators()
print(f"Rolling High: {data2['rolling_high']}, Rolling Low: {data2['rolling_low']}")
