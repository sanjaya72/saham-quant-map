import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & STREAMLIT UI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SAHAM-QUANT-MAP",
    page_icon="📈",
    layout="wide"
)

st.title("📊 SAHAM-QUANT-MAP: Sistem Analisis Kuantitatif Presisi")
st.caption("Designed & Developed for Quantitative Trading | Licensed to **Rommy Sanjaya**")

# -----------------------------------------------------------------------------
# 2. SIDEBAR FILTER & PARAMETER
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Parameter Filter Kuantitatif")

# Filter Nominal Value
min_val = st.sidebar.number_input(
    "Minimum Daily Value (IDR)", 
    value=1_000_000_000, 
    step=500_000_000,
    help="Hanya menampilkan saham dengan transaksi harian di atas nominal ini."
)

# Filter Ambang Batas Kenaikan (CH %)
ch_threshold = st.sidebar.slider(
    "CH % Threshold (Momentum Spike)", 
    min_value=5.0, 
    max_value=15.0, 
    value=10.0,
    step=0.5
)

# Target Risk Management
target_tp = 0.06  # TP 6%
target_sl = 0.03  # SL 3%

# -----------------------------------------------------------------------------
# 3. DAFTAR TICKER TOP 100 IDX / LQ45 (DYNAMIC SCANNING)
# -----------------------------------------------------------------------------
TICKERS_BEI = [
    "ACES", "ADRO", "AKRA", "AMRT", "ANTM", "ARTO", "ASII", "BBCA", "BBNI", "BBRI",
    "BBTN", "BMRI", "BRIS", "BRPT", "BUKA", "CPIN", "EMTK", "ESSA", "EXCL", "GOTO",
    "HRUM", "ICBP", "INKP", "INDF", "INTP", "ITMG", "KLBF", "MDKA", "MEDC", "MIKA",
    "MNCN", "PGAS", "PTBA", "PANI", "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TLKM",
    "TOWR", "UNVR", "UNTR", "MNC_NO_REDUNDANT", "MBMA", "AMMN", "BREN", "CUAN"
]
# Clean up duplicate tickers
TICKERS_BEI = list(set([t for t in TICKERS_BEI if t != "MNC_NO_REDUNDANT"]))

# -----------------------------------------------------------------------------
# 4. FUNSI UTAMA SCANNER & ANALISIS HISTORIS 200 HARI
# -----------------------------------------------------------------------------
def analyze_quant_stocks(ticker_list, min_value, ch_limit):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        status_text.text(f"Memindai & Mengalkulasi [{idx+1}/{total_tickers}]: {ticker}.JK ...")
        progress_bar.progress((idx + 1) / total_tickers)
        
        try:
            # Download data 1 tahun (200+ hari bursa)
            df = yf.download(f"{ticker}.JK", period="1y", interval="1d", progress=False)
            
            if len(df) < 200:
                continue
                
            # Handle MultiIndex columns jika ada dari yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # Hitung Indikator Teknikal Dasar
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA50'] = df['Close'].rolling(50).mean()
            df['Avg_Vol20'] = df['Volume'].rolling(20).mean()
            
            # Data Hari Ini & Kemarin
            today = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Evaluasi 4 Syarat Teknikal Utama
            c1 = today['Close'] > today['MA20']
            c2 = today['MA20'] >= today['MA50']
            c3 = today['Volume'] > today['Avg_Vol20']
            c4 = today['Close'] > prev['Close']
            
            score_count = sum([c1, c2, c3, c4])
            
            # Kalkulasi Matrik Lanjut 200 Hari Bursa
            df_200 = df.tail(200).copy()
            ch_count = (df_200['Pct_Change'] >= ch_limit).sum()
            
            # Hitung SRC Hz (Success Rate Continuation)
            ch_indices = df_200[df_200['Pct_Change'] >= ch_limit].index
            success_count = 0
            
            for ch_idx in ch_indices:
                loc = df_200.index.get_loc(ch_idx)
                if loc < len(df_200) - 1:
                    if df_200.iloc[loc + 1]['Pct_Change'] > 0:
                        success_count += 1
                        
            src_hz = (success_count / ch_count * 100) if ch_count > 0 else 0.0
            
            # Perhitungan Finansial & Trading Plan
            entry_price = float(today['Close'])
            total_value = float(entry_price * today['Volume'])
            trend_direction = "Uptrend" if today['MA20'] > today['MA50'] else "Downtrend"
            
            # Filter Nominal Transaksi Minimal
            if total_value >= min_value:
                results.append({
                    "Ticker": ticker,
                    "Harga Entry": int(entry_price),
                    "Change Hari Ini (%)": round(float(today['Pct_Change']), 2),
                    "Syarat Lolos": score_count,
                    "Lolos 4/4": "YA" if score_count == 4 else "TIDAK",
                    "Frekuensi CH>10% (200D)": int(ch_count),
                    "SRC Hz (%)": f"{round(src_hz, 1)}%",
                    "Arah Tren": trend_direction,
                    "Target Profit (6%)": int(entry_price * (1 + target_tp)),
                    "Stop Loss (3%)": int(entry_price * (1 - target_sl)),
                    "Value (IDR)": int(total_value)
                })
        except Exception:
            continue
            
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

# -----------------------------------------------------------------------------
# 5. EKSEKUSI PEMINDAIAN & LOGIKA TAMPILAN DASHBOARD
# -----------------------------------------------------------------------------
if st.button("🚀 Jalankan Pemindaian Pasar Sekarang"):
    st.info(f"Memulai pemindaian data real-time BEI pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB...")
    
    df_result = analyze_quant_stocks(TICKERS_BEI, min_val, ch_threshold)
    
    if not df_result.empty:
        # Pisahkan Hasil 4/4 dan Fallback
        df_perfect = df_result[df_result['Syarat Lolos'] == 4].sort_values(by="Value (IDR)", ascending=False)
        
        if not df_perfect.empty:
            st.success(f"🎯 Ditemukan {len(df_perfect)} Saham Memenuhi Kriteria Sempurna (4/4):")
            
            # Format Tampilan Tabel Sempurna
            df_show = df_perfect.copy()
            df_show['Syarat Lolos'] = df_show['Syarat Lolos'].astype(str) + "/4"
            st.dataframe(df_show, use_container_width=True)
            
        else:
            st.warning("⚠️ Tidak ada ticker yang memenuhi kriteria 4/4 secara penuh hari ini.")
            st.markdown("### 📋 Fallback Logic: Ticker Terbaik Berdasarkan Skor Terbanyak & Momentum")
            
            # Fallback: Urutkan berdasarkan Skor terbanyak, SRC Hz, dan Value
            df_fallback = df_result.sort_values(
                by=["Syarat Lolos", "Value (IDR)"], 
                ascending=[False, False]
            ).head(10)
            
            df_fallback_show = df_fallback.copy()
            df_fallback_show['Syarat Lolos'] = df_fallback_show['Syarat Lolos'].astype(str) + "/4"
            st.dataframe(df_fallback_show, use_container_width=True)
            
    else:
        st.error("Tidak ada saham yang sesuai dengan kriteria Minimum Value yang Anda tetapkan. Coba turunkan nilainya di sidebar.")

# -----------------------------------------------------------------------------
# FOOTER & LISENSI
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("<center><small>SAHAM-QUANT-MAP DASHBOARD | Developed for Rommy Sanjaya | Strictly Controlled Quantitative Model</small></center>", unsafe_allow_html=True)
