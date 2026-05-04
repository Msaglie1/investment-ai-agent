import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Investment AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CAPITAL_INICIAL   = 10500
ARCHIVO_HISTORIAL = "historial_v2.json"

# ============================================================
# MERCADOS DISPONIBLES
# ============================================================
ACCIONES_USA = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google",
    "AMZN": "Amazon", "NVDA": "Nvidia", "META": "Meta",
    "TSLA": "Tesla", "JPM": "JPMorgan", "JNJ": "Johnson & Johnson",
    "BRK-B": "Berkshire", "AMD": "AMD", "NFLX": "Netflix",
    "DIS": "Disney", "V": "Visa", "MA": "Mastercard",
    "BAC": "Bank of America", "WMT": "Walmart", "XOM": "ExxonMobil"
}

CRIPTO = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "BNB",
    "SOL-USD": "Solana", "XRP-USD": "XRP", "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin", "AVAX-USD": "Avalanche"
}

GLOBALES = {
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "Nasdaq",
    "^FTSE": "FTSE 100", "^N225": "Nikkei 225", "^HSI": "Hang Seng",
    "GC=F": "Oro", "CL=F": "Petróleo", "^VIX": "VIX (Miedo)",
    "DX-Y.NYB": "Dólar (DXY)", "^TNX": "Bonos 10Y USA",
    "EURUSD=X": "EUR/USD", "^BVSP": "Bovespa (Brasil)"
}

# ============================================================
# ESTILOS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Lato:wght@300;400&display=swap');

html, body, [class*="css"] { font-family: 'Lato', sans-serif; }

