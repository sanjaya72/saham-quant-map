import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Konfigurasi Halaman
st.set_page_config(page_title="SAHAM-QUANT-MAP", layout="wide")

st.title("📊 SAHAM-QUANT-MAP: Peta Rekomendasi & Trading Plan")
st.caption("Sistem Analisis Kuantitatif Presisi (Model Saham Akademi)")

# Sidebar Parameter
st.sidebar.header("Filter Parameter")
min_value_input = st.sidebar.number_input("Minimum Value (IDR)", value=0, step=100000000)

# Daftar Ticker Saham (Daftar Saham Likuid Indonesia / IHSG)
TICKERS = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'BBNI.JK', 'TLKM.JK', 
    'ASII.JK', 'UNTR.JK', 'AMRT.JK', 'ICBP.JK', 'INDF.JK',
    'CPIN.JK', 'ADRO.JK', 'PTBA.JK', 'PGAS.JK', 'MEDC.JK',
    'KLBF.JK', 'MDKA.JK', 'ANTM.JK', 'INCO.JK', 'BRIS.JK'
]

def fetch_stock_data():
    data_list = []
    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="60d")
            if len(df) >= 20:
                # Kalkulasi Indikator Teknikal
                close = df['Close'].iloc[-1]
                prev_close = df['Close'].iloc[-2]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
                volume = df['Volume'].iloc[-1]
                avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
                value = close * volume

                # Syarat Teknikal 4-Filter
                c1_uptrend = close > ma20
                c2_ma_cross = ma20 >= ma50
                c3_vol_spike = volume > avg_volume
                c4_positive_day = close > prev_close
                
                # Menghitung berapa syarat yang terpenuhi (0-4)
                score = sum([c1_uptrend, c2_ma_cross, c3_vol_spike, c4_positive_day])

                data_list.append({
                    'Ticker': ticker.replace('.JK', ''),
                    'Harga': close,
                    'MA20': round(ma20, 2),
                    'Value (IDR)': value,
                    'Syarat Lolos': score,
                    'Status 4-Syarat': (score == 4)
                })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# Tombol Eksekusi
if st.button("🚀 Tampilkan Peta Rekomendasi (4 Syarat)"):
    with st.spinner("Mengambil data bursa & menganalisis indikator kuantitatif..."):
        df_result = fetch_stock_data()
        
        if not df_result.empty:
            # Filter berdasarkan Minimum Value dari sidebar
            df_filtered = df_result[df_result['Value (IDR)'] >= min_value_input]
            
            # Filter saham yang meloloskan SEMUA 4 syarat
            df_strict = df_filtered[df_filtered['Status 4-Syarat'] == True]

            if not df_strict.empty:
                st.success(f"✅ Ditemukan {len(df_strict)} saham yang memenuhi SEMUA 4 SYARAT teknikal!")
                st.dataframe(df_strict[['Ticker', 'Harga', 'MA20', 'Value (IDR)', 'Syarat Lolos']], use_container_width=True)
            else:
                # FALLBACK LOGIC: Jika 0 saham meloloskan 4 syarat, tampilkan saham terbaik dengan skor tertinggi
                st.warning("⚠️ Tidak ada saham yang memenuhi 4 syarat sekaligus hari ini.")
                st.info("💡 Menampilkan daftar saham potensial yang memenuhi syarat terbanyak (3/4 syarat):")
                
                df_fallback = df_filtered.sort_values(by=['Syarat Lolos', 'Value (IDR)'], ascending=[False, False]).head(10)
                st.dataframe(df_fallback[['Ticker', 'Harga', 'MA20', 'Value (IDR)', 'Syarat Lolos']], use_container_width=True)
        else:
            st.error("Gagal mengambil data dari bursa. Silakan coba beberapa saat lagi.")
