import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & STREAMLIT UI (RESPONSIF HP & LAPTOP)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SAHAM-QUANT-SUITE (All-in-One)",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SAHAM-QUANT-SUITE: All-in-One Quantitative Radar & ATR Risk")
st.caption("3-in-1 Quantitative Trading System (Trend Breakout, Mean Reversion, RVOL+VWAP) | Licensed to **Rommy Sanjaya**")

# -----------------------------------------------------------------------------
# 2. DAFTAR TICKER UNIVERSE GABUNGAN (TOP 10 + LQ45 + TOP 100 IDX)
# -----------------------------------------------------------------------------
TICKERS_GABUNGAN = list(set([
    # Top Market Cap & LQ45 Utama
    "BBCA", "BBRI", "BMRI", "TLKM", "ASII", "TPIA", "BREN", "AMMN", "ICBP", "BYAN",
    "ACES", "ADRO", "AKRA", "AMRT", "ANTM", "ARTO", "BBNI", "BBTN", "BRIS", "BRPT",
    "BUKA", "CPIN", "EMTK", "ESSA", "EXCL", "GOTO", "HRUM", "INKP", "INDF", "INTP",
    "ITMG", "KLBF", "MDKA", "MEDC", "MIKA", "MNCN", "PGAS", "PTBA", "PANI", "SIDO",
    "SMGR", "SRTG", "TBIG", "TOWR", "UNVR", "UNTR", "MBMA", "CUAN",
    # Tambahan Top 100 IDX Likuid
    "AUTO", "BDMN", "BNGA", "BNLI", "BSDE", "CTRA", "DOID", "ELSA", "ENRG", "ERAA",
    "HEAL", "IMAS", "INDY", "JPFA", "JRPT", "KAEF", "KPIG", "LPKR", "MAIN", "MAPA",
    "MAPI", "MYOR", "PWON", "ROTI", "SMRA", "SMSM", "SSMS", "TAPG", "TKIM", "WIFI"
]))

# -----------------------------------------------------------------------------
# 3. SIDEBAR GLOBAL: MODAL, ATR RISK MANAGEMENT & FILTER LIKUIDITAS
# -----------------------------------------------------------------------------
st.sidebar.header("💼 Pengaturan Modal & ATR Risk")
modal_trading = st.sidebar.number_input(
    "Total Modal Trading (IDR)", 
    min_value=100_000, 
    value=2_000_000, 
    step=500_000,
    help="Ubah ke 10.000.000 setelah tahap uji coba Rp 2.000.000 selesai."
)
risk_per_trade_pct = st.sidebar.number_input(
    "Maksimal Risiko per Trade (%)", 
    min_value=0.5, 
    max_value=5.0, 
    value=1.5, 
    step=0.5,
    help="Batas kerugian maksimal jika terkena Stop Loss (1.5% dari Rp 2 Juta = Rp 30.000)."
)
min_val = st.sidebar.number_input(
    "Minimum Daily Value (IDR)", 
    value=1_000_000_000, 
    step=500_000_000
)

max_risk_idr = modal_trading * (risk_per_trade_pct / 100.0)
st.sidebar.info(f"🛡️ Batas Rugi Maksimal / Trade:\n**Rp {max_risk_idr:,.0f}**")

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Kalibrasi Parameter Strategi")

with st.sidebar.expander("1️⃣ Setting Quant-Map (Breakout)", expanded=False):
    min_freq_map = st.slider("Min Frekuensi Lonjakan >10% (200D)", 0, 10, 1, key="map_freq")
    map_sl_mult = st.number_input("SL Pengali ATR (Map)", 0.5, 3.0, 1.5, 0.1, key="map_sl")
    map_tp_mult = st.number_input("TP Pengali ATR (Map)", 1.0, 6.0, 3.0, 0.5, key="map_tp")

with st.sidebar.expander("2️⃣ Setting Quant-Reversion (Oversold)", expanded=False):
    rsi_limit_rev = st.slider("Batas Maksimal RSI-2", 5, 30, 15, 1, key="rev_rsi")
    rev_sl_mult = st.number_input("SL Pengali ATR (Reversion)", 0.5, 3.0, 1.2, 0.1, key="rev_sl")
    rev_tp_mult = st.number_input("TP Pengali ATR (Reversion)", 1.0, 5.0, 2.4, 0.2, key="rev_tp")

