1. **Fix Original Nifty Scripts:**
   - Modify `options_scalping_bot.py` and `backtest.py` back to their Nifty-only versions. I incorrectly left `SYMBOL = "BANKNIFTY"` and changed the lot sizing to variable dictionary lookups which broke them. I need to revert these to `SYMBOL = "NIFTY"`, restoring their pure structure.

2. **Enforce ₹50,000 Capital Limit on Live BankNifty Bot:**
   - In `banknifty_scalping_bot.py`, I will implement a hard limit on position sizing. Even if `self.broker.get_balance()` returns ₹1,000,000, the maximum allocation for the BankNifty bot will be strictly capped at ₹50,000 to fulfill the user's requirement.

3. **Verify BankNifty Logic:**
   - Ensure `banknifty_backtest.py` and `banknifty_scalping_bot.py` correctly target `BANKNIFTY`, `260105`, strike multiples of `100`, and lot sizes of `15`.

4. **Test and Verify:**
   - Ensure no regressions occur in Nifty scripts.
