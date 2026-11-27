import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os
import base64
import zlib
from datetime import datetime, timezone, timedelta

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & PROTEKSI TAMPILAN PENGEMBANG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SAHAM-QUANT-SUITE MASTER",
    page_icon="📈",
    layout="wide"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
    [data-testid="stToolbarActions"] {display: none !important;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LOGO SVG PROFESIONAL SAHAM-QUANT-SUITE
# -----------------------------------------------------------------------------
LOGO_SVG_HEADER = """
<div style="display: flex; align-items: center; gap: 16px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 16px 24px; border-radius: 12px; border-left: 6px solid #10b981; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 12px;">
    <svg width="54" height="54" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="64" height="64" rx="14" fill="#064e3b" fill-opacity="0.6" stroke="#10b981" stroke-width="2"/>
        <line x1="12" y1="48" x2="52" y2="48" stroke="#334155" stroke-width="1.5"/>
        <line x1="12" y1="32" x2="52" y2="32" stroke="#334155" stroke-width="1" stroke-dasharray="3 3"/>
        <line x1="12" y1="16" x2="52" y2="16" stroke="#334155" stroke-width="1" stroke-dasharray="3 3"/>
        <line x1="18" y1="34" x2="18" y2="46" stroke="#ef4444" stroke-width="2"/>
        <rect x="15" y="37" width="6" height="6" rx="1" fill="#ef4444"/>
        <line x1="28" y1="26" x2="28" y2="42" stroke="#10b981" stroke-width="2"/>
        <rect x="25" y="29" width="6" height="9" rx="1" fill="#10b981"/>
        <line x1="38" y1="20" x2="38" y2="36" stroke="#10b981" stroke-width="2"/>
        <rect x="35" y="23" width="6" height="10" rx="1" fill="#10b981"/>
        <line x1="48" y1="12" x2="48" y2="28" stroke="#34d399" stroke-width="2.5"/>
        <rect x="45" y="15" width="6" height="10" rx="1" fill="#34d399"/>
        <path d="M16 42 L28 31 L38 25 L49 13" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M43 13 H49 V19" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div>
        <div style="font-size: 22px; font-weight: 800; letter-spacing: 0.8px; color: #f8fafc; margin: 0;">
            SAHAM-QUANT-SUITE <span style="background-color: #10b981; color: #064e3b; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; vertical-align: middle; margin-left: 6px;">MASTER PRO</span>
        </div>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 3px;">
            Algorithmic IDX Scanner &bull; Pre-Breakout Resistance Filter &bull; Dynamic ATR Risk
        </div>
    </div>
</div>
"""

st.markdown(LOGO_SVG_HEADER, unsafe_allow_html=True)
st.caption("3-in-1 Quantitative Trading System + Persistent Virtual Lab | Direct Access Mode | Licensed to **Rommy Sanjaya**")

# -----------------------------------------------------------------------------
# 2. DAFTAR TICKER UNIVERSE GABUNGAN (BAKU - 78 EMITEN)
# -----------------------------------------------------------------------------
TICKERS_GABUNGAN = list(set([
    "BBCA", "BBRI", "BMRI", "TLKM", "ASII", "TPIA", "BREN", "AMMN", "ICBP", "BYAN",
    "ACES", "ADRO", "AKRA", "AMRT", "ANTM", "ARTO", "BBNI", "BBTN", "BRIS", "BRPT",
    "BUKA", "CPIN", "EMTK", "ESSA", "EXCL", "GOTO", "HRUM", "INKP", "INDF", "INTP",
    "ITMG", "KLBF", "MDKA", "MEDC", "MIKA", "MNCN", "PGAS", "PTBA", "PANI", "SIDO",
    "SMGR", "SRTG", "TBIG", "TOWR", "UNVR", "UNTR", "MBMA", "CUAN",
    "AUTO", "BDMN", "BNGA", "BNLI", "BSDE", "CTRA", "DOID", "ELSA", "ENRG", "ERAA",
    "HEAL", "IMAS", "INDY", "JPFA", "JRPT", "KAEF", "KPIG", "LPKR", "MAIN", "MAPA",
    "MAPI", "MYOR", "PWON", "ROTI", "SMRA", "SMSM", "SSMS", "TAPG", "TKIM", "WIFI"
]))

# -----------------------------------------------------------------------------
# 3. SIDEBAR: PENGATURAN MODAL (DEFAULT 10 JUTA), ATR RISK & STRATEGI (BAKU)
# -----------------------------------------------------------------------------
st.sidebar.header("💼 Pengaturan Modal & ATR Risk")
modal_trading = st.sidebar.number_input(
    "Total Modal Trading (IDR)", 
    min_value=100_000, 
    value=10_000_000, 
    step=500_000,
    help="Modal aktif default Rp 10.000.000."
)
risk_per_trade_pct = st.sidebar.number_input(
    "Maksimal Risiko per Trade (%)", 
    min_value=0.5, 
    max_value=5.0, 
    value=1.5, 
    step=0.5,
    help="Batas kerugian maksimal jika terkena Stop Loss (1.5% dari Rp 10 Juta = Rp 150.000)."
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

with st.sidebar.expander("3️⃣ Setting Quant-Intraday (Early Entry)", expanded=True):
    rvol_limit_intra = st.slider("Minimum RVOL Terkalibrasi (x)", 1.0, 5.0, 1.3, 0.1, key="intra_rvol")
    max_gain_intra = st.slider("Filter Anti-Pucuk: Max Naik Hari Ini (%)", 1.0, 8.0, 3.0, 0.5, key="intra_max_gain")
    intra_sl_mult = st.number_input("SL Ketat Pengali ATR", 0.3, 2.0, 0.6, 0.1, key="intra_sl")
    intra_safe_mult = st.number_input("Profit Aman Pengali ATR (Cepat)", 0.3, 2.5, 0.6, 0.1, key="intra_safe")
    intra_tp_mult = st.number_input("TP Max Pengali ATR", 0.8, 4.0, 1.5, 0.1, key="intra_tp")

# -----------------------------------------------------------------------------
# 4. MODUL GRAFIK CANDLESTICK MULTI-TIMEFRAME (M5, M15, 1H, DAILY, WEEKLY, MONTHLY)
# -----------------------------------------------------------------------------
TF_CONFIG = {
    "M5": {"period": "5d", "interval": "5m", "tail": 70, "fmt": "%d/%m %H:%M", "intraday": True},
    "M15": {"period": "5d", "interval": "15m", "tail": 65, "fmt": "%d/%m %H:%M", "intraday": True},
    "1H": {"period": "1mo", "interval": "60m", "tail": 65, "fmt": "%d/%m %H:%M", "intraday": True},
    "Daily": {"period": "6mo", "interval": "1d", "tail": 60, "fmt": "%d %b", "intraday": False},
    "Weekly": {"period": "2y", "interval": "1wk", "tail": 60, "fmt": "%d %b %y", "intraday": False},
    "Monthly": {"period": "5y", "interval": "1mo", "tail": 60, "fmt": "%b %Y", "intraday": False}
}

def tampilkan_grafik_candle(ticker, open_price, tp_price, sl_price, judul="Grafik Candle", default_tf="Daily", widget_key="tf_default"):
    tf_list = list(TF_CONFIG.keys())
    default_idx = tf_list.index(default_tf) if default_tf in tf_list else 3
    selected_tf = st.radio(
        f"⏱️ Timeframe ({ticker}.JK):",
        tf_list,
        index=default_idx,
        horizontal=True,
        key=widget_key
    )
    cfg = TF_CONFIG[selected_tf]
    
    try:
        df_g = yf.download(f"{ticker}.JK", period=cfg["period"], interval=cfg["interval"], progress=False)
        if isinstance(df_g.columns, pd.MultiIndex):
            df_g.columns = df_g.columns.get_level_values(0)
        df_g = df_g[df_g['Volume'] > 0].copy()
        if df_g.empty:
            st.warning(f"Data candle {selected_tf} untuk {ticker} belum tersedia.")
            return

        res_20d = None
        if not cfg["intraday"]:
            df_g['MA20'] = df_g['Close'].rolling(20).mean()
            df_g['MA50'] = df_g['Close'].rolling(50).mean()
            if selected_tf == "Daily" and len(df_g) >= 21:
                res_20d = float(df_g['High'].shift(1).rolling(20).max().iloc[-1])

        df_plot = df_g.tail(cfg["tail"])
        sumbu_x = df_plot.index.strftime(cfg["fmt"])

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=sumbu_x,
            open=df_plot['Open'],
            high=df_plot['High'],
            low=df_plot['Low'],
            close=df_plot['Close'],
            name=ticker,
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ))

        if not cfg["intraday"]:
            fig.add_trace(go.Scatter(x=sumbu_x, y=df_plot['MA20'], mode='lines', name='MA20', line=dict(color='#38bdf8', width=1.2)))
            fig.add_trace(go.Scatter(x=sumbu_x, y=df_plot['MA50'], mode='lines', name='MA50', line=dict(color='#f59e0b', width=1.2)))
            if res_20d and not np.isnan(res_20d):
                fig.add_hline(y=res_20d, line_dash="dot", line_color="#a855f7", line_width=1.4,
                              annotation_text=f"Res 20D: {int(round(res_20d)):,}", annotation_position="top left")

        # Garis TP, Open/Entry, dan SL
        fig.add_hline(y=tp_price, line_dash="dash", line_color="#10b981", line_width=2,
                      annotation_text=f"TP: Rp {tp_price:,}", annotation_position="top right")
        fig.add_hline(y=open_price, line_dash="solid", line_color="#3b82f6", line_width=2,
                      annotation_text=f"OPEN: Rp {open_price:,}", annotation_position="bottom right")
        fig.add_hline(y=sl_price, line_dash="dash", line_color="#ef4444", line_width=2,
                      annotation_text=f"SL: Rp {sl_price:,}", annotation_position="bottom left")

        y_min = min(float(df_plot['Low'].min()), sl_price) * 0.985
        y_max = max(float(df_plot['High'].max()), tp_price) * 1.015

        fig.update_layout(
            title=dict(text=f"📊 {judul}: {ticker}.JK [{selected_tf}]", font=dict(size=14)),
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=390,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis=dict(range=[y_min, y_max], side="right"),
            xaxis=dict(nticks=8),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 5. DATABASE PAPER TRADING PERMANEN (BAKU)
# -----------------------------------------------------------------------------
PAPER_FILE = "paper_trades_direct.json"

def encode_state_to_url(db_data):
    try:
        raw_bytes = json.dumps(db_data, separators=(",", ":")).encode("utf-8")
        compressed = zlib.compress(raw_bytes)
        b64_str = base64.urlsafe_b64encode(compressed).decode("utf-8")
        st.query_params["pf"] = b64_str
    except Exception:
        pass

def decode_state_from_url():
    try:
        if "pf" in st.query_params:
            b64_str = st.query_params["pf"]
            compressed = base64.urlsafe_b64decode(b64_str.encode("utf-8"))
            raw_bytes = zlib.decompress(compressed)
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, dict) and "cash" in data and "positions" in data:
                return data
    except Exception:
        pass
    return None

