import streamlit as st
import yfinance as ticker_data
import pandas as pd

st.set_page_config(page_title="SAHAM-QUANT-MAP", layout="wide")

st.title("📊 SAHAM-QUANT-MAP: Peta Rekomendasi & Trading Plan")
st.caption("Sistem Analisis Kuantitatif Presisi (Model Saham Akademi)")

# Sidebar Filter
st.sidebar.header("Filter Parameter")
min_val = st.sidebar.number_input("Minimum Value (IDR)", value=5000000000, step=1000000000)

tickers = ["PANI.JK", "BUMI.JK", "ENRG.JK", "RAJA.JK", "DEWA.JK", "TMPO.JK", "BBRI.JK", "TLKM.JK"]

def analyze_stock(symbol):
    try:
        df = ticker_data.download(symbol, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 50: return None
        
        last_price = float(df['Close'].iloc[-1])
        volume_today = float(df['Volume'].iloc[-1])
        val_today = last_price * volume_today
        
        # 1. Filter Min Value
        if val_today < min_val: return None
        
        # 2. Hitung Modus Price (37 Hari)
        recent_prices = df['Close'].tail(37).round()
        modus_price = float(recent_prices.mode().iloc[0]) if not recent_prices.empty else last_price
        
        # 3. Filter Trend (SMA 20)
        sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        trend = "UPTREND" if last_price > sma20 else "DOWNTREND"
        
        # 4. Deteksi CH10 & Max Break (200 Hari / High Historis)
        high_200 = float(df['High'].tail(200).max())
        close_to_high = ((high_200 - last_price) / last_price) * 100
        is_max_break = "YES" if last_price >= high_200 else "NO"
        
        # Penilaian 4 Syarat (Kandidat Valid jika UPTREND & Min Value Terpenuhi)
        status_kandidat = "✅ VALID OPEN TRADE" if trend == "UPTREND" else "❌ SKIP (DOWNTREND)"
        
        return {
            "Stock": symbol.replace(".JK", ""),
            "Close to High (%)": f"{close_to_high:.2f}%",
            "Max Break": is_max_break,
            "Trend": trend,
            "Last Price": int(last_price),
            "Modus Price (37D)": int(modus_price),
            "Status Kandidat": status_kandidat
        }
    except Exception as e:
        return None

if st.button("🚀 Tampilkan Peta Rekomendasi (4 Syarat)"):
    with st.spinner("Memproses Data Kuantitatif BEI..."):
        results = [data for t in tickers if (data := analyze_stock(t)) is not None]
        if results:
            res_df = pd.DataFrame(results)
            st.subheader(f"RECOMMENDATION MAP (Min Value > Rp {min_val:,.0f})")
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("Tidak ada saham yang memenuhi kriteria minimum value.")
