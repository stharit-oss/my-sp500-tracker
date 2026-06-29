import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ตั้งค่าหน้าเว็บให้เป็นแบบ Wide และปรับธีมเบื้องต้น
st.set_page_config(layout="wide", page_title="AlphaTrack - Global Dashboard", page_icon="📈")

# ตกแต่งสไตล์ CSS เพิ่มเติมเพื่อให้ปุ่มและตารางดูโมเดิร์นขึ้น
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-weight: 800; color: #00FFCC; letter-spacing: -1px; }
    .stRadio i { color: #00FFCC; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; color: #00FFCC; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ AlphaTrack: Global Divergence Dashboard")
st.caption("ระบบสแกนสัญญาณเทคนิคและจัดอันดับหุ้นชั้นนำระดับโลกแบบ Real-time Simulation")
st.markdown("---")

# 1. ข้อมูลรายชื่อหุ้นระดับสากล
MARKET_DATA = {
    "🇺🇸 สหรัฐอเมริกา (S&P 500 / NASDAQ)": [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'AMD',
        'NFLX', 'QCOM', 'JPM', 'V', 'DIS', 'WMT', 'XOM', 'JNJ', 'PG', 'ORCL'
    ],
    "🇹🇭 ประเทศไทย (SET50 ตัวท็อป)": [
        'DELTA.BK', 'PTT.BK', 'AOT.BK', 'ADVANC.BK', 'BDMS.BK', 'CPALL.BK', 'GULF.BK', 
        'PTTEP.BK', 'KBANK.BK', 'SCB.BK', 'BBL.BK', 'SCC.BK', 'CPN.BK', 'TRUE.BK', 'MINT.BK'
    ]
}

@st.cache_data
def generate_premium_mock_data():
    all_data = {}
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(60)][::-1]
    np.random.seed(2026) # กำหนดปีปัจจุบันเป็น Seed
    
    for market, tickers in MARKET_DATA.items():
        for t in tickers:
            is_thai = t.endswith('.BK')
            start_price = np.random.uniform(30, 150) if is_thai else np.random.uniform(150, 600)
            returns = np.random.normal(0.0006, 0.018, 60)
            price_series = start_price * np.cumprod(1 + returns)
            
            # เจาะจงให้หุ้นบางตัวเกิดสัญญาณซื้อที่สวยงาม
            has_divergence = t in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK', 'ADVANC.BK']
            if has_divergence:
                rsi_series = np.linspace(23, 41, 60) + np.random.normal(0, 2, 60)
                price_series[-10:] = price_series[-10:] * 0.91 
            else:
                rsi_series = np.random.uniform(35, 78, 60)
                
            df = pd.DataFrame({
                'Close': price_series,
                'RSI_14': np.clip(rsi_series, 0, 100)
            }, index=dates)
            all_data[t] = df
    return all_data

all_stock_data = generate_premium_mock_data()

# 2. จัดวางแถบควบคุม (Sidebar ดีไซน์ใหม่)
with st.sidebar:
    st.image("https://img.icons8.com/nolan/64/bullish.png", width=60)
    st.header("🎛️ แผงควบคุมระบบ")
    selected_market = st.selectbox("เลือกตลาดหุ้นที่ต้องการวิเคราะห์", list(MARKET_DATA.keys()))
    st.markdown("---")
    filter_option = st.radio("คัดกรองสัญญาณเทคนิค", ["แสดงหุ้นทั้งหมด", "เฉพาะ Bullish Divergence 🔥"])
    st.markdown("---")
    st.info("💡 **Bullish Divergence** คือ สัญญาณที่ราคามีการทำจุดต่ำสุดใหม่ แต่ดัชนี RSI เริ่มยกฐานสูงขึ้น บ่งบอกถึงโอกาสในการกลับตัวเป็นขาขึ้น")

current_market_tickers = MARKET_DATA[selected_market]

# 3. ประมวลผลและคำนวณข้อมูลตาราง
screened_list = []
for ticker in current_market_tickers:
    if ticker in all_stock_data:
        df = all_stock_data[ticker]
        pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        pct_1w = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        has_div = ticker in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK', 'ADVANC.BK']
        display_ticker = ticker.replace('.BK', ' (TH)') if ticker.endswith('.BK') else ticker
        
        screened_list.append({
            'Ticker_Raw': ticker,
            'ชื่อย่อหุ้น': display_ticker,
            'ราคาล่าสุด': round(float(df['Close'].iloc[-1]), 2),
            'เปลี่ยนแปลง 1D': round(float(pct_1d), 2),
            'เปลี่ยนแปลง 1W': round(float(pct_1w), 2),
            'RSI (14)': round(float(df['RSI_14'].iloc[-1]), 2),
            'สัญญาณ': "🔥 ซื้อ (Divergence)" if has_div else "⏳ ปกติ"
        })

