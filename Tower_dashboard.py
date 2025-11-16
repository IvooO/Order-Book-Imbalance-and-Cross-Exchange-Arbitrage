import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client
import random
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# 1. BINANCE CONFIG
# -------------------------
BINANCE_API_KEY = "YOUR_API_KEY"
BINANCE_API_SECRET = "YOUR_API_SECRET"
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

SYMBOL = "BTCUSDT"
ORDER_BOOK_LIMIT = 5
MAX_SIGNALS = 10

# -------------------------
# 2. HELPER FUNCTIONS
# -------------------------
def get_live_order_book(symbol: str, limit: int = 5):
    ob = client.get_order_book(symbol=symbol, limit=limit)
    bids = pd.DataFrame(ob['bids'], columns=['price', 'quantity']).astype(float)
    asks = pd.DataFrame(ob['asks'], columns=['price', 'quantity']).astype(float)
    return bids, asks

def calculate_obi(bids, asks):
    return bids['quantity'].sum() / asks['quantity'].sum() if asks['quantity'].sum() != 0 else np.inf

def generate_obi_signal(obi, threshold):
    if obi > threshold:
        return "BUY", f"OBI {obi:.2f} > {threshold} → Buyer pressure", 1.0
    elif obi < 1/threshold:
        return "SELL", f"OBI {obi:.2f} < {1/threshold:.2f} → Seller pressure", 1.0
    else:
        return "NEUTRAL", f"OBI {obi:.2f} balanced → Market Making", 0.5

def simulate_arbitrage(price_a, spread_threshold):
    price_b = price_a * (1 + random.uniform(-0.01,0.01)/100)
    spread_pct = (price_b - price_a)/price_a
    if spread_pct >= spread_threshold:
        return "ARB A→B", f"BUY @ ${price_a:.2f} | SELL @ ${price_b:.2f}", spread_pct
    elif spread_pct <= -spread_threshold:
        return "ARB B→A", f"BUY @ ${price_b:.2f} | SELL @ ${price_a:.2f}", spread_pct
    else:
        return "NO EDGE", "No profitable arbitrage", spread_pct

def calculate_position_size(confidence, max_usd, price):
    factor = (confidence - 0.5)/0.5 if confidence >= 0.5 else 0
    usd_allocation = factor * max_usd
    return usd_allocation/price if price != 0 else 0

def create_depth_chart(bids, asks):
    bids = bids.sort_values("price")
    asks = asks.sort_values("price")
    bids["cumsum"] = bids["quantity"].cumsum()
    asks["cumsum"] = asks["quantity"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bids['price'], y=bids['cumsum'], fill='tozeroy', mode='lines', name='Bids', line_color="#00c7a5"))
    fig.add_trace(go.Scatter(x=asks['price'], y=asks['cumsum'], fill='tozeroy', mode='lines', name='Asks', line_color="#ff4c4c"))
    fig.update_layout(title="Market Depth", xaxis_title="Price (USD)", yaxis_title="Cumulative Quantity (BTC)")
    return fig

# -------------------------
# 3. SESSION STATE INIT
# -------------------------
if "signal_history" not in st.session_state:
    st.session_state.signal_history = []
if "obi_history" not in st.session_state:
    st.session_state.obi_history = []

# -------------------------
# 4. STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Institutional BTC Dashboard", layout="wide")
st.title("Institutional  BTC Quant Dashboard")

# Tabs
tab_dashboard, tab_strategy = st.tabs([" Dashboard", " Strategy & Analytics"])

# Sidebar
st.sidebar.header("Settings")
obi_threshold = st.sidebar.slider("OBI Threshold", 1.05, 1.5, 1.1, 0.01)
arb_edge = st.sidebar.number_input("Minimum Arbitrage Edge (%)", 0.0001, 0.1, 0.005, format="%.4f")
max_position_usd = st.sidebar.number_input("Max Position (USD)", 1000, 500000, 50000, step=5000)

