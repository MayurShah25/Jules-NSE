1. **Analyze the Issue:**
   - The user successfully bypassed the IP ban! But now Zerodha is rejecting the order because it is a `MARKET` order without market protection.
   - Zerodha explicitly bans sending raw `MARKET` orders for NSE options via the API due to liquidity and flash-crash risks.
   - We must send a `LIMIT` order instead. However, since the bot is a fast-paced scalper, we want it to execute immediately like a market order.
   - **Solution:** We need to fetch the `LTP` (Last Traded Price) right before placing the order, calculate a slight buffer (e.g., 2% above LTP for Buy, 2% below LTP for Sell) to ensure it fills instantly, and send it as a `LIMIT` order.

2. **Update the `BrokerAPI`:**
   - In both `options_scalping_bot.py` and `banknifty_scalping_bot.py`, modify the `place_order` method.
   - If `order_type == "MARKET"`, instead of sending `ORDER_TYPE_MARKET`, fetch the `ltp`, add a small buffer (e.g., +2% for Buy, -2% for Sell to act like an aggressive limit order), and send it as `ORDER_TYPE_LIMIT` with `price=calculated_price`.

3. **Verify:**
   - Ensure the new logic rounds the price to the nearest tick size (0.05 for NSE) so the exchange doesn't reject the price format.
