import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="US Stock Divergence Tracker")
st.title("📈 S&P 500 Bullish Divergence & Performance Tracker")
st.write("ระบบคัดกรองหุ้นสหรัฐฯ ที่มีสัญญาณกลับตัว (Bullish Divergence) และจัดอันดับตามเปอร์เซ็นต์การเปลี่ยนแปลง")

TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'V', 'JNJ', 'WMT', 'DIS', 'NFLX']

@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start_date, end=end_date, progress=False)
            if not df.empty:
                df.ta.rsi(close='Close', length=14, append=True)
                data[t] = df
        except:
            continue
    return data

def check_bullish_divergence(df):
    if len(df) < 30 or 'RSI_14' not in df.columns:
        return False
    recent = df.tail(20)
    latest_rsi = df['RSI_14'].iloc[-1]
    if latest_rsi < 35 and df['RSI_14'].iloc[-5] < latest_rsi:
        return True
    return False

with st.spinner('กำลังดึงข้อมูลหุ้นและคำนวณ Indicators...'):
    stock_data = get_stock_data(TICKERS)

screened_list = []
for ticker, df in stock_data.items():
    if df.empty: continue
    pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    pct_1w = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
    has_div = check_bullish_divergence(df)
    screened_list.append({
        'Ticker': ticker,
        'Price': round(df['Close'].iloc[-1], 2),
        '1D %': round(pct_1d, 2),
        '1W %': round(pct_1w, 2),
        'RSI(14)': round(df['RSI_14'].iloc[-1], 2),
        'Bullish Divergence': "🔥 น่าซื้อ (Divergence)" if has_div else "ปกติ"
    })

df_summary = pd.DataFrame(screened_list)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 รายการหุ้นที่คัดกรอง")
    filter_option = st.radio("ตัวกรองการแสดงผล:", ["ทั้งหมด", "เฉพาะตัวที่น่าซื้อ (Divergence)"])
    if filter_option == "เฉพาะตัวที่น่าซื้อ (Divergence)":
        df_display = df_summary[df_summary['Bullish Divergence'].str.contains("🔥")]
    else:
    df_display = df_summary.sort_values(by='Ticker', ascending=True)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    selected_ticker = st.selectbox("เลือกหุ้นที่ต้องการดูกราฟเทคนิค:", df_display['Ticker'].tolist() if not df_display.empty else TICKERS)

with col2:
    st.subheader(f"📊 กราฟเทคนิคแบบ Interactive: {selected_ticker}")
    if selected_ticker in stock_data:
        df_plot = stock_data[selected_ticker].tail(90)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], mode='lines', name='Price', line=dict(color='#00FFCC')))
        fig.update_layout(title=f"ราคาหุ้น {selected_ticker}", template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], mode='lines', name='RSI', line=dict(color='#FFCC00')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title="RSI (14)", template="plotly_dark", height=200, yaxis=dict(range=[10, 90]))
        st.plotly_chart(fig_rsi, use_container_width=True)