# -------------------------
# 5. DASHBOARD TAB
# -------------------------
with tab_dashboard:
    try:
        bids, asks = get_live_order_book(SYMBOL, ORDER_BOOK_LIMIT)
        current_price = float(bids['price'].iloc[0])
        obi = calculate_obi(bids, asks)

        # 15-min OBI
        now = datetime.now()
        st.session_state.obi_history.append({'timestamp': now, 'obi': obi})
        cutoff = now - timedelta(minutes=15)
        st.session_state.obi_history = [x for x in st.session_state.obi_history if x['timestamp'] > cutoff]
        avg_obi = np.mean([x['obi'] for x in st.session_state.obi_history]) if st.session_state.obi_history else obi

        # Signals
        signal_obi, reason_obi, confidence = generate_obi_signal(avg_obi, obi_threshold)
        position_btc = calculate_position_size(confidence, max_position_usd, current_price)
        arb_signal, arb_action, arb_spread = simulate_arbitrage(current_price, arb_edge/100)

        # Append signal history
        entry = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "OBI Signal": signal_obi,
            "OBI Avg": round(avg_obi,3),
            "Arb Signal": arb_signal,
            "Arb Spread %": round(arb_spread*100,4),
            "Position BTC": round(position_btc,4)
        }
        st.session_state.signal_history.append(entry)
        st.session_state.signal_history = st.session_state.signal_history[-MAX_SIGNALS:]

        # KPI Cards
        col1, col2, col3 = st.columns(3)
        color_obi = "#00c7a5" if signal_obi=="BUY" else ("#ff4c4c" if signal_obi=="SELL" else "#4c4cff")
        color_arb = "#00c7a5" if "ARB" in arb_signal else "#4c4cff"

        col1.markdown(f"""
            <div style="background:#ffffff;border-left:5px solid {color_obi};border-radius:8px;padding:15px;">
                <h4>OBI Signal</h4>
                <h2 style="color:{color_obi}">{signal_obi}</h2>
                <p>{reason_obi}</p>
                <p>15-min Avg OBI: {avg_obi:.3f}</p>
            </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
            <div style="background:#ffffff;border-left:5px solid {color_arb};border-radius:8px;padding:15px;">
                <h4>Arbitrage Signal</h4>
                <h2 style="color:{color_arb}">{arb_signal}</h2>
                <p>{arb_action}</p>
                <p>Spread: {arb_spread*100:.4f}%</p>
            </div>
        """, unsafe_allow_html=True)

        col3.metric("Recommended Position (BTC)", f"{position_btc:.4f}")

        # Signal history table
        st.subheader("Last 10 Signals")
        st.table(pd.DataFrame(st.session_state.signal_history).sort_values("timestamp", ascending=False))

        # Live Order Book
        st.subheader("Live Order Book")
        col_bids, col_asks = st.columns(2)
        col_bids.markdown(f"**BIDS ({bids['quantity'].sum():.4f} BTC)**")
        col_bids.dataframe(bids.style.format({"price":"${:,.2f}","quantity":"{:.4f}"}), use_container_width=True)
        col_asks.markdown(f"**ASKS ({asks['quantity'].sum():.4f} BTC)**")
        col_asks.dataframe(asks.style.format({"price":"${:,.2f}","quantity":"{:.4f}"}), use_container_width=True)

        st.markdown(f"*Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}*")

    except Exception as e:
        st.error(f"Error fetching live data: {e}")

# -------------------------
# 6. STRATEGY & ANALYTICS TAB
# -------------------------
with tab_strategy:
    st.header("Strategy & Analytics")

    # OBI Trend
    st.subheader("15-min OBI Trend")
    if st.session_state.obi_history:
        df_obi = pd.DataFrame(st.session_state.obi_history)
        fig_obi = px.line(df_obi, x="timestamp", y="obi", title="OBI Trend (15-min)")
        st.plotly_chart(fig_obi, use_container_width=True)

    # Market Depth
    st.subheader("Market Depth Chart")
    if 'bids' in locals() and 'asks' in locals():
        depth_chart = create_depth_chart(bids, asks)
        st.plotly_chart(depth_chart, use_container_width=True)

    # Arbitrage Spread History
    st.subheader("Arbitrage Spread History")
    df_signal = pd.DataFrame(st.session_state.signal_history)
    if not df_signal.empty:
        fig_arb = px.line(df_signal, x="timestamp", y="Arb Spread %", title="Arbitrage Spread (%) Over Last Signals")
        st.plotly_chart(fig_arb, use_container_width=True)

    # Position Size Analytics
    st.subheader("Position Size Analytics")
    if not df_signal.empty:
        fig_pos = px.bar(df_signal, x="timestamp", y="Position BTC", color="OBI Signal", title="Position Size BTC vs Signal")
        st.plotly_chart(fig_pos, use_container_width=True)
