import datetime
import time
import ccxt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="AI Trading Signal Dashboard", page_icon="📈", layout="wide"
)

st.title("🚀 AI Trading Signal Dashboard")
st.markdown("Real-time Chart Scan & Buy/Sell Signals")

# Sidebar
st.sidebar.header("Control Panel")
symbol = st.sidebar.selectbox(
    "Select Coin", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
)
timeframe = st.sidebar.selectbox(
    "Select Timeframe", ["1m", "5m", "15m", "1h"], index=1
)


# Fetch Data and Calculate Indicators using Pure Pandas
def fetch_data(symbol, timeframe):
  try:
    exchange = ccxt.binance()
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(
        bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Manual RSI Calculation (14)
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Manual EMA Calculation (50)
    df["EMA_50"] = df["close"].ewm(span=50, adjust=False).mean()

    last = df.iloc[-1]
    price = last["close"]
    rsi = last["RSI"]
    ema50 = last["EMA_50"]

    signal = "NEUTRAL ⚖️"
    status = "info"
    if pd.notna(rsi) and pd.notna(ema50):
      if rsi < 35 and price > ema50:
        signal = "STRONG BUY 🟢"
        status = "success"
      elif rsi > 65 and price < ema50:
        signal = "STRONG SELL 🔴"
        status = "error"
      elif price > ema50:
        signal = "BUY (Uptrend) 🟢"
        status = "success"
      else:
        signal = "SELL (Downtrend) 🔴"
        status = "error"

    return df, price, rsi, ema50, signal, status
  except Exception as e:
    return None, 0, 0, 0, f"Error: {e}", "warning"


df, price, rsi, ema50, signal, status = fetch_data(symbol, timeframe)

if df is not None:
  # Metrics Cards
  col1, col2, col3 = st.columns(3)
  col1.metric("Current Price", f"${price:,.2f}")
  col2.metric("RSI (14)", f"{rsi:.1f}" if pd.notna(rsi) else "N/A")
  col3.metric("EMA (50)", f"${ema50:,.2f}" if pd.notna(ema50) else "N/A")

  # Alert Display
  if status == "success":
    st.success(f"**Signal Alert:** {signal} on {symbol}")
  elif status == "error":
    st.error(f"**Signal Alert:** {signal} on {symbol}")
  else:
    st.info(f"**Signal Alert:** {signal}")

  # Price Chart
  st.subheader("Price & EMA Trend Chart")
  st.line_chart(df.set_index("timestamp")[["close", "EMA_50"]])

  # Last Candle Data
  with st.expander("Recent Data"):
    st.dataframe(df.tail(10))
    
