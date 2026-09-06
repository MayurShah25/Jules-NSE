# Options Scalping Bot Strategy Architecture

This document outlines the detailed strategy architecture for the automated Options Buying Bot for NSE (Nifty/BankNifty).

## 1. Strategy Architecture Overview

The bot is designed to scalp options (buying CE and PE) based on key intraday levels, specifically the Day High and Day Low. It incorporates multiple filters to ensure a high probability of success and rigorous risk management to protect capital.

### Entry Logic

1.  **Level Identification:** The bot dynamically calculates the `Day High` and `Day Low` for the current trading session based on incoming tick/candle data.
2.  **Breakout Detection:**
    *   **Bullish:** If the current price crosses and closes above the `Day High`.
    *   **Bearish:** If the current price crosses and closes below the `Day Low`.
3.  **Instrument Selection:**
    *   Upon a bullish breakout, the bot selects the At-The-Money (ATM) Call Option (CE) strike.
    *   Upon a bearish breakdown, the bot selects the ATM Put Option (PE) strike.
    *   ATM strikes are chosen for a balance of delta and liquidity, preventing excessive theta decay common in OTM strikes.

### Exit Logic

1.  **Stop Loss (SL):** A strict percentage-based Stop Loss (e.g., 10% of the premium) is calculated and placed immediately upon entry.
2.  **Trailing Stop Loss (TSL):** As the trade moves in favor, the SL trails the price by a fixed percentage (e.g., 5%). This locks in profits during fast momentum moves (scalping).
3.  **Manual/Time Exit:** The bot will automatically exit any open positions if a manual interrupt occurs or if the trading day ends.

---

## 2. Filters & Indicator Setup

To prevent entering false breakouts and losing capital in choppy markets, the bot relies on specific technical indicators.

### Recommended Timeframe
*   **3-Minute Chart:** Ideal for scalping as it filters out the extreme noise of the 1-minute chart while still providing fast enough signals for intraday momentum.

### Trend Filter (Don't fight the trend)
*   **Indicators:** VWAP (Volume Weighted Average Price) and 50-period EMA (Exponential Moving Average).
*   **Logic:**
    *   **Long CE Filter:** Price *must* be above both VWAP and the 50 EMA. This confirms the intraday trend is bullish and supports the Day High breakout.
    *   **Long PE Filter:** Price *must* be below both VWAP and the 50 EMA. This confirms the intraday trend is bearish and supports the Day Low breakdown.

### Sideways Market Filter (Prevent Bleeding/Starvation)
*   **Indicator:** ADX (Average Directional Index) - 14-period.
*   **Logic:**
    *   ADX measures trend strength regardless of direction.
    *   If ADX < 20, the market is considered sideways or lacking momentum.
    *   The bot will pause and **not take any trades** as long as ADX remains below 20. Options buyers bleed capital to theta decay and whipsaws in these conditions.

---

## 3. Risk Management Module

Capital protection is the highest priority. The bot implements three layers of safety:

1.  **Strict System-Placed SL:** The moment an entry order is filled, the script calculates the SL price and should immediately send an SL-M (Stop Loss Market) order to the broker. This protects against sudden violent spikes in the opposite direction.
2.  **Trailing SL for Scalps:** In scalping, profits can vanish quickly. The bot continuously monitors the Last Traded Price (LTP) of the option and updates the Trailing SL. If the price moves up by 5%, the SL moves up by 5%, securing gains.
3.  **Daily Kill Switch (Max Loss Per Day):**
    *   The bot continuously monitors the daily realized/unrealized MTM (Mark-To-Market) PnL.
    *   A hard limit is set (e.g., -₹5000).
    *   If the daily loss exceeds this limit, the `kill_switch_active` flag is triggered.
    *   The bot will immediately close any open positions and halt all trading activity for the remainder of the day to prevent revenge trading or catastrophic losses.