# NSE & MCX Scalping Bot Strategy Architecture

This document outlines the detailed strategy architecture for the automated Options Buying Bots (NSE Nifty/BankNifty) and Commodities Futures Bots (MCX Crude Oil/Natural Gas).

## 1. Strategy Architecture Overview

The bots are high-frequency, 1-minute intraday scalpers. They utilize a highly dynamic **30-Minute Rolling Window** combined with advanced momentum filters to trigger trades only during statistically probable expansions.

### Entry Logic

1.  **Level Identification:** The bot dynamically calculates a `Rolling High` and `Rolling Low` based on the previous 30 candles (30 minutes).
2.  **Breakout Strategy:**
    *   **Bullish Breakout:** Current price breaks the 30-min Rolling High.
    *   **Bearish Breakdown:** Current price breaks the 30-min Rolling Low.
3.  **Mean-Reversion Strategy (Wick Rejections):**
    *   If a candle wicks outside the 30-min rolling level but closes back *inside* the range (in the direction of the macro trend), the bot buys the bounce.
4.  **Instrument Selection:**
    *   **NSE:** Strictly buys At-The-Money (ATM) strikes to maintain a healthy ~0.5 Delta and prevent excessive Theta decay.
    *   **MCX:** Directly trades the nearest-expiry front-month Futures contract.

### Exit & Dynamic Risk Management

The bots utilize two distinct risk management paradigms:

1. **NSE Options (Percentage-Based Dynamic Risk):**
   *   **Strong Trend Mode (ADX >= 30):** The bot recognizes a massive breakout is occurring. It widens the Stop Loss to **8%** to survive volatility, pushes the Take Profit target to **20%**, and uses a **5%** Trailing Take Profit (TTP) to let the winner run.
   *   **Moderate Trend Mode (ADX >= 20):** The bot recognizes standard momentum. It tightens the Stop Loss to **5%**, aims for a **10%** Take Profit target, and trails very tightly at **3%**.
   *   **Sideways/Chop Mode (ADX < 20):** The bot recognizes the market is ranging. It executes high-probability mean-reversion bounces off the 30-minute Rolling High/Low with ultra-tight constraints: **3% SL**, **6% Target**, and **2% Trailing**.

2. **MCX Mini Futures (Hard-Point Scalping):**
   * Commodities are traded using strict point-based scalping targets to overcome volatility and slippage.
   * **Crude Oil:** Target 15 Points, SL 8 Points, Trailing 5 Points.
   * **Natural Gas:** Target 2 Points, SL 1 Point, Trailing 0.5 Points.

*   **Step-Trailing & Break-Even Preservation:** On all trades, if the asset gains match the Stop Loss threshold (a 1:1 Risk/Reward), the Stop Loss is permanently moved to the Break-Even entry price (plus slippage buffer) to ensure a winning trade never turns red. The SL is then continuously "step-trailed" upwards behind the price action to incrementally lock in profit.

---

## 2. Advanced Momentum Filters (The "Chop Killer")

To prevent bleeding capital in sideways markets (whipsawing), the bot must pass a rigorous set of mathematical filters before any entry is approved.

*   **Timeframe:** 1-Minute Chart.
*   **Trend Filter (EMA 21):** Price must be above the 21 EMA to buy Calls, and below to buy Puts.
*   **RSI (14-Period):** Price must demonstrate true directional strength. RSI must be `> 50` for bullish trades and `< 50` for bearish trades (unless in Sideways Chop Mode, where RSI is reversed to catch oversold/overbought fading).
*   **Dual-Engine Logic:** If ADX > 20, the bot trades Momentum (Breakouts). If ADX < 20, the bot trades Mean Reversion (Supply & Demand bounces).
*   **Chop Killer (VWAP Expansion):** Buying breakouts directly on the VWAP line often results in immediate mean-reversion fakeouts. The bot requires the entry price to be at least `0.05%` away from the VWAP, ensuring we are buying true expansion momentum. (This is bypassed in the first 45 minutes of the market open to catch gap-down momentum).

---

## 3. Capital Protection Module

1.  **Strict MIS Auto-Square-Off:** Options buyers are crushed by overnight gaps and Theta decay. At exactly 3:15 PM (NSE) or 11:15 PM (MCX), the bots auto-cancel all pending orders and Market-Sell any open positions, keeping you 100% in cash overnight.
2.  **Daily Kill Switch (Max Loss Per Day):** The bot continuously monitors your overall MTM. If it hits the defined Daily Max Loss, it completely halts all trading for the rest of the day to prevent revenge trading.
3.  **Maximum Exposure Capping:** Even as capital compounds, the bot refuses to buy more than **10 Lots** per order to respect exchange freeze limits and prevent catastrophic single-trade exposure.