import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# Konfigurasi Halaman
st.set_page_config(
    page_title="SAHAM-QUANT-MAP", 
    page_icon="📈",
    layout="wide"
)

# Link Logo
LOGO_URL = "https://raw.githubusercontent.com/sanjaya72/saham-quant-map/main/logo.png"

# Header Utama dengan Logo & Waktu Real-Time (WIB)
wib = pytz.timezone('Asia/Jakarta')
waktu_sekarang = datetime.now(wib)
hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

hari_str = hari_list[waktu_sekarang.weekday()]
tanggal_str = f"{waktu_sekarang.day} {bulan_list[waktu_sekarang.month - 1]} {waktu_sekarang.year}"
jam_str = waktu_sekarang.strftime("%H:%M:%S")

# Menampilkan Logo & Judul Dashboard
col_logo, col_title = st.columns([1, 5])

with col_logo:
    try:
        st.image(LOGO_URL, width=110)
    except Exception:
        st.write("📈")

with col_title:
    st.title("SAHAM-QUANT-MAP")
    st.markdown("##### *Peta Rekomendasi & Automatic Trading Plan*")

# Sub-judul keterangan yang sudah direvisi
st.caption("Sistem Analisis Kuantitatif Presisi")
st.caption(f"📅 **Waktu Akses Dashboard:** {hari_str}, {tanggal_str} | 🕒 {jam_str} WIB")
st.divider()

# Sidebar Parameter
st.sidebar.header("Filter Parameter")
min_value_input = st.sidebar.number_input("Minimum Value (IDR)", value=0, step=100000000)

# Sidebar Watermark / Lisensi
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 **Rommy Sanjaya**\nAll Rights Reserved.")

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
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
                ma50 = float(df['Close'].rolling(50).mean().iloc[-1]) if len(df) >= 50 else ma20
                volume = float(df['Volume'].iloc[-1])
                avg_volume = float(df['Volume'].rolling(20).mean().iloc[-1])
                value = close * volume

                # Syarat Teknikal 4-Filter
                c1_uptrend = close > ma20
                c2_ma_cross = ma20 >= ma50
                c3_vol_spike = volume > avg_volume
                c4_positive_day = close > prev_close
                
                # Menghitung Skor Syarat (0-4)
                score = sum([c1_uptrend, c2_ma_cross, c3_vol_spike, c4_positive_day])

                # Kalkulasi Automatic Trading Plan (Risk Management)
                stop_loss = round(min(close * 0.97, ma20 * 0.98))
                target_profit = round(close * 1.06)

                data_list.append({
                    'Ticker': ticker.replace('.JK', ''),
                    'Harga Entry': round(close),
                    'MA20': round(ma20, 2),
                    'Stop Loss (SL)': stop_loss,
                    'Target Profit (TP)': target_profit,
                    'Value (IDR)': round(value),
                    'Syarat Lolos': f"{score}/4",
                    'Score_Num': score,
                    'Status 4-Syarat': (score == 4)
                })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# Tombol Eksekusi
if st.button("🚀 Tampilkan Peta Rekomendasi & Trading Plan"):
    with st.spinner("Mengambil data bursa & menghitung Trading Plan kuantitatif..."):
        df_result = fetch_stock_data()
        
        if not df_result.empty:
            # Filter berdasarkan Minimum Value dari sidebar
            df_filtered = df_result[df_result['Value (IDR)'] >= min_value_input]
            
            # Filter saham yang meloloskan SEMUA 4 syarat
            df_strict = df_filtered[df_filtered['Status 4-Syarat'] == True]

            cols_to_display = ['Ticker', 'Harga Entry', 'MA20', 'Stop Loss (SL)', 'Target Profit (TP)', 'Value (IDR)', 'Syarat Lolos']

            if not df_strict.empty:
                st.success(f"✅ Ditemukan {len(df_strict)} saham yang memenuhi SEMUA 4 SYARAT teknikal!")
                st.dataframe(df_strict[cols_to_display], use_container_width=True)
            else:
                # FALLBACK LOGIC: Tampilkan saham terbaik dengan syarat terbanyak
                st.warning("⚠️ Tidak ada saham yang memenuhi 4 syarat sekaligus hari ini.")
                st.info("💡 Menampilkan daftar saham potensial dengan skor terbanyak beserta Trading Plan:")
                
                df_fallback = df_filtered.sort_values(by=['Score_Num', 'Value (IDR)'], ascending=[False, False]).head(10)
                st.dataframe(df_fallback[cols_to_display], use_container_width=True)
        else:
            st.error("Gagal mengambil data dari bursa. Silakan coba beberapa saat lagi.")

# Footer & Professional Branding Lisensi Rommy Sanjaya
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns([1, 2, 1])

with col_f2:
    st.markdown(
        "<div style='text-align: center; color: #6c757d; font-size: 13px; line-height: 1.6;'>"
        "<b>SAHAM-QUANT-MAP DASHBOARD</b><br>"
        "Designed & Developed for Quantitative Equity Analysis<br>"
        "Licensed to <b>Rommy Sanjaya</b> | All Rights Reserved © 2026"
        "</div>", 
        unsafe_allow_html=True
    )