def load_paper_db():
    url_data = decode_state_from_url()
    if url_data is not None:
        st.session_state["paper_db_cache"] = url_data
        return url_data

    if "paper_db_cache" in st.session_state:
        encode_state_to_url(st.session_state["paper_db_cache"])
        return st.session_state["paper_db_cache"]

    if os.path.exists(PAPER_FILE):
        try:
            with open(PAPER_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "cash" in data:
                    st.session_state["paper_db_cache"] = data
                    encode_state_to_url(data)
                    return data
        except Exception:
            pass

    default_paper = {
        "initial_capital": int(modal_trading),
        "cash": int(modal_trading),
        "positions": [],
        "history": []
    }
    save_paper_db(default_paper)
    return default_paper

def save_paper_db(db_data):
    st.session_state["paper_db_cache"] = db_data
    encode_state_to_url(db_data)
    try:
        with open(PAPER_FILE, "w") as f:
            json.dump(db_data, f, indent=2)
    except Exception:
        pass

def execute_paper_buy(ticker, strategy_name, entry_price, lot_qty, tp_price, sl_price):
    u_data = load_paper_db()
    gross_cost = entry_price * lot_qty * 100
    buy_fee = int(round(gross_cost * 0.0015))
    total_debit = gross_cost + buy_fee
    
    if lot_qty <= 0:
        return False, "Jumlah lot 0 (modal atau batas risiko tidak mencukupi)."
    if total_debit > u_data["cash"]:
        return False, f"Saldo RDN Virtual tidak cukup (Butuh Rp {total_debit:,.0f}, Saldo Rp {u_data['cash']:,.0f})."
        
    now_wib = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M WIB")
    u_data["cash"] -= total_debit
    u_data["positions"].append({
        "id": f"{ticker}_{int(datetime.now().timestamp())}",
        "ticker": ticker,
        "strategy": strategy_name,
        "entry_time": now_wib,
        "entry_price": int(entry_price),
        "lot": int(lot_qty),
        "tp_price": int(tp_price),
        "sl_price": int(sl_price),
        "buy_cost": int(total_debit)
    })
    save_paper_db(u_data)
    return True, f"Order Virtual BUY {ticker} ({lot_qty} Lot @ Rp {entry_price:,}) berhasil dicatat!"

def execute_paper_sell(pos_index, exit_price, reason="Manual Close"):
    u_data = load_paper_db()
    pos = u_data["positions"].pop(pos_index)
    
    gross_proceeds = exit_price * pos["lot"] * 100
    sell_fee = int(round(gross_proceeds * 0.0025))
    net_proceeds = gross_proceeds - sell_fee
    net_pnl = net_proceeds - pos["buy_cost"]
    pnl_pct = round((net_pnl / pos["buy_cost"]) * 100, 2)
    
    now_wib = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M WIB")
    u_data["cash"] += net_proceeds
    u_data["history"].insert(0, {
        "Ticker": pos["ticker"],
        "Strategi": pos["strategy"],
        "Lot": pos["lot"],
        "Entry (Rp)": pos["entry_price"],
        "Exit (Rp)": int(exit_price),
        "Waktu Tutup": now_wib,
        "Keterangan": reason,
        "Net P/L (Rp)": int(net_pnl),
        "Net P/L (%)": f"+{pnl_pct}%" if pnl_pct > 0 else f"{pnl_pct}%"
    })
    save_paper_db(u_data)
    return net_pnl

# -----------------------------------------------------------------------------
# 6. FUNGSI INDIKATOR TEKNIKAL & MESIN PEMINDAI TERPADU (BAKU)
# -----------------------------------------------------------------------------
def get_intraday_time_factor(now_wib):
    if now_wib.weekday() >= 5:
        return 1.0
    total_mins = now_wib.hour * 60 + now_wib.minute
    open_mins = 9 * 60
    close_mins = 16 * 60
    
    if total_mins < open_mins or total_mins >= close_mins:
        return 1.0
    elapsed = max(20, total_mins - open_mins)
    if total_mins > 13 * 60 + 30:
        elapsed -= 90
    elif total_mins > 12 * 60:
        elapsed = 180
    return min(1.0, max(0.10, elapsed / 330.0))

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

def run_unified_scanner(ticker_list, time_factor):
    res_map, res_rev, res_intra = [], [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(ticker_list)
    adj_min_val = min_val * time_factor
    
    for idx, ticker in enumerate(ticker_list):
        status_text.text(f"Memindai 3 Strategi & Filter Resistance [{idx+1}/{total_tickers}]: {ticker}.JK ...")
        progress_bar.progress((idx + 1) / total_tickers)
        
        try:
            df = yf.download(f"{ticker}.JK", period="1y", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df[df['Volume'] > 0]
            if len(df) < 200:
                continue
                
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['ATR14'] = calculate_atr(df, period=14)
            df['Avg_Vol20'] = df['Volume'].rolling(20).mean()
            
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA50'] = df['Close'].rolling(50).mean()
            
            df['RSI2'] = calculate_rsi(df['Close'], period=2)
            df['MA200'] = df['Close'].rolling(200).mean()
            df['Std20'] = df['Close'].rolling(20).std()
            df['Lower_BB'] = df['MA20'] - (2 * df['Std20'])
            
            df['RVOL'] = df['Volume'] / df['Avg_Vol20']
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP_5D'] = (df['Typical_Price'] * df['Volume']).rolling(5).sum() / df['Volume'].rolling(5).sum()
            
            df['Res_20D'] = df['High'].shift(1).rolling(20).max()
            df['Gain_3D'] = ((df['Close'] - df['Close'].shift(3)) / df['Close'].shift(3)) * 100
            
            today = df.iloc[-1]
            prev = df.iloc[-2]
            
            entry_price = float(today['Close'])
            atr_val = float(today['ATR14'])
            total_value = float(entry_price * today['Volume'])
            pct_chg_today = float(today['Pct_Change'])
            
            if entry_price < 50 or total_value < adj_min_val or np.isnan(atr_val):
                continue

            candle_range = max(1.0, float(today['High'] - today['Low']))
            close_pos = (entry_price - float(today['Low'])) / candle_range
            res_20d = float(today['Res_20D']) if not np.isnan(today['Res_20D']) else entry_price
            dist_to_res_pct = ((entry_price - res_20d) / res_20d) * 100
            gain_3d = float(today['Gain_3D']) if not np.isnan(today['Gain_3D']) else pct_chg_today

            is_pre_breakout_zone = (-2.5 <= dist_to_res_pct <= 1.5)
            is_not_overextended = (gain_3d <= 4.5)
            is_strong_close = (close_pos >= 0.70)
            pass_strict_breakout = is_pre_breakout_zone and is_not_overextended and is_strong_close
                
            df_200 = df.tail(200).copy()
            
            # A. QUANT-MAP
            m_c1 = today['Close'] > today['MA20']
            m_c2 = today['MA20'] >= today['MA50']
            m_c3 = (today['Volume'] / time_factor) > today['Avg_Vol20']
            m_c4 = (today['Close'] > prev['Close']) and pass_strict_breakout
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
                "Change (%)": round(pct_chg_today, 2),
                "Jarak Res 20D (%)": f"{dist_to_res_pct:+.2f}%",
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
            
            # B. QUANT-REVERSION
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
                "Change (%)": round(pct_chg_today, 2),
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
            
            # C. QUANT-INTRADAY
            adj_rvol = float(today['RVOL']) / time_factor
            i_c1 = adj_rvol >= rvol_limit_intra
            i_c2 = (today['Close'] >= today['Typical_Price']) and is_strong_close
            i_c3 = (today['Close'] > today['VWAP_5D']) and (today['MA20'] >= today['MA50'])
            i_c4 = (today['Close'] > today['Open']) and (0 < pct_chg_today <= max_gain_intra) and is_not_overextended and is_pre_breakout_zone
            i_score = sum([i_c1, i_c2, i_c3, i_c4])
            
            sl_i, tp_i, safe_i, lot_i, modal_i = calc_position_sizing(entry_price, atr_val, intra_sl_mult, intra_tp_mult, modal_trading, max_risk_idr, intra_safe_mult)
            gross_safe_pct = ((safe_i - entry_price) / entry_price) * 100
            net_safe_pct = round(gross_safe_pct - 0.40, 2)
            
            res_intra.append({
                "Ticker": ticker,
                "Harga Entry": int(entry_price),
                "Change (%)": round(pct_chg_today, 2),
                "Jarak Res 20D (%)": f"{dist_to_res_pct:+.2f}%",
                "Harga VWAP": int(round(today['Typical_Price'])),
                "Adj RVOL (x)": round(adj_rvol, 2),
                "ATR 14 (Rp)": int(round(atr_val)),
                "Skor": i_score,
                "Lolos 4/4": "YA" if i_score == 4 else "TIDAK",
                "Rekomendasi Lot": lot_i,
                f"Profit Aman ({intra_safe_mult}x)": safe_i,
                "Net Profit Aman (%)": f"+{net_safe_pct}%" if net_safe_pct > 0 else f"{net_safe_pct}%",
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
# 7. TOMBOL EKSEKUSI TUNGGAL & TAMPILAN 4 TAB TERPADU (BAKU + GRAFIK 78 SAHAM)
# -----------------------------------------------------------------------------
u_paper = load_paper_db()

if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None

if st.button("🚀 Jalankan Pemindaian All-in-One (3 Strategi + Filter Resistance)", use_container_width=True):
    hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    now_wib = datetime.now(timezone(timedelta(hours=7)))
    waktu_lengkap = f"{hari_indo[now_wib.weekday()]}, {now_wib.strftime('%d-%m-%Y %H:%M:%S')} WIB"
    time_factor = get_intraday_time_factor(now_wib)
    
    df_map, df_rev, df_intra = run_unified_scanner(TICKERS_GABUNGAN, time_factor)
    st.session_state["scan_results"] = {
        "df_map": df_map,
        "df_rev": df_rev,
        "df_intra": df_intra,
        "waktu": waktu_lengkap
    }

if st.session_state["scan_results"] is None and (len(u_paper["positions"]) > 0 or len(u_paper["history"]) > 0):
    st.warning("📂 Ditemukan Posisi Saham Virtual Aktif dari sesi sebelumnya. Tekan tombol pemindaian di atas untuk sinyal hari ini, atau pantau posisi aktif Anda di bawah:")

if st.session_state["scan_results"] is not None:
    res_data = st.session_state["scan_results"]
    df_map = res_data["df_map"]
    df_rev = res_data["df_rev"]
    df_intra = res_data["df_intra"]
    
    map_4_tickers = set(df_map[(df_map['Skor'] == 4) & (df_map['Freq_Raw'] >= min_freq_map)]['Ticker']) if not df_map.empty else set()
    intra_4_tickers = set(df_intra[df_intra['Skor'] == 4]['Ticker']) if not df_intra.empty else set()
    double_signals = map_4_tickers.intersection(intra_4_tickers)
    
    st.info(f"Pemindaian Selesai | Modal: **Rp {modal_trading:,.0f}** | Batas Rugi/Trade: **Rp {max_risk_idr:,.0f}** | Waktu: **{res_data['waktu']}**")
    if double_signals:
        st.success(f"🔥 **DOUBLE SIGNAL TERDETEKSI (Lolos Ketat Breakout & Intraday):** **{', '.join(double_signals)}**")
    
    if not df_map.empty:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 1. QUANT-MAP (Breakout)", 
            "🔄 2. QUANT-REVERSION (Oversold)", 
            "⚡ 3. QUANT-INTRADAY (Siap Resistance)",
            f"💼 4. PAPER TRADING ({len(u_paper['positions'])} Aktif)"
        ])
        
        with tab1:
            df_m_perf = df_map[(df_map['Skor'] == 4) & (df_map['Freq_Raw'] >= min_freq_map)].copy()
            if not df_m_perf.empty:
                st.success(f"🎯 {len(df_m_perf)} Saham Lolos Sinyal Pre-Breakout Resistance 4/4:")
                df_m_show = df_m_perf.drop(columns=['Freq_Raw']).copy()
                df_m_show['Skor'] = df_m_show['Skor'].astype(str) + "/4"
                st.dataframe(df_m_show, use_container_width=True)
            else:
                st.warning("⚠️ Belum ada saham yang memenuhi syarat ketat Pre-Breakout 4/4 saat ini. Top 10 Pantauan:")
                df_m_fb = df_map.sort_values(by=["Skor", "Change (%)"], ascending=[False, False]).head(10).drop(columns=['Freq_Raw'])
                df_m_fb['Skor'] = df_m_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_m_fb, use_container_width=True)
            
            df_m_sorted = df_map.sort_values(by=["Skor", "Change (%)"], ascending=[False, False]).reset_index(drop=True)
            pilihan_m_idx = st.selectbox(
                "📊 Pilih Saham untuk Lihat Grafik Candle (Open, TP & SL):",
                range(len(df_m_sorted)),
                format_func=lambda i: f"{'🎯 [4/4] ' if df_m_sorted.loc[i, 'Skor'] == 4 else f'[{df_m_sorted.loc[i, \"Skor\"]}/4] '}{df_m_sorted.loc[i, 'Ticker']} — Open: Rp {df_m_sorted.loc[i, 'Harga Entry']:,} | TP: Rp {df_m_sorted.loc[i, f'TP ATR ({map_tp_mult}x)']:,} | SL: Rp {df_m_sorted.loc[i, f'SL ATR ({map_sl_mult}x)']:,}",
                key="grafik_m_all"
            )
            row_m = df_m_sorted.iloc[pilihan_m_idx]
            tampilkan_grafik_candle(row_m['Ticker'], row_m['Harga Entry'], row_m[f"TP ATR ({map_tp_mult}x)"], row_m[f"SL ATR ({map_sl_mult}x)"], f"Quant-Map ({row_m['Skor']}/4)", default_tf="Daily", widget_key="tf_map")
                
        with tab2:
            df_r_perf = df_rev[df_rev['Skor'] == 4].sort_values(by="RSI-2", ascending=True).copy()
            if not df_r_perf.empty:
                st.success(f"🎯 {len(df_r_perf)} Saham Lolos Sinyal Pantulan Jenuh Jual 4/4:")
                df_r_show = df_r_perf.copy()
                df_r_show['Skor'] = df_r_show['Skor'].astype(str) + "/4"
                st.dataframe(df_r_show, use_container_width=True)
            else:
                st.warning("⚠️ Belum ada sinyal Mean Reversion 4/4 hari ini. Menampilkan Top 10 Saham RSI-2 Terendah:")
                df_r_fb = df_rev.sort_values(by=["Skor", "RSI-2"], ascending=[False, True]).head(10)
                df_r_fb['Skor'] = df_r_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_r_fb, use_container_width=True)
            
            df_r_sorted = df_rev.sort_values(by=["Skor", "RSI-2"], ascending=[False, True]).reset_index(drop=True)
            pilihan_r_idx = st.selectbox(
                "📊 Pilih Saham untuk Lihat Grafik Candle (Open, TP & SL):",
                range(len(df_r_sorted)),
                format_func=lambda i: f"{'🎯 [4/4] ' if df_r_sorted.loc[i, 'Skor'] == 4 else f'[{df_r_sorted.loc[i, \"Skor\"]}/4] '}{df_r_sorted.loc[i, 'Ticker']} — Open: Rp {df_r_sorted.loc[i, 'Harga Entry']:,} | TP: Rp {df_r_sorted.loc[i, f'TP ATR ({rev_tp_mult}x)']:,} | SL: Rp {df_r_sorted.loc[i, f'SL ATR ({rev_sl_mult}x)']:,}",
                key="grafik_r_all"
            )
            row_r = df_r_sorted.iloc[pilihan_r_idx]
            tampilkan_grafik_candle(row_r['Ticker'], row_r['Harga Entry'], row_r[f"TP ATR ({rev_tp_mult}x)"], row_r[f"SL ATR ({rev_sl_mult}x)"], f"Quant-Reversion ({row_r['Skor']}/4)", default_tf="Daily", widget_key="tf_rev")
                
        with tab3:
            df_i_perf = df_intra[df_intra['Skor'] == 4].sort_values(by="Adj RVOL (x)", ascending=False).copy()
            if not df_i_perf.empty:
                st.success(f"🎯 {len(df_i_perf)} Saham Lolos Sinyal Ketat Siap Resistance (Naik ≤ {max_gain_intra}%) 4/4:")
                df_i_show = df_i_perf.copy()
                df_i_show['Skor'] = df_i_show['Skor'].astype(str) + "/4"
                st.dataframe(df_i_show, use_container_width=True)
            else:
                st.warning("⚠️ Belum ada sinyal ketat Siap Resistance 4/4 saat ini. Menampilkan Top 10 Adj RVOL Tertinggi:")
                df_i_fb = df_intra.sort_values(by=["Skor", "Adj RVOL (x)"], ascending=[False, False]).head(10)
                df_i_fb['Skor'] = df_i_fb['Skor'].astype(str) + "/4"
                st.dataframe(df_i_fb, use_container_width=True)
            
            df_i_sorted = df_intra.sort_values(by=["Skor", "Adj RVOL (x)"], ascending=[False, False]).reset_index(drop=True)
            pilihan_i_idx = st.selectbox(
                "📊 Pilih Saham untuk Lihat Grafik Candle (Open, TP & SL):",
                range(len(df_i_sorted)),
                format_func=lambda i: f"{'🎯 [4/4] ' if df_i_sorted.loc[i, 'Skor'] == 4 else f'[{df_i_sorted.loc[i, \"Skor\"]}/4] '}{df_i_sorted.loc[i, 'Ticker']} — Open: Rp {df_i_sorted.loc[i, 'Harga Entry']:,} | TP: Rp {df_i_sorted.loc[i, f'Profit Aman ({intra_safe_mult}x)']:,} | SL: Rp {df_i_sorted.loc[i, f'SL Ketat ({intra_sl_mult}x)']:,}",
                key="grafik_i_all"
            )
            row_i = df_i_sorted.iloc[pilihan_i_idx]
            tampilkan_grafik_candle(row_i['Ticker'], row_i['Harga Entry'], row_i[f"Profit Aman ({intra_safe_mult}x)"], row_i[f"SL Ketat ({intra_sl_mult}x)"], f"Quant-Intraday ({row_i['Skor']}/4)", default_tf="Daily", widget_key="tf_intra")
                
        with tab4:
            u_paper = load_paper_db()
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            invested_val = sum(p["buy_cost"] for p in u_paper["positions"])
            total_realized = sum(h["Net P/L (Rp)"] for h in u_paper["history"])
            
            col_p1.metric("Modal Awal Simulasi", f"Rp {u_paper['initial_capital']:,.0f}")
            col_p2.metric("Saldo RDN Virtual", f"Rp {u_paper['cash']:,.0f}")
            col_p3.metric("Dana di Posisi Aktif", f"Rp {invested_val:,.0f}")
            col_p4.metric("Total Realized P/L", f"Rp {total_realized:+,.0f}")
            
            st.markdown("---")
            st.subheader("⚡ Eksekusi BUY Virtual (Dari Sinyal Lolos 4/4)")
            
            kandidat_order = []
            for _, row in df_map[(df_map['Skor'] == 4) & (df_map['Freq_Raw'] >= min_freq_map)].iterrows():
                lot_num = int(str(row["Rekomendasi Lot"]).split()[0])
                if lot_num > 0:
                    tag = "🔥 DOUBLE | " if row['Ticker'] in double_signals else ""
                    kandidat_order.append({
                        "label": f"{tag}[Quant-Map] {row['Ticker']} | Entry: Rp {row['Harga Entry']:,} | {lot_num} Lot | TP: {row[f'TP ATR ({map_tp_mult}x)']} | SL: {row[f'SL ATR ({map_sl_mult}x)']}",
                        "ticker": row["Ticker"], "strategy": "Quant-Map", "entry": row["Harga Entry"],
                        "lot": lot_num, "tp": row[f"TP ATR ({map_tp_mult}x)"], "sl": row[f"SL ATR ({map_sl_mult}x)"]
                    })
            for _, row in df_rev[df_rev['Skor'] == 4].iterrows():
                lot_num = int(str(row["Rekomendasi Lot"]).split()[0])
                if lot_num > 0:
                    kandidat_order.append({
                        "label": f"[Quant-Reversion] {row['Ticker']} | Entry: Rp {row['Harga Entry']:,} | {lot_num} Lot | TP: {row[f'TP ATR ({rev_tp_mult}x)']} | SL: {row[f'SL ATR ({rev_sl_mult}x)']}",
                        "ticker": row["Ticker"], "strategy": "Quant-Reversion", "entry": row["Harga Entry"],
                        "lot": lot_num, "tp": row[f"TP ATR ({rev_tp_mult}x)"], "sl": row[f"SL ATR ({rev_sl_mult}x)"]
                    })
            for _, row in df_intra[df_intra['Skor'] == 4].iterrows():
                lot_num = int(str(row["Rekomendasi Lot"]).split()[0])
                if lot_num > 0:
                    tag = "🔥 DOUBLE | " if row['Ticker'] in double_signals else ""
                    kandidat_order.append({
                        "label": f"{tag}[Quant-Intraday] {row['Ticker']} | Entry: Rp {row['Harga Entry']:,} | {lot_num} Lot | Profit Aman: {row[f'Profit Aman ({intra_safe_mult}x)']} | SL: {row[f'SL Ketat ({intra_sl_mult}x)']}",
                        "ticker": row["Ticker"], "strategy": "Quant-Intraday", "entry": row["Harga Entry"],
                        "lot": lot_num, "tp": row[f"Profit Aman ({intra_safe_mult}x)"], "sl": row[f"SL Ketat ({intra_sl_mult}x)"]
                    })
                    
            if kandidat_order:
                pilihan_idx = st.selectbox(
                    "Pilih Saham Lolos Sinyal 4/4:",
                    range(len(kandidat_order)),
                    format_func=lambda x: kandidat_order[x]["label"]
                )
                sel = kandidat_order[pilihan_idx]
                tampilkan_grafik_candle(sel["ticker"], sel["entry"], sel["tp"], sel["sl"], f"Preview ({sel['strategy']})", default_tf="Daily", widget_key="tf_preview")
                
                if st.button("🟢 Eksekusi BUY Virtual", use_container_width=True):
                    ok, msg = execute_paper_buy(sel["ticker"], sel["strategy"], sel["entry"], sel["lot"], sel["tp"], sel["sl"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.info("ℹ️ Belum ada sinyal 4/4 dengan alokasi lot > 0 untuk dieksekusi.")
                
            st.markdown("---")
            st.subheader(f"📂 Posisi Saham Virtual Aktif ({len(u_paper['positions'])})")
            if st.button("🔄 Cek Harga Live & Auto-TP/SL", use_container_width=True):
                closed_logs = []
                for i in range(len(u_paper["positions"]) - 1, -1, -1):
                    p = u_paper["positions"][i]
                    try:
                        live_df = yf.download(f"{p['ticker']}.JK", period="1d", interval="5m", progress=False)
                        if isinstance(live_df.columns, pd.MultiIndex):
                            live_df.columns = live_df.columns.get_level_values(0)
                        if not live_df.empty:
                            high_p = int(round(float(live_df['High'].max())))
                            low_p = int(round(float(live_df['Low'].min())))
                            if high_p >= p["tp_price"]:
                                pnl = execute_paper_sell(i, p["tp_price"], "Auto-TP Tercapai 🎯")
                                closed_logs.append(f"🎯 **{p['ticker']}** kena Take Profit @ Rp {p['tp_price']:,} (Net P/L: Rp {pnl:+,.0f})")
                            elif low_p <= p["sl_price"]:
                                pnl = execute_paper_sell(i, p["sl_price"], "Auto-SL Terpicu 🛡️")
                                closed_logs.append(f"🛡️ **{p['ticker']}** kena Stop Loss @ Rp {p['sl_price']:,} (Net P/L: Rp {pnl:+,.0f})")
                    except Exception:
                        pass
                if closed_logs:
                    for log in closed_logs:
                        st.info(log)
                    st.rerun()
                else:
                    st.success("✅ Harga live dicek: Belum ada posisi yang menyentuh garis TP maupun SL.")
                    
            u_paper = load_paper_db()
            if u_paper["positions"]:
                for idx_p, p in enumerate(u_paper["positions"]):
                    st.markdown(f"**{p['ticker']}** ({p['strategy']}) — Entry: **Rp {p['entry_price']:,}** | **{p['lot']} Lot** | Modal Terpakai: **Rp {p['buy_cost']:,}** | TP: **Rp {p['tp_price']:,}** | SL: **Rp {p['sl_price']:,}**")
                    if st.button(f"🔴 Tutup Posisi {p['ticker']} @Entry", key=f"sell_{p['id']}"):
                        execute_paper_sell(idx_p, p["entry_price"], "Tutup Manual")
                        st.rerun()
                
                pos_idx_grafik = st.selectbox(
                    "Grafik Posisi Aktif (Garis Open, TP & SL):",
                    range(len(u_paper["positions"])),
                    format_func=lambda i: f"{u_paper['positions'][i]['ticker']} ({u_paper['positions'][i]['strategy']}) — Open: Rp {u_paper['positions'][i]['entry_price']:,} | TP: Rp {u_paper['positions'][i]['tp_price']:,} | SL: Rp {u_paper['positions'][i]['sl_price']:,}",
                    key="grafik_posisi_aktif"
                )
                p_aktif = u_paper["positions"][pos_idx_grafik]
                tampilkan_grafik_candle(p_aktif["ticker"], p_aktif["entry_price"], p_aktif["tp_price"], p_aktif["sl_price"], f"Posisi Aktif ({p_aktif['strategy']})", default_tf="M15", widget_key="tf_aktif_tab4")
            else:
                st.caption("Belum ada posisi saham virtual yang sedang terbuka.")
                
            st.markdown("---")
            st.subheader("📜 Jurnal Riwayat Transaksi Selesai")
            if u_paper["history"]:
                st.dataframe(pd.DataFrame(u_paper["history"]), use_container_width=True)
            else:
                st.caption("Belum ada transaksi yang ditutup.")
                
            st.markdown("---")
            st.subheader("💾 Cadangan & Pemulihan Jurnal (.json)")
            st.download_button(
                label="⬇️ Unduh File Backup Jurnal (.json)",
                data=json.dumps(u_paper, indent=2),
                file_name=f"jurnal_quant_{datetime.now(timezone(timedelta(hours=7))).strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
            uploaded_backup = st.file_uploader("⬆️ Pulihkan dari File Backup (.json)", type=["json"])
            if uploaded_backup is not None:
                if st.button("📥 Terapkan File Backup Ini", use_container_width=True):
                    try:
                        restored = json.load(uploaded_backup)
                        if "cash" in restored and "positions" in restored:
                            save_paper_db(restored)
                            st.success("✅ Seluruh posisi aktif & jurnal riwayat berhasil dipulihkan!")
                            st.rerun()
                        else:
                            st.error("Format file backup tidak sesuai.")
                    except Exception as e:
                        st.error(f"Gagal membaca file: {e}")

            st.markdown("---")
            if st.button(f"♻️ Reset Saldo Simulasi ke Modal Sidebar (Rp {modal_trading:,.0f})", use_container_width=True):
                save_paper_db({
                    "initial_capital": int(modal_trading),
                    "cash": int(modal_trading),
                    "positions": [],
                    "history": []
                })
                st.success(f"✅ Saldo simulasi direset ke Rp {modal_trading:,.0f}!")
                st.rerun()
    else:
        st.error("Tidak ada saham yang memenuhi filter Minimum Daily Value.")
else:
    if len(u_paper["positions"]) > 0 or len(u_paper["history"]) > 0:
        st.markdown("---")
        st.subheader("💼 Status Portofolio Virtual Tersimpan")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        invested_val = sum(p["buy_cost"] for p in u_paper["positions"])
        total_realized = sum(h["Net P/L (Rp)"] for h in u_paper["history"])
        col_p1.metric("Modal Awal Simulasi", f"Rp {u_paper['initial_capital']:,.0f}")
        col_p2.metric("Saldo RDN Virtual", f"Rp {u_paper['cash']:,.0f}")
        col_p3.metric("Dana di Posisi Aktif", f"Rp {invested_val:,.0f}")
        col_p4.metric("Total Realized P/L", f"Rp {total_realized:+,.0f}")
        if u_paper["positions"]:
            for p in u_paper["positions"]:
                st.markdown(f"• **{p['ticker']}** ({p['strategy']}) — Entry: **Rp {p['entry_price']:,}** | **{p['lot']} Lot** | Terpakai: **Rp {p['buy_cost']:,}** | TP: **Rp {p['tp_price']:,}** | SL: **Rp {p['sl_price']:,}**")
            
            pos_idx_saved = st.selectbox(
                "Grafik Posisi Aktif (Garis Open, TP & SL):",
                range(len(u_paper["positions"])),
                format_func=lambda i: f"{u_paper['positions'][i]['ticker']} ({u_paper['positions'][i]['strategy']}) — Open: Rp {u_paper['positions'][i]['entry_price']:,} | TP: Rp {u_paper['positions'][i]['tp_price']:,} | SL: Rp {u_paper['positions'][i]['sl_price']:,}",
                key="grafik_posisi_tersimpan"
            )
            p_saved = u_paper["positions"][pos_idx_saved]
            tampilkan_grafik_candle(p_saved["ticker"], p_saved["entry_price"], p_saved["tp_price"], p_saved["sl_price"], f"Posisi Aktif ({p_saved['strategy']})", default_tf="M15", widget_key="tf_saved_pos")

# -----------------------------------------------------------------------------
# FOOTER & LISENSI
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("<center><small>SAHAM-QUANT-SUITE MASTER EDITION | Core Quantitative Engine | Licensed to Rommy Sanjaya</small></center>", unsafe_allow_html=True)
