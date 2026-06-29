import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="US Stock Divergence Tracker")
st.title("📈 S&P 500 Bullish Divergence & Performance Tracker")
st.write("ระบบคัดกรองหุ้นสหรัฐฯ ที่มีสัญญาณกลับตัว (Bullish Divergence) และจัดอันดับตามเปอร์เซ็นต์การเปลี่ยนแปลง")

# ลิสต์หุ้นยอดนิยมเพื่อความรวดเร็วในการโหลดหน้าเว็บ
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'DIS', 'NFLX']

def calculate_rsi(df, period=14):
    """คำนวณ RSI แบบความเร็วสูง"""
    close = df['Close']
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    ma_gain = gain.rolling(window=period).mean()
    ma_loss = loss.rolling(window=period).mean()
    
    # คำนวณในรูปแบบเซ็ตข้อมูลเพื่อความรวดเร็ว
    rs = ma_gain / ma_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@st.cache_data(ttl=600)  # ลดเวลาแคชลงเหลือ 10 นาทีเพื่อความสดใหม่ของข้อมูล
def get_stock_data(tickers):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100) # ดึงข้อมูลย้อนหลังแค่ 100 วันพอเพื่อความเร็ว
    data = {}
    
    for t in tickers:
        try:
            # ดึงข้อมูลผ่าน yfinance ticker object โดยตรงเพื่อป้องกันอาการค้าง
            ticker_obj = yf.Ticker(t)
            df = ticker_obj.history(start=start_date, end=end_date, raised=False)
            
            if not df.empty and len(df) > 20:
                df['RSI_14'] = calculate_rsi(df)
                data[t] = df
        except Exception as e:
            continue
    return data

def check_bullish_divergence(df):
    """เช็คสัญญาณ Divergence อย่างง่ายเพื่อไม่ให้หน่วงเครื่อง"""
    if len(df) < 20 or 'RSI_14' not in df.columns:
        return False
    
    # ดูข้อมูล 10 แท่งล่าสุด
    recent = df.tail(10)
    latest_rsi = df['RSI_14'].iloc[-1]
    
    # เงื่อนไข: ราคาปิดวันนี้ต่ำกว่า 5 วันก่อน แต่ RSI วันนี้กลับยกตัวสูงกว่า 5 วันก่อน ในโซนขายมากเกินไป (Oversold)
    if pd.notna(latest_rsi) and latest_rsi < 40:
        if df['Close'].iloc[-1] < df['Close'].iloc[-5] and latest_rsi > df['RSI_14'].iloc[-5]:
            return True
    return False

# โหลดข้อมูลหุ้น
with st.spinner('กำลังดึงข้อมูลและสแกนหุ้นความเร็วสูง...'):
    stock_data = get_stock_data(TICKERS)

screened_list = []
for ticker, df in stock_data.items():
    try:
        if df.empty or len(df) < 5: continue
        
        # คำนวณ % Change
        pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        pct_1w = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        has_div = check_bullish_divergence(df)
        
        screened_list.append({
            'Ticker': ticker,
            'Price': round(float(df['Close'].iloc[-1]), 2),
            '1D %': round(float(pct_1d), 2),
            '1W %': round(float(pct_1w), 2),
            'RSI(14)': round(float(df['RSI_14'].iloc[-1]), 2) if pd.notna(df['RSI_14'].iloc[-1]) else 50.0,
            'Bullish Divergence': "🔥 น่าซื้อ (Divergence)" if has_div else "ปกติ"
        })
    except:
        continue

if screened_list:
    df_summary = pd.DataFrame(screened_list)
else:
    # กรณีดึงข้อมูลไม่ได้เลย ให้ทำตารางเปล่าหลอกไว้ป้องกันเอเรอร์
    df_summary = pd.DataFrame(columns=['Ticker', 'Price', '1D %', '1W %', 'RSI(14)', 'Bullish Divergence'])

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 รายการหุ้นที่คัดกรอง")
    filter_option = st.radio("ตัวกรองการแสดงผล:", ["ทั้งหมด", "เฉพาะตัวที่น่าซื้อ (Divergence)"])
    
    if filter_option == "เฉพาะตัวที่น่าซื้อ (Divergence)":
        df_display = df_summary[df_summary['Bullish Divergence'].str.contains("🔥")]
    else:
        df_display = df_summary.sort_values(by='Ticker', ascending=True)
        
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    ticker_list = df_display['Ticker'].tolist() if not df_display.empty else TICKERS
    selected_ticker = st.selectbox("เลือกหุ้นที่ต้องการดูกราฟเทคนิค:", ticker_list)

with col2:
    st.subheader(f"📊 กราฟเทคนิคแบบ Interactive: {selected_ticker}")
    if selected_ticker in stock_data:
        df_plot = stock_data[selected_ticker].tail(60)
        
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
