1. **Disable Paper Trading:**
   - In `options_scalping_bot.py` and `banknifty_scalping_bot.py`, set the global configuration parameter `PAPER_TRADING = False`.

2. **Verify Broker API Order Placement:**
   - Verify that the `place_order` and `exit_position` methods in the `BrokerAPI` class properly transmit real orders to the Zerodha Kite Connect API using `self.kite.place_order(...)` instead of mocking the orders, and that they handle the `PAPER_TRADING` flag correctly.

3. **Verify the Daily PNL calculation logic for real orders:**
   - Ensure the RiskManager accurately assesses PNL from the broker's real MTM (Mark To Market) and doesn't rely solely on the internally calculated PNL when in live execution mode. (Wait, in a previous step we intentionally changed this to *always* use the internally calculated PNL because it's faster and avoids desync. Let me check the code to see if that's safe for live).