with st.sidebar.expander("3️⃣ Setting Quant-Intraday (RVOL+VWAP)", expanded=False):
    rvol_limit_intra = st.slider("Minimum RVOL (x)", 1.0, 5.0, 1.5, 0.1, key="intra_rvol")
    intra_sl_mult = st.number_input("SL Pengali ATR (Intraday)", 0.3, 2.0, 0.8, 0.1, key="intra_sl")
    intra_safe_mult = st.number_input("Profit Aman Pengali ATR", 0.5, 3.0, 1.0, 0.1, key="intra_safe")
    intra_tp_mult = st.number_input("TP Max Pengali ATR (Intraday)", 1.0, 4.0, 1.8, 0.2, key="intra_tp")

# -----------------------------------------------------------------------------
# 4. FUNGSI INDIKATOR TEKNIKAL & MESIN PEMINDAI TERPADU (1x TARIK DATA)
# -----------------------------------------------------------------------------
def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def calculate_rsi(series, period=2):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_position_sizing(entry_price, atr_val, sl_mult, tp_mult, modal, max_risk, safe_mult=None):
    sl_price = max(1, int(round(entry_price - (atr_val * sl_mult))))
    tp_price = int(round(entry_price + (atr_val * tp_mult)))
    safe_price = int(round(entry_price + (atr_val * safe_mult))) if safe_mult else None
    
    risk_per_lot = max(1, entry_price - sl_price) * 100
    cost_per_lot = entry_price * 100
    
    rec_lot = min(int(max_risk // risk_per_lot), int(modal // cost_per_lot))
    est_modal = int(rec_lot * cost_per_lot)
    lot_label = f"{rec_lot} Lot" if rec_lot > 0 else "0 (Modal/Risiko)"
    
    return sl_price, tp_price, safe_price, lot_label, est_modal

def run_unified_scanner(ticker_list):
    res_map, res_rev, res_intra = [], [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        status_text.text(f"Memindai 3 Strategi & ATR [{idx+1}/{total_tickers}]: {ticker}.JK ...")
        progress_bar.progress((idx + 1) / total_tickers)
        
        try:
            df = yf.download(f"{ticker}.JK", period="1y", interval="1d", progress=False)
            if len(df) < 200:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # Indikator Umum
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['ATR14'] = calculate_atr(df, period=14)
            df['Avg_Vol20'] = df['Volume'].rolling(20).mean()
            
            # Indikator Quant-Map
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA50'] = df['Close'].rolling(50).mean()
            
            # Indikator Quant-Reversion
            df['RSI2'] = calculate_rsi(df['Close'], period=2)
            df['MA200'] = df['Close'].rolling(200).mean()
            df['Std20'] = df['Close'].rolling(20).std()
            df['Lower_BB'] = df['MA20'] - (2 * df['Std20'])
            
            # Indikator Quant-Intraday (RVOL + VWAP)
            df['RVOL'] = df['Volume'] / df['Avg_Vol20']
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP_5D'] = (df['Typical_Price'] * df['Volume']).rolling(5).sum() / df['Volume'].rolling(5).sum()
            
            today = df.iloc[-1]
            prev = df.iloc[-2]
            
            entry_price = float(today['Close'])
            atr_val = float(today['ATR14'])
            total_value = float(entry_price * today['Volume'])
            
            # Filter ketat: Abaikan saham papan FCA (< Rp 50) dan transaksi tipis (< min_val)
            if entry_price < 50 or total_value < min_val or np.isnan(atr_val):
                continue
                
            df_200 = df.tail(200).copy()
            
            # -----------------------------------------------------------------
            # A. LOGIKA 1: QUANT-MAP (TREND BREAKOUT)
            # -----------------------------------------------------------------
            m_c1 = today['Close'] > today['MA20']
            m_c2 = today['MA20'] >= today['MA50']
            m_c3 = today['Volume'] > today['Avg_Vol20']
            m_c4 = today['Close'] > prev['Close']
            m_score = sum([m_c1, m_c2, m_c3, m_c4])
            
            spike_idx = df_200[df_200['Pct_Change'] >= 10.0].index
            freq_spike = len(spike_idx)
            src_hits = sum(
                1 for sp in spike_idx 
                if df_200.index.get_loc(sp) < len(df_200) - 3 and 
                df_200.iloc[df_200.index.get_loc(sp)+1 : df_200.index.get_loc(sp)+4]['High'].max() >= df_200.iloc[df_200.index.get_loc(sp)]['Close'] * 1.03
            )
            src_hz = (src_hits / freq_spike * 100) if freq_spike > 0 else 0.0
            
            sl_m, tp_m, _, lot_m, modal_m = calc_position_sizing(entry_price, atr_val, map_sl_mult, map_tp_mult, modal_trading, max_risk_idr)
            
            res_map.append({
                "Ticker": ticker,
                "Harga Entry": int(entry_price),
                "Change (%)": round(float(today['Pct_Change']), 2),
                "ATR 14 (Rp)": int(round(atr_val)),
                "Skor": m_score,
                "Lolos 4/4": "YA" if m_score == 4 else "TIDAK",
                "SRC Hz (%)": f"{round(src_hz, 1)}%",
                "Tren": "Uptrend" if m_c2 else "Downtrend",
                "Rekomendasi Lot": lot_m,
                f"TP ATR ({map_tp_mult}x)": tp_m,
                f"SL ATR ({map_sl_mult}x)": sl_m,
                "Modal Terpakai (Rp)": modal_m,
                "Freq_Raw": freq_spike
            })
            
            # -----------------------------------------------------------------
            # B. LOGIKA 2: QUANT-REVERSION (OVERSOLD BOUNCE)
            # -----------------------------------------------------------------
            r_c1 = today['Close'] > today['MA200']
            r_c2 = today['RSI2'] <= rsi_limit_rev
            r_c3 = today['Close'] <= (today['Lower_BB'] * 1.01)
            r_c4 = today['Close'] >= prev['Low']
            r_score = sum([r_c1, r_c2, r_c3, r_c4])
            
            os_idx = df_200[df_200['RSI2'] <= rsi_limit_rev].index
            bounce_hits = sum(
                1 for os_i in os_idx 
                if df_200.index.get_loc(os_i) < len(df_200) - 2 and 
                max(df_200.iloc[df_200.index.get_loc(os_i)+1]['Close'], df_200.iloc[df_200.index.get_loc(os_i)+2]['Close']) > df_200.iloc[df_200.index.get_loc(os_i)]['Close']
            )
            win_rev = (bounce_hits / len(os_idx) * 100) if len(os_idx) > 0 else 0.0
            
            sl_r, tp_r, _, lot_r, modal_r = calc_position_sizing(entry_price, atr_val, rev_sl_mult, rev_tp_mult, modal_trading, max_risk_idr)
            
            res_rev.append({
                "Ticker": ticker,
                "Harga Entry": int(entry_price),
                "Change (%)": round(float(today['Pct_Change']), 2),
                "RSI-2": round(float(today['RSI2']), 1),
                "ATR 14 (Rp)": int(round(atr_val)),
                "Skor": r_score,
                "Lolos 4/4": "YA" if r_score == 4 else "TIDAK",
                "Win Rate (200D)": f"{round(win_rev, 1)}%",
                "Tren Utama": "Bullish (>MA200)" if r_c1 else "Bearish (<MA200)",
                "Rekomendasi Lot": lot_r,
                f"TP ATR ({rev_tp_mult}x)": tp_r,
                f"SL ATR ({rev_sl_mult}x)": sl_r,
                "Modal Terpakai (Rp)": modal_r
            })
            
            # -----------------------------------------------------------------
            # C. LOGIKA 3: QUANT-INTRADAY (RVOL + VWAP)
            # -----------------------------------------------------------------
            i_c1 = today['RVOL'] >= rvol_limit_intra
            i_c2 = today['Close'] >= today['Typical_Price']
            i_c3 = today['Close'] > today['VWAP_5D']
            i_c4 = today['Close'] > today['Open']
            i_score = sum([i_c1, i_c2, i_c3, i_c4])
            
            df_60 = df.tail(60).copy()
            rv_idx = df_60[(df_60['RVOL'] >= rvol_limit_intra) & (df_60['Close'] >= df_60['Typical_Price'])].index
            ft_hits = sum(
                1 for rv_i in rv_idx 
                if df_60.index.get_loc(rv_i) < len(df_60) - 1 and 
                df_60.iloc[df_60.index.get_loc(rv_i)+1]['High'] > df_60.iloc[df_60.index.get_loc(rv_i)]['Close']
            )
            win_intra = (ft_hits / len(rv_idx) * 100) if len(rv_idx) > 0 else 0.0
            
            sl_i, tp_i, safe_i, lot_i, modal_i = calc_position_sizing(entry_price, atr_val, intra_sl_mult, intra_tp_mult, modal_trading, max_risk_idr, intra_safe_mult)
            
            res_intra.append({
                "Ticker": ticker,
                "Harga Entry": int(entry_price),
                "Harga VWAP": int(round(today['Typical_Price'])),
                "RVOL (x)": round(float(today['RVOL']), 2),
                "ATR 14 (Rp)": int(round(atr_val)),
                "Skor": i_score,
                "Lolos 4/4": "YA" if i_score == 4 else "TIDAK",
                "Win Rate (60D)": f"{round(win_intra, 1)}%",
                "Rekomendasi Lot": lot_i,
                f"Profit Aman ({intra_safe_mult}x)": safe_i,
                f"TP Max ({intra_tp_mult}x)": tp_i,
                f"SL Ketat ({intra_sl_mult}x)": sl_i,
                "Modal Terpakai (Rp)": modal_i
            })
            
        except Exception:
            continue
            
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(res_map), pd.DataFrame(res_rev), pd.DataFrame(res_intra)

# -----------------------------------------------------------------------------
# 5. TOMBOL EKSEKUSI TUNGGAL & TAMPILAN 3 TAB TERPADU
# -----------------------------------------------------------------------------
if st.button("🚀 Jalankan Pemindaian All-in-One (3 Strategi Sekaligus)", use_container_width=True):
    hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    now_wib = datetime.now(timezone(timedelta(hours=7)))
    waktu_lengkap = f"{hari_indo[now_wib.weekday()]}, {now_wib.strftime('%d-%m-%Y %H:%M:%S')} WIB"
    
    st.info(f"Pemindaian Selesai | Modal: **Rp {modal_trading:,.0f}** | Batas Rugi/Trade: **Rp {max_risk_idr:,.0f}** | Waktu: **{waktu_lengkap}**")
    
    df_map, df_rev, df_intra = run_unified_scanner(TICKERS_GABUNGAN)
    
    if not df_map.empty:
        tab1, tab2, tab3 = st.tabs([
            "📈 1. QUANT-MAP (Breakout)", 
            "🔄 2. QUANT-REVERSION (Oversold)", 
            "⚡ 3. QUANT-INTRADAY (RVOL+VWAP)"
        ])
        
        # TAB 1: QUANT-MAP
        with tab1:
            df_m_perf = df_map[(df_map['Skor'] == 4) & (df_map['Freq_Raw'] >= min_freq_map)].copy()
            if not df_m_perf.empty:
                st.success(f"🎯 {len(df_m_perf)} Saham Lolos Sinyal Breakout 4/4:")
                df_m_perf['Skor'] = df_m_perf['Skor'].astype(str) + "/4"
                st.dataframe(df_m_perf.drop(columns=['Freq_Raw']), use_container_width=True)
            else:
                st.warning("⚠️ Belum ada sinyal Breakout 4/4 hari ini. Menampilkan Top 10 Fallback:")
                df_m_fb = df_map.sort_values(by=["Skor", "Change (%)"], ascending=[False, False]).head(10).drop(columns=['Freq_Raw'])
                df_m_fb['Skor'] = df_m_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_m_fb, use_container_width=True)
                
        # TAB 2: QUANT-REVERSION
        with tab2:
            df_r_perf = df_rev[df_rev['Skor'] == 4].sort_values(by="RSI-2", ascending=True).copy()
            if not df_r_perf.empty:
                st.success(f"🎯 {len(df_r_perf)} Saham Lolos Sinyal Pantulan Jenuh Jual 4/4:")
                df_r_perf['Skor'] = df_r_perf['Skor'].astype(str) + "/4"
                st.dataframe(df_r_perf, use_container_width=True)
            else:
                st.warning("⚠️ Belum ada sinyal Mean Reversion 4/4 hari ini. Menampilkan Top 10 Saham RSI-2 Terendah:")
                df_r_fb = df_rev.sort_values(by=["Skor", "RSI-2"], ascending=[False, True]).head(10)
                df_r_fb['Skor'] = df_r_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_r_fb, use_container_width=True)
                
        # TAB 3: QUANT-INTRADAY
        with tab3:
            df_i_perf = df_intra[df_intra['Skor'] == 4].sort_values(by="RVOL (x)", ascending=False).copy()
            if not df_i_perf.empty:
                st.success(f"🎯 {len(df_i_perf)} Saham Lolos Sinyal Momentum RVOL + VWAP 4/4:")
                df_i_perf['Skor'] = df_i_perf['Skor'].astype(str) + "/4"
                st.dataframe(df_i_perf, use_container_width=True)
            else:
                st.warning("⚠️ Belum ada sinyal RVOL + VWAP 4/4 hari ini. Menampilkan Top 10 RVOL Tertinggi:")
                df_i_fb = df_intra.sort_values(by=["Skor", "RVOL (x)"], ascending=[False, False]).head(10)
                df_i_fb['Skor'] = df_i_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_i_fb, use_container_width=True)
    else:
        st.error("Tidak ada saham yang memenuhi filter Minimum Daily Value.")

# -----------------------------------------------------------------------------
# FOOTER & LISENSI
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("<center><small>SAHAM-QUANT-SUITE ALL-IN-ONE | Developed for Rommy Sanjaya | Strictly Controlled ATR Quantitative System</small></center>", unsafe_allow_html=True)

            
