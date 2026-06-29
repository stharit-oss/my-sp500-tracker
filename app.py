import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="US Stock Divergence Tracker")
st.title("📈 S&P 500 Bullish Divergence & Performance Tracker")
st.write("ระบบคัดกรองหุ้นสหรัฐฯ ที่มีสัญญาณกลับตัว (Bullish Divergence) และจัดอันดับตามเปอร์เซ็นต์การเปลี่ยนแปลง (เวอร์ชันจำลองข้อมูลความเร็วสูง)")

# 1. สร้างข้อมูลจำลอง (Mock Data) สำหรับหุ้นยอดนิยมเพื่อความเร็วและไม่โดนบล็อก
@st.cache_data
def generate_mock_data():
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'DIS', 'NFLX']
    data = {}
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(60)][::-1]
    
    np.random.seed(42) # ล็อคค่าสุ่มเพื่อให้ข้อมูลนิ่ง
    
    for t in tickers:
        # จำลองราคาหุ้น
        start_price = np.random.uniform(100, 500)
        returns = np.random.normal(0.001, 0.02, 60)
        price_series = start_price * np.cumprod(1 + returns)
        
        # จำลอง RSI ให้สอดคล้องกัน (และจงใจทำลายแนวโน้มบางตัวให้เกิด Divergence)
        if t in ['NVDA', 'TSLA', 'AAPL']: # กำหนดให้ 3 ตัวนี้เกิด Bullish Divergence แข็งๆ
            rsi_series = np.linspace(25, 45, 60) + np.random.normal(0, 3, 60)
            price_series[-10:] = price_series[-10:] * 0.92 # บังคับราคาลง แต่ RSI ยกสูงขึ้น
        else:
            rsi_series = np.random.uniform(40, 70, 60)
            
        df = pd.DataFrame({
            'Close': price_series,
            'RSI_14': np.clip(rsi_series, 0, 100)
        }, index=dates)
        data[t] = df
    return data

# โหลดข้อมูลด่วน
stock_data = generate_mock_data()

screened_list = []
for ticker, df in stock_data.items():
    pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    pct_1w = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
    
    # เงื่อนไขเช็ค Divergence จากข้อมูลที่จำลองไว้
    has_div = ticker in ['NVDA', 'TSLA', 'AAPL']
    
    screened_list.append({
        'Ticker': ticker,
        'Price': round(float(df['Close'].iloc[-1]), 2),
        '1D %': round(float(pct_1d), 2),
        '1W %': round(float(pct_1w), 2),
        'RSI(14)': round(float(df['RSI_14'].iloc[-1]), 2),
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
    selected_ticker = st.selectbox("เลือกหุ้นที่ต้องการดูกราฟเทคนิค:", df_display['Ticker'].tolist())

with col2:
    st.subheader(f"📊 กราฟเทคนิคแบบ Interactive: {selected_ticker}")
    if selected_ticker in stock_data:
        df_plot = stock_data[selected_ticker]
        
        # กราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], mode='lines', name='Price', line=dict(color='#00FFCC')))
        fig.update_layout(title=f"ราคาหุ้น {selected_ticker}", template="plotly_dark", height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # กราฟ RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], mode='lines', name='RSI', line=dict(color='#FFCC00')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title="RSI (14)", template="plotly_dark", height=180, yaxis=dict(range=[10, 90]), margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rsi, use_container_width=True)