.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 1.5rem; border-bottom: 1px solid #1e2a1e; margin-bottom: 1.5rem;
}
.logo {
    font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700;
    color: #e8f5e2; letter-spacing: -0.02em;
}
.logo span { color: #7bc67e; }
.tagline { font-size: 0.75rem; color: #4a6741; font-family: 'IBM Plex Mono', monospace; margin-top: 2px; }

.pill {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; font-weight: 500;
    padding: 5px 12px; border-radius: 100px;
}
.pill-paper { background: #1a2f1a; color: #7bc67e; border: 1px solid #2d4a2d; }
.pill-real  { background: #2f1a1a; color: #e07070; border: 1px solid #4a2d2d; }

.metric-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 1.5rem; }
.metric-card {
    background: #0d1a0d; border: 1px solid #1e2a1e; border-radius: 10px;
    padding: 1rem 1.25rem;
}
.metric-label { font-size: 0.7rem; color: #4a6741; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; font-family: 'IBM Plex Mono', monospace; }
.metric-value { font-size: 1.5rem; font-weight: 700; color: #e8f5e2; font-family: 'Syne', sans-serif; }
.metric-sub { font-size: 0.75rem; margin-top: 3px; font-family: 'IBM Plex Mono', monospace; }
.pos { color: #7bc67e; } .neg { color: #e07070; } .neu { color: #4a6741; }

.section-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    color: #4a6741; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px;
}

.card {
    background: #0d1a0d; border: 1px solid #1e2a1e; border-radius: 10px;
    padding: 1.25rem; margin-bottom: 1rem;
}

.signal-buy  { background: #0d1a0d; border-left: 3px solid #7bc67e; border-radius: 8px; padding: 1rem; margin-bottom: 8px; }
.signal-sell { background: #1a0d0d; border-left: 3px solid #e07070; border-radius: 8px; padding: 1rem; margin-bottom: 8px; }
.signal-ticker { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; }
.signal-text { font-size: 0.82rem; color: #6b8c6b; margin-top: 4px; line-height: 1.5; }
.signal-prices { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; margin-top: 6px; }

.op-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #1e2a1e; }
.op-row:last-child { border-bottom: none; }
.op-ticker { font-family: 'Syne', sans-serif; font-size: 0.9rem; font-weight: 600; color: #e8f5e2; }
.op-detail { font-size: 0.75rem; color: #4a6741; font-family: 'IBM Plex Mono', monospace; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 100px; font-size: 0.65rem; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }
.b-open { background: #0d1f2d; color: #5ba3d9; border: 1px solid #1a3a52; }
.b-win  { background: #0d1a0d; color: #7bc67e; border: 1px solid #2d4a2d; }
.b-loss { background: #1a0d0d; color: #e07070; border: 1px solid #4a2d2d; }

.learn-box { background: #111f11; border-radius: 8px; padding: 1rem; font-size: 0.82rem; color: #6b8c6b; line-height: 1.6; font-style: italic; border-left: 2px solid #2d4a2d; }

.ticker-btn-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1rem; }
.mkt-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.mkt-price { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 700; color: #e8f5e2; }
.mkt-change-pos { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; color: #7bc67e; }
.mkt-change-neg { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; color: #e07070; }

.stTabs [data-baseweb="tab-list"] {
    gap: 2px; background: transparent;
    border-bottom: 1px solid #1e2a1e; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
    color: #4a6741; background: transparent; border: none;
    padding: 8px 16px; border-radius: 6px 6px 0 0;
}
.stTabs [aria-selected="true"] {
    color: #7bc67e; background: #0d1a0d;
    border: 1px solid #1e2a1e; border-bottom: 1px solid #0d1a0d; font-weight: 500;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

div[data-testid="stMetric"] { background: #0d1a0d; border: 1px solid #1e2a1e; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; color: #e8f5e2 !important; }
div[data-testid="stMetricDelta"] { font-family: 'IBM Plex Mono', monospace !important; }

.stSelectbox > div > div { background: #0d1a0d; border-color: #1e2a1e; color: #e8f5e2; }
.stTextInput > div > div { background: #0d1a0d; border-color: #1e2a1e; color: #e8f5e2; }

[data-testid="stSidebar"] { background: #080f08; }

.empty-state { text-align: center; padding: 3rem; color: #4a6741; font-size: 0.875rem; font-family: 'IBM Plex Mono', monospace; }

.macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.macro-item { background: #111f11; border-radius: 8px; padding: 10px 14px; }
.macro-name { font-size: 0.7rem; color: #4a6741; font-family: 'IBM Plex Mono', monospace; margin-bottom: 4px; }
.macro-val  { font-size: 1rem; font-weight: 600; color: #e8f5e2; font-family: 'Syne', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
@st.cache_data(ttl=300)
def descargar_datos(ticker, period="6mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def precio_actual(ticker):
    try:
        df = yf.download(ticker, period="2d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if len(df) >= 2:
            hoy   = float(df["Close"].iloc[-1])
            ayer  = float(df["Close"].iloc[-2])
            cambio = ((hoy - ayer) / ayer) * 100
            return hoy, cambio
        return None, None
    except:
        return None, None

@st.cache_data(ttl=60)
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"operaciones": [], "reportes": [], "aprendizajes": []}

def calcular_metricas(historial):
    ops       = historial.get("operaciones", [])
    cerradas  = [o for o in ops if o.get("estado","").startswith("cerrada")]
    ganadoras = [o for o in cerradas if o.get("resultado_usd", 0) > 0]
    ganancia  = sum(o.get("resultado_usd", 0) for o in cerradas)
    abiertas  = [o for o in ops if o.get("estado") == "abierta"]
    invertido = sum(o.get("capital_invertido", 0) for o in abiertas)
    win_rate  = (len(ganadoras) / len(cerradas) * 100) if cerradas else 0
    return {
        "ganancia_total": round(ganancia, 2),
        "capital_actual": round(CAPITAL_INICIAL + ganancia, 2),
        "invertido":      round(invertido, 2),
        "en_caja":        round(CAPITAL_INICIAL + ganancia - invertido, 2),
        "cerradas":       len(cerradas),
        "ganadoras":      len(ganadoras),
        "abiertas":       len(abiertas),
        "win_rate":       round(win_rate, 1),
    }

def calcular_rsi(close, window=14):
    delta = close.diff()
    gain  = delta.where(delta > 0, 0).rolling(window).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))

def grafico_velas(df, ticker, mostrar_indicadores=True):
    if df.empty:
        return None

    # Calcular indicadores
    close  = df["Close"]
    ma20   = close.rolling(20).mean()
    ma50   = close.rolling(50).mean()
    rsi    = calcular_rsi(close)
    ema12  = close.ewm(span=12, adjust=False).mean()
    ema26  = close.ewm(span=26, adjust=False).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_up  = bb_mid + 2 * bb_std
    bb_dn  = bb_mid - 2 * bb_std

    if mostrar_indicadores:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=["", "RSI (14)", "MACD"]
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # Velas japonesas
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=ticker,
        increasing_line_color="#7bc67e",
        decreasing_line_color="#e07070",
        increasing_fillcolor="#7bc67e",
        decreasing_fillcolor="#e07070",
        line_width=1,
    ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=bb_up, line=dict(color="#2d4a6e", width=1), name="BB Superior", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_dn, line=dict(color="#2d4a6e", width=1), fill="tonexty", fillcolor="rgba(45,74,110,0.08)", name="BB Inferior", showlegend=False), row=1, col=1)

    # Medias móviles
    fig.add_trace(go.Scatter(x=df.index, y=ma20, line=dict(color="#f0c040", width=1.5), name="MA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma50, line=dict(color="#a78bfa", width=1.5), name="MA50"), row=1, col=1)

    # Volumen
    colors = ["#7bc67e" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#e07070" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, opacity=0.3, name="Volumen", showlegend=False), row=1, col=1)

    if mostrar_indicadores:
        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color="#7bc67e", width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#e07070", line_width=1, row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#7bc67e", line_width=1, row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(224,112,112,0.05)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(123,198,126,0.05)", line_width=0, row=2, col=1)

        # MACD
        macd_colors = ["#7bc67e" if v >= 0 else "#e07070" for v in (macd - signal)]
        fig.add_trace(go.Bar(x=df.index, y=macd - signal, marker_color=macd_colors, name="Histograma", opacity=0.6), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd,   line=dict(color="#7bc67e", width=1.5), name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=signal, line=dict(color="#f0c040", width=1.5), name="Señal"), row=3, col=1)

    fig.update_layout(
        height=580 if mostrar_indicadores else 420,
        paper_bgcolor="#080f08",
        plot_bgcolor="#080f08",
        font=dict(family="IBM Plex Mono", size=11, color="#4a6741"),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#6b8c6b")
        ),
        margin=dict(t=30, b=20, l=10, r=10),
    )
    for i in range(1, 4 if mostrar_indicadores else 2):
        fig.update_xaxes(
            showgrid=True, gridcolor="#0d1a0d", zeroline=False,
            showspikes=True, spikecolor="#2d4a2d", spikethickness=1,
            row=i, col=1
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="#0d1a0d", zeroline=False,
            row=i, col=1
        )

    return fig

# ============================================================
# CARGAR DATOS
# ============================================================
historial = cargar_historial()
metricas  = calcular_metricas(historial)
reportes  = historial.get("reportes", [])
ultimo    = reportes[-1] if reportes else None

# ============================================================
# HEADER
# ============================================================
modo_label = historial.get("reportes", [{}])[-1].get("analisis", {}) if reportes else {}
st.markdown("""
<div class="top-bar">
  <div>
    <div class="logo">Investment <span>AI</span> Agent</div>
    <div class="tagline">multi-agent · paper trading · S&P500 · CRYPTO · GLOBAL</div>
  </div>
  <div style="display:flex;gap:10px;align-items:center">
    <span class="pill pill-paper">● PAPER TRADING</span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#4a6741">
""" + datetime.now().strftime("%d/%m/%Y %H:%M") + """
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MÉTRICAS
# ============================================================
c1, c2, c3, c4, c5 = st.columns(5)
pct = ((metricas["capital_actual"] - CAPITAL_INICIAL) / CAPITAL_INICIAL * 100)
with c1:
    st.metric("Capital actual", f"${metricas['capital_actual']:,.0f}", f"${metricas['ganancia_total']:+,.2f}")
with c2:
    st.metric("Retorno total", f"{pct:+.2f}%", "vs capital inicial")
with c3:
    st.metric("Win rate", f"{metricas['win_rate']}%", f"{metricas['ganadoras']} de {metricas['cerradas']} ops")
with c4:
    st.metric("Posiciones abiertas", metricas["abiertas"], f"${metricas['invertido']:,.0f} en juego")
with c5:
    st.metric("En caja", f"${metricas['en_caja']:,.0f}", "disponible")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ============================================================
# TABS PRINCIPALES
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Mercado", "🤖 Agente IA", "💼 Operaciones", "📊 Performance", "🌍 Macro", "⚙️ Config"
])

# ══════════════════════════════════════════════════════
# TAB 1 — MERCADO (gráficos)
# ══════════════════════════════════════════════════════
with tab1:
    col_izq, col_der = st.columns([1, 3])

    with col_izq:
        st.markdown('<div class="section-label">Seleccionar mercado</div>', unsafe_allow_html=True)
        mercado = st.radio("", ["🇺🇸 Acciones USA", "₿ Cripto", "🌍 Global & Índices"], label_visibility="collapsed")

        if "USA" in mercado:
            opciones = ACCIONES_USA
        elif "Cripto" in mercado:
            opciones = CRIPTO
        else:
            opciones = GLOBALES

        ticker_sel = st.selectbox("Activo", list(opciones.keys()), format_func=lambda x: f"{x} — {opciones[x]}", label_visibility="collapsed")

        st.markdown('<div class="section-label" style="margin-top:1rem">Período</div>', unsafe_allow_html=True)
        periodo = st.radio("", ["1mo", "3mo", "6mo", "1y", "2y"], horizontal=True, label_visibility="collapsed")

        st.markdown('<div class="section-label" style="margin-top:1rem">Intervalo</div>', unsafe_allow_html=True)
        intervalo = st.radio("", ["1d", "1wk"], horizontal=True, label_visibility="collapsed")

        st.markdown('<div class="section-label" style="margin-top:1rem">Indicadores</div>', unsafe_allow_html=True)
        mostrar_ind = st.toggle("RSI + MACD", value=True)

        st.markdown('<div class="section-label" style="margin-top:1rem">Buscar cualquier ticker</div>', unsafe_allow_html=True)
        ticker_custom = st.text_input("", placeholder="ej: COIN, UBER, MATIC-USD", label_visibility="collapsed")
        if ticker_custom:
            ticker_sel = ticker_custom.upper().strip()

        # Precio actual
        precio, cambio = precio_actual(ticker_sel)
        if precio:
            color = "mkt-change-pos" if cambio >= 0 else "mkt-change-neg"
            signo = "+" if cambio >= 0 else ""
            st.markdown(f"""
            <div style="margin-top:1.5rem">
                <div class="section-label">Precio actual</div>
                <div class="mkt-price">${precio:,.2f}</div>
                <div class="{color}">{signo}{cambio:.2f}% hoy</div>
            </div>
            """, unsafe_allow_html=True)

    with col_der:
        st.markdown(f'<div class="section-label">{ticker_sel} — Velas japonesas · {periodo} · {intervalo}</div>', unsafe_allow_html=True)
        with st.spinner("Cargando gráfico..."):
            df = descargar_datos(ticker_sel, period=periodo, interval=intervalo)
        if not df.empty:
            fig = grafico_velas(df, ticker_sel, mostrar_ind)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="empty-state">No se encontraron datos para este ticker</div>', unsafe_allow_html=True)

    # Mini watchlist
    st.markdown('<div class="section-label" style="margin-top:1rem">Watchlist rápida</div>', unsafe_allow_html=True)
    watchlist = ["AAPL", "NVDA", "TSLA", "MSFT", "BTC-USD", "ETH-USD", "^GSPC", "^VIX"]
    cols = st.columns(len(watchlist))
    for i, t in enumerate(watchlist):
        p, c = precio_actual(t)
        with cols[i]:
            if p and c is not None:
                color = "#7bc67e" if c >= 0 else "#e07070"
                signo = "+" if c >= 0 else ""
                st.markdown(f"""
                <div style="background:#0d1a0d;border:1px solid #1e2a1e;border-radius:8px;padding:10px;text-align:center">
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#4a6741">{t}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#e8f5e2">${p:,.1f}</div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:{color}">{signo}{c:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 2 — AGENTE IA
# ══════════════════════════════════════════════════════
with tab2:
    if not ultimo:
        st.markdown('<div class="empty-state">Sin reportes todavía.<br>Corre python investment_agent_v2.py para el primer análisis.</div>', unsafe_allow_html=True)
    else:
        analisis = ultimo.get("analisis", {})
        fecha    = ultimo.get("fecha", "—")
        vix_rep  = ultimo.get("vix", "—")
        fg_rep   = ultimo.get("fear_greed", "—")

        col_a, col_b = st.columns([3, 2])

        with col_a:
            st.markdown(f'<div class="section-label">Análisis CEO Agent · {fecha}</div>', unsafe_allow_html=True)

            nivel = analisis.get("nivel_riesgo", "—")
            color_nivel = {"BAJO": "#7bc67e", "MEDIO": "#f0c040", "ALTO": "#e07070"}.get(nivel, "#4a6741")

            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="font-size:0.9rem;color:#8aab8a;line-height:1.7;max-width:75%">
                        {analisis.get('resumen_mercado', '—')}
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:0.65rem;color:#4a6741;font-family:'IBM Plex Mono',monospace;margin-bottom:4px">RIESGO</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{color_nivel};font-family:'Syne',sans-serif">{nivel}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Señales compra
            st.markdown('<div class="section-label">Señales de compra</div>', unsafe_allow_html=True)
            compras = analisis.get("señales_compra", [])
            if compras:
                for s in compras:
                    confianza_color = {"ALTA": "#7bc67e", "MEDIA": "#f0c040", "BAJA": "#e07070"}.get(s.get("confianza",""), "#4a6741")
                    factores = " · ".join(s.get("factores", []))
                    st.markdown(f"""
                    <div class="signal-buy">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span class="signal-ticker" style="color:#7bc67e">{s.get('ticker','')}</span>
                            <span style="font-size:0.7rem;color:{confianza_color};font-family:'IBM Plex Mono',monospace">
                                CONFIANZA {s.get('confianza','')}
                            </span>
                        </div>
                        <div class="signal-prices">
                            entrada <b style="color:#e8f5e2">${s.get('precio_entrada_sugerido',0):.2f}</b> &nbsp;→&nbsp;
                            objetivo <b style="color:#7bc67e">${s.get('precio_objetivo',0):.2f}</b> &nbsp;|&nbsp;
                            stop <b style="color:#e07070">${s.get('stop_loss',0):.2f}</b>
                        </div>
                        <div class="signal-text">{s.get('justificacion','')}</div>
                        <div style="margin-top:6px;font-size:0.7rem;color:#4a6741;font-family:'IBM Plex Mono',monospace">{factores}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state" style="padding:1.5rem">Sin señales de compra hoy</div>', unsafe_allow_html=True)

            # Señales venta
            st.markdown('<div class="section-label" style="margin-top:1rem">Evitar / Vender</div>', unsafe_allow_html=True)
            ventas = analisis.get("señales_venta", [])
            if ventas:
                for s in ventas:
                    st.markdown(f"""
                    <div class="signal-sell">
                        <span class="signal-ticker" style="color:#e07070">{s.get('ticker','')}</span>
                        <div class="signal-text">{s.get('razon','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_b:
            # Sentimiento
            st.markdown('<div class="section-label">Sentimiento del mercado</div>', unsafe_allow_html=True)
            fg = fg_rep if isinstance(fg_rep, (int, float)) else 50
            color_fg = "#e07070" if fg < 30 else "#f0c040" if fg < 50 else "#7bc67e" if fg < 75 else "#e07070"
            label_fg = "MIEDO EXTREMO" if fg < 20 else "MIEDO" if fg < 40 else "NEUTRO" if fg < 60 else "CODICIA" if fg < 80 else "CODICIA EXTREMA"

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=fg,
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#4a6741"),
                    bar=dict(color=color_fg),
                    bgcolor="#0d1a0d",
                    bordercolor="#1e2a1e",
                    steps=[
                        dict(range=[0, 25], color="#2f1a1a"),
                        dict(range=[25, 50], color="#1f1f0d"),
                        dict(range=[50, 75], color="#0d1a0d"),
                        dict(range=[75, 100], color="#1a2f0d"),
                    ],
                    threshold=dict(line=dict(color="#e8f5e2", width=2), thickness=0.75, value=fg)
                ),
                number=dict(font=dict(color="#e8f5e2", family="Syne"), suffix=""),
                title=dict(text=label_fg, font=dict(color=color_fg, family="IBM Plex Mono", size=12))
            ))
            fig_gauge.update_layout(
                height=200, margin=dict(t=20, b=10, l=20, r=20),
                paper_bgcolor="#080f08", font=dict(color="#4a6741")
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <span style="font-size:0.75rem;color:#4a6741;font-family:'IBM Plex Mono',monospace">VIX</span>
                    <span style="font-size:0.9rem;font-weight:700;color:#e8f5e2;font-family:'Syne',sans-serif">{vix_rep if isinstance(vix_rep, str) else f'{vix_rep:.1f}'}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <span style="font-size:0.75rem;color:#4a6741;font-family:'IBM Plex Mono',monospace">Fear & Greed</span>
                    <span style="font-size:0.9rem;font-weight:700;color:{color_fg};font-family:'Syne',sans-serif">{fg}/100</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Distribución capital
            st.markdown('<div class="section-label">Distribución del capital</div>', unsafe_allow_html=True)
            dist    = analisis.get("distribucion_capital", {})
            en_ops  = dist.get("en_operaciones", 0)
            en_caja = dist.get("en_caja", 100)
            fig_pie = go.Figure(go.Pie(
                values=[en_ops, en_caja],
                labels=["En operaciones", "En caja"],
                hole=0.6,
                marker_colors=["#7bc67e", "#1e2a1e"],
                textinfo="none",
                hovertemplate="%{label}: %{value}%<extra></extra>"
            ))
            fig_pie.update_layout(
                height=180, margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor="#080f08", plot_bgcolor="#080f08",
                showlegend=True,
                legend=dict(font=dict(size=10, color="#4a6741"), bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Aprendizaje
            st.markdown('<div class="section-label">Aprendizaje del día</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="learn-box">{analisis.get("aprendizaje_del_dia","—")}</div>', unsafe_allow_html=True)

            alerta = analisis.get("alerta_critica")
            if alerta and alerta != "null":
                st.markdown(f"""
                <div style="background:#2f1a0d;border:1px solid #4a2d1a;border-radius:8px;padding:1rem;margin-top:1rem">
                    <div style="font-size:0.7rem;color:#e07040;font-family:'IBM Plex Mono',monospace;margin-bottom:4px">🚨 ALERTA CRÍTICA</div>
                    <div style="font-size:0.85rem;color:#e8c8a0">{alerta}</div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 3 — OPERACIONES
# ══════════════════════════════════════════════════════
with tab3:
    ops = historial.get("operaciones", [])
    if not ops:
        st.markdown('<div class="empty-state">Sin operaciones todavía.<br>Aparecerán aquí cuando el agente haga su primera recomendación.</div>', unsafe_allow_html=True)
    else:
        col_op1, col_op2 = st.columns([3, 2])

        with col_op1:
            abiertas = [o for o in ops if o.get("estado") == "abierta"]
            st.markdown(f'<div class="section-label">Posiciones abiertas ({len(abiertas)})</div>', unsafe_allow_html=True)
            if abiertas:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                for op in abiertas:
                    entrada  = op.get("precio_entrada", 0)
                    objetivo = op.get("precio_objetivo", 0)
                    stop     = op.get("stop_loss", 0)
                    p_actual, _ = precio_actual(op.get("ticker", ""))
                    ganancia_viva = ((p_actual - entrada) / entrada * 100) if p_actual else 0
                    color_viva = "#7bc67e" if ganancia_viva >= 0 else "#e07070"
                    st.markdown(f"""
                    <div class="op-row">
                        <div>
                            <div class="op-ticker">{op.get('ticker','')} <span class="badge b-open">ABIERTA</span></div>
                            <div class="op-detail">entrada ${entrada:.2f} · obj ${objetivo:.2f} · stop ${stop:.2f}</div>
                            <div class="op-detail">{op.get('cantidad',0)} acciones · ${op.get('capital_invertido',0):,.0f} invertidos · {op.get('confianza','')}</div>
                        </div>
                        <div style="text-align:right">
                            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:{color_viva}">{ganancia_viva:+.2f}%</div>
                            <div class="op-detail">{op.get('fecha_entrada','')[:10]}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state" style="padding:1.5rem">Sin posiciones abiertas</div>', unsafe_allow_html=True)

            cerradas = [o for o in ops if o.get("estado","").startswith("cerrada")]
            st.markdown(f'<div class="section-label" style="margin-top:1rem">Historial ({len(cerradas)})</div>', unsafe_allow_html=True)
            if cerradas:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                for op in reversed(cerradas[-10:]):
                    estado = op.get("estado","")
                    badge  = "b-win" if "ganancia" in estado else "b-loss"
                    label  = "GANANCIA" if "ganancia" in estado else "STOP-LOSS"
                    res    = op.get("resultado_usd", 0)
                    res_pct = op.get("resultado_pct", 0)
                    color  = "#7bc67e" if res >= 0 else "#e07070"
                    st.markdown(f"""
                    <div class="op-row">
                        <div>
                            <div class="op-ticker">{op.get('ticker','')} <span class="badge {badge}">{label}</span></div>
                            <div class="op-detail">entrada ${op.get('precio_entrada',0):.2f} → salida ${op.get('precio_salida',0):.2f}</div>
                        </div>
                        <div style="text-align:right;font-family:'IBM Plex Mono',monospace">
                            <div style="color:{color};font-weight:600">${res:+,.2f}</div>
                            <div class="op-detail">{res_pct:+.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with col_op2:
            cerradas = [o for o in ops if o.get("estado","").startswith("cerrada")]
            if cerradas:
                st.markdown('<div class="section-label">Resultado de operaciones</div>', unsafe_allow_html=True)
                ganadoras = len([o for o in cerradas if o.get("resultado_usd",0) > 0])
                perdedoras = len(cerradas) - ganadoras
                fig_d = go.Figure(go.Pie(
                    values=[ganadoras, perdedoras],
                    labels=["Ganadoras", "Perdedoras"],
                    hole=0.6,
                    marker_colors=["#7bc67e", "#e07070"],
                    textinfo="none"
                ))
                fig_d.update_layout(
                    height=220, margin=dict(t=0,b=0,l=0,r=0),
                    paper_bgcolor="#080f08", plot_bgcolor="#080f08",
                    showlegend=True,
                    legend=dict(font=dict(size=10, color="#4a6741"), bgcolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig_d, use_container_width=True)

# ══════════════════════════════════════════════════════
# TAB 4 — PERFORMANCE
# ══════════════════════════════════════════════════════
with tab4:
    if len(reportes) < 2:
        st.markdown('<div class="empty-state">Necesitas al menos 2 días de datos para ver la curva.<br>Corre el agente cada día.</div>', unsafe_allow_html=True)
    else:
        fechas    = [r.get("fecha","")[:10] for r in reportes]
        capital_ev = []
        acum = 0
        for r in reportes:
            ops_dia = [o for o in historial.get("operaciones",[]) if o.get("fecha_salida","")[:10] == r.get("fecha","")[:10]]
            acum += sum(o.get("resultado_usd",0) for o in ops_dia)
            capital_ev.append(round(CAPITAL_INICIAL + acum, 2))

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=fechas, y=capital_ev,
            mode="lines+markers",
            line=dict(color="#7bc67e", width=2.5),
            marker=dict(size=6, color="#7bc67e"),
            fill="tozeroy",
            fillcolor="rgba(123,198,126,0.06)",
            hovertemplate="Fecha: %{x}<br>Capital: $%{y:,.2f}<extra></extra>"
        ))
        fig_line.add_hline(y=CAPITAL_INICIAL, line_dash="dot", line_color="#1e2a1e",
                           annotation_text="Capital inicial", annotation_font_color="#4a6741")
        fig_line.update_layout(
            title=dict(text="Evolución del portafolio", font=dict(color="#4a6741", family="IBM Plex Mono", size=12)),
            height=350, margin=dict(t=40,b=20,l=10,r=10),
            paper_bgcolor="#080f08", plot_bgcolor="#080f08",
            xaxis=dict(showgrid=False, tickfont=dict(color="#4a6741")),
            yaxis=dict(showgrid=True, gridcolor="#0d1a0d", tickformat="$,.0f", tickfont=dict(color="#4a6741")),
            font=dict(family="IBM Plex Mono", color="#4a6741")
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # VIX y Fear&Greed histórico
        if any("vix" in r for r in reportes):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.markdown('<div class="section-label">VIX histórico</div>', unsafe_allow_html=True)
                vix_vals = [r.get("vix", None) for r in reportes]
                vix_fechas = [r.get("fecha","")[:10] for r in reportes]
                fig_vix = go.Figure(go.Scatter(
                    x=vix_fechas, y=vix_vals,
                    line=dict(color="#e07070", width=2),
                    fill="tozeroy", fillcolor="rgba(224,112,112,0.06)"
                ))
                fig_vix.add_hline(y=30, line_dash="dot", line_color="#e07070", line_width=1)
                fig_vix.add_hline(y=20, line_dash="dot", line_color="#f0c040", line_width=1)
                fig_vix.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10),
                                      paper_bgcolor="#080f08", plot_bgcolor="#080f08",
                                      xaxis=dict(showgrid=False, tickfont=dict(color="#4a6741", size=9)),
                                      yaxis=dict(showgrid=True, gridcolor="#0d1a0d", tickfont=dict(color="#4a6741", size=9)))
                st.plotly_chart(fig_vix, use_container_width=True)
            with col_v2:
                st.markdown('<div class="section-label">Fear & Greed histórico</div>', unsafe_allow_html=True)
                fg_vals   = [r.get("fear_greed", None) for r in reportes]
                fig_fg = go.Figure(go.Scatter(
                    x=vix_fechas, y=fg_vals,
                    line=dict(color="#7bc67e", width=2),
                    fill="tozeroy", fillcolor="rgba(123,198,126,0.06)"
                ))
                fig_fg.add_hline(y=75, line_dash="dot", line_color="#e07070", line_width=1)
                fig_fg.add_hline(y=25, line_dash="dot", line_color="#7bc67e", line_width=1)
                fig_fg.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10),
                                     paper_bgcolor="#080f08", plot_bgcolor="#080f08",
                                     xaxis=dict(showgrid=False, tickfont=dict(color="#4a6741", size=9)),
                                     yaxis=dict(showgrid=True, gridcolor="#0d1a0d", tickfont=dict(color="#4a6741", size=9)))
                st.plotly_chart(fig_fg, use_container_width=True)

# ══════════════════════════════════════════════════════
# TAB 5 — MACRO
# ══════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-label">Indicadores macroeconómicos en tiempo real</div>', unsafe_allow_html=True)

    macro_tickers = {
        "^VIX": ("VIX — Índice del miedo", ""),
        "DX-Y.NYB": ("Dólar (DXY)", ""),
        "GC=F": ("Oro", "$"),
        "CL=F": ("Petróleo WTI", "$"),
        "^TNX": ("Bonos 10Y USA", "%"),
        "^GSPC": ("S&P 500", "$"),
        "BTC-USD": ("Bitcoin", "$"),
        "EURUSD=X": ("EUR/USD", ""),
    }

    cols_macro = st.columns(4)
    for i, (ticker, (nombre, prefijo)) in enumerate(macro_tickers.items()):
        p, c = precio_actual(ticker)
        with cols_macro[i % 4]:
            if p and c is not None:
                color = "#7bc67e" if c >= 0 else "#e07070"
                signo = "+" if c >= 0 else ""
                st.markdown(f"""
                <div class="macro-item" style="margin-bottom:10px">
                    <div class="macro-name">{nombre}</div>
                    <div class="macro-val">{prefijo}{p:,.2f}</div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:{color};margin-top:2px">{signo}{c:.2f}% hoy</div>
                </div>
                """, unsafe_allow_html=True)

    # Correlaciones
    st.markdown('<div class="section-label" style="margin-top:1.5rem">Correlaciones clave a recordar</div>', unsafe_allow_html=True)
    correlaciones = [
        ("🟡 Oro sube", "→ mercado asustado → reducir exposición"),
        ("📈 Bonos suben", "→ tasas bajan → acciones pueden subir"),
        ("💵 Dólar fuerte", "→ Bitcoin y emergentes caen"),
        ("😱 VIX > 30", "→ pánico → posible oportunidad de compra"),
        ("🤑 Fear&Greed > 75", "→ euforia → considerar tomar ganancias"),
        ("📉 S&P 500 baja", "→ no pelear contra la marea, ser conservador"),
    ]
    cols_corr = st.columns(2)
    for i, (causa, efecto) in enumerate(correlaciones):
        with cols_corr[i % 2]:
            st.markdown(f"""
            <div style="background:#0d1a0d;border:1px solid #1e2a1e;border-radius:8px;padding:12px;margin-bottom:8px">
                <div style="font-size:0.85rem;font-weight:600;color:#e8f5e2;font-family:'Syne',sans-serif">{causa}</div>
                <div style="font-size:0.8rem;color:#4a6741;font-family:'IBM Plex Mono',monospace;margin-top:4px">{efecto}</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 6 — CONFIG
# ══════════════════════════════════════════════════════
with tab6:
    col_cfg1, col_cfg2 = st.columns(2)

    with col_cfg1:
        st.markdown('<div class="section-label">Keys necesarias</div>', unsafe_allow_html=True)
        keys_info = [
            ("Anthropic API Key", "console.anthropic.com", "~$20 USD", "El cerebro del agente"),
            ("NewsAPI Key",       "newsapi.org",           "Gratis",   "Noticias en tiempo real"),
            ("Alpaca API Key",    "alpaca.markets",        "Gratis",   "Broker paper/real trading"),
            ("Telegram Bot",      "@BotFather en Telegram","Gratis",   "Alertas instantáneas"),
        ]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for nombre, url, costo, desc in keys_info:
            badge_color = "#2f1a1a" if costo != "Gratis" else "#0d1a0d"
            badge_text_color = "#e07070" if costo != "Gratis" else "#7bc67e"
            st.markdown(f"""
            <div class="op-row">
                <div>
                    <div class="op-ticker">{nombre}</div>
                    <div class="op-detail">{url} · {desc}</div>
                </div>
                <div style="background:{badge_color};color:{badge_text_color};font-family:'IBM Plex Mono',monospace;font-size:0.7rem;padding:3px 10px;border-radius:100px">{costo}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:1rem">Parámetros del sistema</div>', unsafe_allow_html=True)
        params = [
            ("Capital inicial", f"${CAPITAL_INICIAL:,} USD"),
            ("Mercado",         "Acciones USA · Cripto · Global"),
            ("Acciones",        "10 del S&P 500"),
            ("Estrategia",      "Swing trading (2–7 días)"),
            ("Modelo IA",       "Claude Sonnet 4"),
            ("Agentes",         "Macro · News · Technical · Fundamental · Sentiment · Risk · CEO"),
            ("Alertas",         "Telegram + Email"),
            ("Broker",          "Alpaca (paper/real)"),
        ]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for k, v in params:
            st.markdown(f"""
            <div class="op-row">
                <div class="op-detail">{k}</div>
                <div style="font-size:0.8rem;color:#8aab8a;font-family:'IBM Plex Mono',monospace;text-align:right">{v}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cfg2:
        st.markdown('<div class="section-label">Próximas mejoras</div>', unsafe_allow_html=True)
        mejoras = [
            ("🔔", "Alertas precio en tiempo real"),
            ("📊", "Backtesting histórico"),
            ("🤖", "Extended Thinking para CEO Agent"),
            ("📰", "Análisis de sentimiento en noticias"),
            ("💹", "Soporte cripto completo"),
            ("🌎", "Mercados latinoamericanos"),
            ("📱", "App móvil nativa"),
            ("👥", "Multi-usuario con login"),
        ]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for icono, mejora in mejoras:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #1e2a1e;font-size:0.82rem;color:#6b8c6b">
                {icono} {mejora}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:1rem">Estructura de archivos</div>', unsafe_allow_html=True)
        st.code("""
investment-ai-agent/
├── investment_agent_v2.py  ← agente completo
├── dashboard_v2.py         ← este dashboard
├── requirements.txt        ← dependencias
├── historial_v2.json       ← memoria del agente
└── .streamlit/
    └── secrets.toml        ← API keys (no subir)
        """, language="bash")

# Footer
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem;font-size:0.7rem;color:#1e2a1e;border-top:1px solid #1e2a1e;margin-top:2rem;font-family:'IBM Plex Mono',monospace">
    Investment AI Agent v2.0 · Paper trading · Solo con fines educativos
</div>
""", unsafe_allow_html=True)
