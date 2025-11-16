# Order-Book-Imbalance-and-Cross-Exchange-Arbitrage
Dashboard for quantitative trading
# BTC Quant Dashboard (15-Minute Smoothed OBI + Arbitrage)

A **real-time cryptocurrency trading dashboard** built with Streamlit. This project provides systematic trading signals using:

- **Order Book Imbalance (OBI)** smoothed over 15 minutes
- **Cross-exchange arbitrage signals**
- **Live order book tables**  
- **Tunable strategy parameters in the sidebar**

---

## Features

1. **15-Minute Smoothed OBI Signal**
   - Calculates the ratio of total bid liquidity to total ask liquidity.
   - Smoothed over a rolling 15-minute window to avoid signal noise.
   - Provides actionable **BUY / SELL / NEUTRAL** signals.

2. **Cross-Exchange Arbitrage**
   - Simulates arbitrage opportunities between Binance and another exchange (currently `MockEx`).
   - Shows which exchange to buy from and which to sell to.
   - Highlights arbitrage edge in percentage terms.

3. **Live Order Book**
   - Displays Binance order book in real time.
   - Side-by-side tables for bids and asks.

4. **Tunable Parameters**
   - **OBI Threshold** – adjust the aggressiveness of BUY/SELL signals.
   - **Arbitrage Edge (%)** – minimum percentage difference required to trigger an arbitrage signal.

5. **Real-Time Updates**
   - The dashboard auto-refreshes every 15 seconds for near-live data updates.

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/btc-quant-dashboard.git
cd btc-quant-dashboard

