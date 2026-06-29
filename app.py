import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(layout="wide", page_title="AlphaTrack Pro - Dashboard", page_icon="📊")

# ตกแต่ง CSS
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    h1 { font-weight: 800; color: #00FFCC; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #00FFCC; }
    .stSelectbox label { color: #00FFCC; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ AlphaTrack Pro: Multi-Chart Analysis")
st.caption("Advanced Technical Dashboard - วิเคราะห์สัญญาณราคาและโมเมนตัม RSI ในหน้าจอเดียว")
st.markdown("---")

# 2. ข้อมูลรายชื่อหุ้น
MARKET_DATA = {
    "🇺🇸 US Market (S&P 500 / NASDAQ)": [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'AMD',
        'NFLX', 'QCOM', 'JPM', 'V', 'DIS', 'WMT', 'XOM', 'JNJ', 'PG', 'ORCL'
    ],
    "🇹🇭 Thai Market (SET50)": [
        'DELTA.BK', 'PTT.BK', 'AOT.BK', 'ADVANC.BK', 'BDMS.BK', 'CPALL.BK', 'GULF.BK', 
        'PTTEP.BK', 'KBANK.BK', 'SCB.BK', 'BBL.BK', 'SCC.BK', 'CPN.BK', 'TRUE.BK', 'MINT.BK'
    ]
}

@st.cache_data
def generate_data():
    all_data = {}
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(60)][::-1]
    np.random.seed(2026)
    for market, tickers in MARKET_DATA.items():
        for t in tickers:
            is_thai = t.endswith('.BK')
            start_price = np.random.uniform(30, 150) if is_thai else np.random.uniform(150, 600)
            returns = np.random.normal(0.0006, 0.018, 60)
            price_series = start_price * np.cumprod(1 + returns)
            
            # กำหนดสัญญาณ Divergence
            has_div = t in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK', 'ADVANC.BK']
            if has_div:
                rsi_series = np.linspace(23, 42, 60) + np.random.normal(0, 2, 60)
                price_series[-10:] = price_series[-10:] * 0.92 
            else:
                rsi_series = np.random.uniform(35, 75, 60)
                
            df = pd.DataFrame({'Close': price_series, 'RSI_14': np.clip(rsi_series, 0, 100)}, index=dates)
            all_data[t] = df
    return all_data

all_stock_data = generate_data()

# 3. Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_market = st.selectbox("Select Market", list(MARKET_DATA.keys()))
    filter_option = st.radio("Signal Filter", ["All Stocks", "Bullish Divergence 🔥"])
    st.markdown("---")
    st.success("กราฟเวอร์ชันใหม่จะแสดง **Price** และ **RSI** คู่กันเพื่อให้ง่ายต่อการดูสัญญาณการกลับตัว")

# 4. ประมวลผลข้อมูล
current_tickers = MARKET_DATA[selected_market]
screened_list = []
for ticker in current_tickers:
    df = all_stock_data[ticker]
    pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    has_div = ticker in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK', 'ADVANC.BK']
    display_name = ticker.replace('.BK', ' (TH)') if ticker.endswith('.BK') else ticker
    screened_list.append({
        'Ticker_Raw': ticker, 'Name': display_name, 'Price': round(df['Close'].iloc[-1], 2),
        'Change %': round(pct_1d, 2), 'RSI': round(df['RSI_14'].iloc[-1], 2),
        'Signal': "🔥 BUY" if has_div else "Wait"
    })

df_summary = pd.DataFrame(screened_list)
if filter_option == "Bullish Divergence 🔥":
    df_display = df_summary[df_summary['Signal'] == "🔥 BUY"]
else:
    df_display = df_summary.sort_values(by='Change %', ascending=False)

# 5. Dashboard Metrics
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Market", selected_market.split()[1])
col_m2.metric("Signals Found", f"{len(df_summary[df_summary['Signal'] == '🔥 BUY'])} Stocks")
col_m3.metric("Top Mover", df_summary.iloc[0]['Name'], f"{df_summary.iloc[0]['Change %']}%")

# 6. Main Layout
l_col, r_col = st.columns([4, 6])

with l_col:
    st.subheader("📋 Stock List")
    def color_picker(val):
        color = '#00FF66' if val > 0 else '#FF3366' if val < 0 else 'white'
        return f'color: {color}'
    
    st.dataframe(df_display.drop(columns=['Ticker_Raw']).style.map(color_picker, subset=['Change %']), 
                 use_container_width=True, hide_index=True)
    
    ticker_map = dict(zip(df_display['Name'], df_display['Ticker_Raw']))
    selected_stock = st.selectbox("🎯 เลือกหุ้นเพื่อดูกราฟ:", list(ticker_map.keys()))
    target_ticker = ticker_map[selected_stock]

with r_col:
    st.subheader(f"📊 Technical Analysis: {selected_stock}")
    
    df_plot = all_stock_data[target_ticker]
    
    # --- ส่วนสำคัญ: สร้าง Subplots 2 แถว ---
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1, # ระยะห่างระหว่างกราฟบนกับล่าง
        row_heights=[0.6, 0.4] # กราฟราคา 60% กราฟ RSI 40%
    )

    # 1. เพิ่มกราฟราคาในแถวที่ 1
    fig.add_trace(
        go.Scatter(x=df_plot.index, y=df_plot['Close'], name="Price", line=dict(color='#00FFCC', width=3)),
        row=1, col=1
    )

    # 2. เพิ่มกราฟ RSI ในแถวที่ 2
    fig.add_trace(
        go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], name="RSI", line=dict(color='#FFCC00', width=2)),
        row=2, col=1
    )

    # เพิ่มเส้นแนวรับแนวต้าน RSI (70, 30)
    fig.add_hline(y=70, line_dash="dash", line_color="#FF3366", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00FF66", row=2, col=1)

    # ปรับแต่งหน้าตา Dashboard
    fig.update_layout(
        template="plotly_dark",
        height=550,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # ปรับแต่งแกน Y ของ RSI
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[10, 90], row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)
