import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Global Stock Divergence Tracker")
st.title("📈 Global Bullish Divergence & Performance Tracker")
st.write("ระบบคัดกรองหุ้นระดับโลก (US & TH) ที่มีสัญญาณกลับตัว (Bullish Divergence) และจัดอันดับความน่าสนใจ")

# 1. จัดหมวดหมู่รายชื่อหุ้นตัวท็อปแต่ละตลาด (US S&P500/NASDAQ & Thai SET)
MARKET_DATA = {
    "🇺🇸 สหรัฐอเมริกา (S&P 500 & NASDAQ)": [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'AMD',
        'NFLX', 'QCOM', 'JPM', 'V', 'DIS', 'WMT', 'XOM', 'JNJ', 'PG', 'ORCL'
    ],
    "🇹🇭 ประเทศไทย (SET50 ตัวท็อป)": [
        'DELTA.BK', 'PTT.BK', 'AOT.BK', 'ADVANC.BK', 'BDMS.BK', 'CPALL.BK', 'GULF.BK', 
        'PTTEP.BK', 'KBANK.BK', 'SCB.BK', 'BBL.BK', 'SCC.BK', 'CPN.BK', 'TRUE.BK', 'MINT.BK'
    ]
}

# 2. ฟังก์ชันจำลองข้อมูลความเร็วสูงแยกตามตลาด
@st.cache_data
def generate_market_mock_data():
    all_data = {}
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(60)][::-1]
    
    np.random.seed(100) # ล็อคค่าสุ่ม
    
    # วนลูปสร้างข้อมูลหุ้นทุกตัวในทุกตลาด
    for market, tickers in MARKET_DATA.items():
        for t in tickers:
            # จำลองราคาหุ้นตามประเภทตลาด (หุ้นไทยหลักสิบบาท หุ้นนอกหลักร้อยเหรียญ)
            is_thai = t.endswith('.BK')
            start_price = np.random.uniform(30, 150) if is_thai else np.random.uniform(150, 600)
            
            returns = np.random.normal(0.0005, 0.015, 60)
            price_series = start_price * np.cumprod(1 + returns)
            
            # สุ่มสร้างสัญญาณ Divergence ให้บางตัว (เช่น TSLA, NVDA, DELTA.BK, KBANK.BK)
            has_divergence = t in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK']
            if has_divergence:
                rsi_series = np.linspace(24, 42, 60) + np.random.normal(0, 2.5, 60)
                price_series[-10:] = price_series[-10:] * 0.93 # ราคาย่อลง แต่ RSI ยกตัวขึ้น
            else:
                rsi_series = np.random.uniform(38, 75, 60)
                
            df = pd.DataFrame({
                'Close': price_series,
                'RSI_14': np.clip(rsi_series, 0, 100)
            }, index=dates)
            all_data[t] = df
            
    return all_data

# โหลดข้อมูลเข้าสู่ระบบ
all_stock_data = generate_market_mock_data()

# 3. ส่วนควบคุมบนหน้าเว็บ (Sidebar / Filter)
st.sidebar.header("🔍 ตัวกรองและเลือกตลาด")
selected_market = st.sidebar.selectbox("เลือกตลาดหุ้นที่ต้องการดู:", list(MARKET_DATA.keys()))
filter_option = st.sidebar.radio("ตัวกรองสัญญาณซื้อ:", ["แสดงทั้งหมด", "เฉพาะตัวที่เกิด Bullish Divergence 🔥"])

# คัดแยกรายชื่อหุ้นตามตลาดที่เลือก
current_market_tickers = MARKET_DATA[selected_market]

# 4. ประมวลผลสร้างตารางสรุปข้อมูล
screened_list = []
for ticker in current_market_tickers:
    if ticker in all_stock_data:
        df = all_stock_data[ticker]
        pct_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        pct_1w = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        
        # เช็คว่าตัวนี้ถูกตั้งค่าให้เกิด Divergence ไหม
        has_div = ticker in ['NVDA', 'TSLA', 'DELTA.BK', 'KBANK.BK']
        
        # ตกแต่งชื่อย่อหุ้นไทยให้ดูง่ายในตาราง
        display_ticker = ticker.replace('.BK', ' (TH)') if ticker.endswith('.BK') else ticker
        
        screened_list.append({
            'Ticker Original': ticker, # เก็บชื่อจริงไว้ดึงข้อมูลกราฟ
            'ชื่อหุ้น': display_ticker,
            'ราคาล่าสุด': round(float(df['Close'].iloc[-1]), 2),
            'เปลี่ยนแปลง 1 วัน (%)': round(float(pct_1d), 2),
            'เปลี่ยนแปลง 1 สัปดาห์ (%)': round(float(pct_1w), 2),
            'RSI (14)': round(float(df['RSI_14'].iloc[-1]), 2),
            'สถานะเทคนิค': "🔥 สัญญาณน่าซื้อ (Divergence)" if has_div else "ปกติ"
        })

df_summary = pd.DataFrame(screened_list)

# จัดการตัวกรองตามเงื่อนไขที่เลือกใน Sidebar
if filter_option == "เฉพาะตัวที่เกิด Bullish Divergence 🔥":
    df_display = df_summary[df_summary['สถานะเทคนิค'].str.contains("🔥")]
else:
    df_display = df_summary.sort_values(by='ชื่อหุ้น', ascending=True)

# 5. การแสดงผล Layout แบบ 2 ฝั่ง (ตาราง และ กราฟ)
col1, col2 = st.columns([4, 5])

with col1:
    st.subheader(f"📋 รายการหุ้นในตลาด {selected_market.split()[0]}")
    if not df_display.empty:
        # แสดงตารางข้อมูลแบบซ่อนอินเด็กซ์
        st.dataframe(df_display.drop(columns=['Ticker Original']), use_container_width=True, hide_index=True)
        # กล่องเลือกหุ้นเพื่อดูกราฟ (ผูกโยงกับหุ้นในตารางที่โชว์)
        ticker_map = dict(zip(df_display['ชื่อหุ้น'], df_display['Ticker Original']))
        selected_display_name = st.selectbox("เลือกหุ้นที่ต้องการเปิดกราฟเทคนิค:", list(ticker_map.keys()))
        target_ticker = ticker_map[selected_display_name]
    else:
        st.warning("⚠️ ไม่พบหุ้นที่ตรงตามเงื่อนไขตัวกรองในตลาดนี้ ณ ขณะนี้")
        target_ticker = current_market_tickers[0]

with col2:
    st.subheader(f"📊 กราฟเทคนิคแบบ Interactive: {target_ticker.replace('.BK', '')}")
    if target_ticker in all_stock_data:
        df_plot = all_stock_data[target_ticker]
        
        # พล็อตตัวกราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], mode='lines', name='ราคา', line=dict(color='#00FFCC', width=2)))
        fig.update_layout(title="กราฟราคาหุ้นย้อนหลัง", template="plotly_dark", height=240, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # พล็อตตัวกราฟ RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], mode='lines', name='RSI', line=dict(color='#FFCC00', width=1.5)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig_rsi.update_layout(title="ดัชนี RSI (14 วัน)", template="plotly_dark", height=180, yaxis=dict(range=[10, 90]), margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rsi, use_container_width=True)
