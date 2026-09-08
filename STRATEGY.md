# Options Scalping Bot Strategy Architecture

This document outlines the detailed strategy architecture for the automated Options Buying Bot for NSE (Nifty/BankNifty).

## 1. Strategy Architecture Overview

The bot is a high-frequency, 1-minute intraday scalper. It completely abandons arbitrary "Daily" support and resistance levels, instead utilizing a highly dynamic **30-Minute Rolling Window** combined with advanced momentum filters to trigger trades only during statistically probable expansions.

### Entry Logic

1.  **Level Identification:** The bot dynamically calculates a `Rolling High` and `Rolling Low` based on the previous 30 candles (30 minutes).
2.  **Breakout Strategy:**
    *   **Bullish Breakout:** Current price breaks the 30-min Rolling High.
    *   **Bearish Breakdown:** Current price breaks the 30-min Rolling Low.
3.  **Mean-Reversion Strategy (Wick Rejections):**
    *   If a candle wicks outside the 30-min rolling level but closes back *inside* the range (in the direction of the macro trend), the bot buys the bounce.
4.  **Instrument Selection:**
    *   It strictly buys At-The-Money (ATM) strikes (rounded to the nearest 50 for Nifty) to maintain a healthy ~0.5 Delta and prevent excessive Theta decay.

### Exit & Dynamic Risk Management

The bot utilizes an AI-like Dynamic Risk Allocation system based on the `ADX` indicator at the exact time of entry:

*   **Strong Trend Mode (ADX >= 35):** The bot recognizes a massive breakout is occurring. It widens the Stop Loss to **8%** to survive volatility, pushes the Take Profit target to **30%**, and uses a **5%** Trailing Take Profit (TTP) to let the winner run.
*   **Moderate Trend Mode (ADX < 35):** The bot recognizes standard momentum. It tightens the Stop Loss to **5%**, aims for a **15%** Take Profit target, and trails very tightly at **3%**.
*   **Break-Even Preservation:** On all trades, if the option premium gains match the Stop Loss percentage (a 1:1 Risk/Reward), the Stop Loss is permanently moved to the Break-Even entry price to ensure a winning trade never turns red.

---

## 2. Advanced Momentum Filters (The "Chop Killer")

To prevent bleeding capital in sideways markets (whipsawing), the bot must pass a rigorous set of mathematical filters before any entry is approved.

*   **Timeframe:** 1-Minute Chart.
*   **Trend Filter (EMA 21):** Price must be above the 21 EMA to buy Calls, and below to buy Puts.
*   **RSI (14-Period):** Price must demonstrate true directional strength. RSI must be `> 50` for bullish trades and `< 50` for bearish trades.
*   **Chop Killer 1 (ADX > 25):** If ADX is below 25, the market is entirely sideways. The bot sits idle.
*   **Chop Killer 2 (VWAP Expansion):** Buying breakouts directly on the VWAP line often results in immediate mean-reversion fakeouts. The bot requires the entry price to be at least `0.05%` away from the VWAP, ensuring we are buying true expansion momentum.

---

## 3. Capital Protection Module

1.  **Strict 15:15 MIS Auto-Square-Off:** Options buyers are crushed by overnight gaps and Theta decay. At exactly 3:15 PM, the bot auto-cancels all pending orders and Market-Sells any open positions, keeping you 100% in cash overnight.
2.  **Daily Kill Switch (Max Loss Per Day):** The bot continuously monitors your overall MTM. If it hits the defined Daily Max Loss, it completely halts all trading for the rest of the day to prevent revenge trading.
3.  **Maximum Exposure Capping:** Even as capital compounds, the bot refuses to buy more than **10 Lots (500 units)** per order to respect exchange freeze limits and prevent catastrophic single-trade exposure.