df_summary = pd.DataFrame(screened_list)
total_divergence = len(df_summary[df_summary['สัญญาณ'].str.contains("ซื้อ")])
top_gainer = df_summary.loc[df_summary['เปลี่ยนแปลง 1D'].idxmax()]

# 4. ส่วนแสดงผลการวิเคราะห์ระดับบน (Top Metrics)
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="📊 ตลาดที่เลือกเทรด", value=selected_market.split()[1], delta=f"{len(current_market_tickers)} หุ้นในระบบ")
with m_col2:
    st.metric(label="🔥 หุ้นที่เกิด Divergence ตอนนี้", value=f"{total_divergence} ตัว", delta="น่าจับตาเปิดสถานะซื้อ", delta_color="normal")
with m_col3:
    st.metric(label="🚀 หุ้นที่บวกแรงที่สุดในวัน (Top Gainer)", value=top_gainer['ชื่อย่อหุ้น'], delta=f"+{top_gainer['เปลี่ยนแปลง 1D']}%")

st.markdown("---")

# 5. การจัดการตารางและการกรองผลข้อมูล
if filter_option == "เฉพาะ Bullish Divergence 🔥":
    df_display = df_summary[df_summary['สัญญาณ'].str.contains("ซื้อ")]
else:
    df_display = df_summary.sort_values(by='เปลี่ยนแปลง 1D', ascending=False) # สวยขึ้นโดยเรียงจากตัวที่บวกแรงที่สุด

# ใช้การแสดงผลแถบซ้าย-ขวา (Layout)
layout_col1, layout_col2 = st.columns([4, 5])

with layout_col1:
    st.subheader("📋 รายการสรุปผลและอันดับหุ้น")
    
    if not df_display.empty:
        # ฟังก์ชันจัดสีตารางอัตโนมัติ (สไตล์พรีเมียม)
        def style_positive_negative(val):
            if isinstance(val, (int, float)):
                color = '#00FF66' if val > 0 else '#FF3366' if val < 0 else 'white'
                return f'color: {color}; font-weight: bold;'
            return ''
            
        styled_df = df_display.drop(columns=['Ticker_Raw']).style.map(style_positive_negative, subset=['เปลี่ยนแปลง 1D', 'เปลี่ยนแปลง 1W'])
        
        # แสดงผลตารางแบบโมเดิร์น
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # กล่องเลือกหุ้นดีไซน์กระชับ
        ticker_map = dict(zip(df_display['ชื่อย่อหุ้น'], df_display['Ticker_Raw']))
        selected_name = st.selectbox("🎯 เลือกหุ้นที่คุณสนใจ เพื่อเปิดหน้าจอกราฟวิเคราะห์ขั้นสูง:", list(ticker_map.keys()))
        target_ticker = ticker_map[selected_name]
    else:
        st.warning("ไม่มีหุ้นที่เกิดสัญญาณ Divergence ในตลาดนี้ ณ ขณะนี้")
        target_ticker = current_market_tickers[0]

with layout_col2:
    st.subheader(f"📊 หน้าจอวิเคราะห์กราฟเทคนิค: {target_ticker.replace('.BK','')}")
    
    if target_ticker in all_stock_data:
        df_plot = all_stock_data[target_ticker]
        
        # ใช้ระบบ Tabs ช่วยจัดกลุ่มกราฟให้ดูดีเหมือน Streaming Platform
        tab1, tab2 = st.tabs(["📉 กราฟราคาปัจจุบัน", "📈 ดัชนีโมเมนตัม RSI"])
        
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], mode='lines+markers', name='Price', line=dict(color='#00FFCC', width=2.5)))
            fig.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333'))
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], mode='lines', name='RSI', line=dict(color='#FFCC00', width=2)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#FF3366")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#00FF66")
            fig_rsi.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=10, b=10),
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  yaxis=dict(range=[10, 90], showgrid=True, gridcolor='#333333'), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_rsi, use_container_width=True)
