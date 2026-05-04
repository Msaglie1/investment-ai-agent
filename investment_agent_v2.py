"""
╔══════════════════════════════════════════════════════════════╗
║         INVESTMENT AI AGENT v2.0 — SISTEMA COMPLETO         ║
║                                                              ║
║  Agentes: Macro + News + Technical + Fundamental +           ║
║           Sentiment + Risk + CEO                             ║
║  Modos:   Paper Trading | Dinero Real (Alpaca)               ║
║  Alertas: Telegram + Email                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import anthropic
import yfinance as yf
import pandas as pd
import requests
import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================
# ⚙️  CONFIGURACIÓN — COMPLETA TODOS LOS CAMPOS
# ============================================================

# --- Anthropic (obligatorio) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# --- Modo de operación ---
# "paper"  → simulado, sin dinero real
# "real"   → conectado a Alpaca con dinero real
MODO = "paper"

# --- Alpaca (broker) ---
ALPACA_API_KEY    = "TU_ALPACA_API_KEY"
ALPACA_SECRET_KEY = "TU_ALPACA_SECRET_KEY"
# URLs — no tocar
ALPACA_URL_PAPER = "https://paper-api.alpaca.markets"
ALPACA_URL_REAL  = "https://api.alpaca.markets"
ALPACA_URL = ALPACA_URL_PAPER if MODO == "paper" else ALPACA_URL_REAL

# --- NewsAPI (noticias en tiempo real) ---
NEWS_API_KEY = "TU_NEWS_API_KEY"  # gratis en newsapi.org

# --- Telegram (alertas instantáneas) ---
TELEGRAM_TOKEN   = "TU_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "TU_TELEGRAM_CHAT_ID"

# --- Email (reporte diario) ---
EMAIL_REMITENTE   = "tu@gmail.com"
EMAIL_CONTRASENA  = "tu_contrasena_app"   # contraseña de app Gmail
EMAIL_DESTINATARIO = "tu@gmail.com"

# --- Portafolio ---
CAPITAL_USD       = 10500
ARCHIVO_HISTORIAL = "historial_v2.json"

# --- Acciones a monitorear ---
ACCIONES = {
    "AAPL":  "Apple",
    "MSFT":  "Microsoft",
    "GOOGL": "Google",
    "AMZN":  "Amazon",
    "NVDA":  "Nvidia",
    "META":  "Meta",
    "TSLA":  "Tesla",
    "JPM":   "JPMorgan",
    "JNJ":   "Johnson & Johnson",
    "BRK-B": "Berkshire Hathaway"
}

# ============================================================
# 💾  MEMORIA
# ============================================================
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"operaciones": [], "reportes": [], "aprendizajes": []}

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

# ============================================================
# 📲  ALERTAS TELEGRAM
# ============================================================
def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "TU_TELEGRAM_BOT_TOKEN":
        print("⚠️  Telegram no configurado — saltando alerta")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }, timeout=10)
        print("📲 Alerta Telegram enviada")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

# ============================================================
# 📧  EMAIL DIARIO
# ============================================================
def enviar_email(asunto, cuerpo):
    if not EMAIL_REMITENTE or EMAIL_REMITENTE == "tu@gmail.com":
        print("⚠️  Email no configurado — saltando")
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_REMITENTE
        msg["To"]      = EMAIL_DESTINATARIO
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_REMITENTE, EMAIL_CONTRASENA)
            server.send_message(msg)
        print("📧 Email enviado")
    except Exception as e:
        print(f"❌ Error email: {e}")

# ============================================================
# 🌍  MACRO AGENT — Fed, inflación, dólar, VIX
# ============================================================
def macro_agent():
    print("\n🌍 Macro Agent analizando...")
    datos = {}

    try:
        # VIX — índice del miedo
        vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)
        datos["vix"] = float(vix["Close"].iloc[-1])
        datos["vix_5d_ago"] = float(vix["Close"].iloc[-5]) if len(vix) >= 5 else datos["vix"]

        # DXY — índice del dólar
        dxy = yf.download("DX-Y.NYB", period="5d", interval="1d", progress=False)
        if isinstance(dxy.columns, pd.MultiIndex):
            dxy.columns = dxy.columns.get_level_values(0)
        datos["dolar"] = float(dxy["Close"].iloc[-1]) if not dxy.empty else 103.0

        # S&P 500 — tendencia general
        sp500 = yf.download("^GSPC", period="30d", interval="1d", progress=False)
        if isinstance(sp500.columns, pd.MultiIndex):
            sp500.columns = sp500.columns.get_level_values(0)
        sp_actual   = float(sp500["Close"].iloc[-1])
        sp_hace_30d = float(sp500["Close"].iloc[0])
        datos["sp500_tendencia_30d"] = round(((sp_actual - sp_hace_30d) / sp_hace_30d) * 100, 2)
        datos["sp500_precio"]        = sp_actual

        # Oro — activo refugio
        oro = yf.download("GC=F", period="5d", interval="1d", progress=False)
        if isinstance(oro.columns, pd.MultiIndex):
            oro.columns = oro.columns.get_level_values(0)
        datos["oro"] = float(oro["Close"].iloc[-1]) if not oro.empty else 2300.0

        # Bonos del tesoro 10Y
        bonos = yf.download("^TNX", period="5d", interval="1d", progress=False)
        if isinstance(bonos.columns, pd.MultiIndex):
            bonos.columns = bonos.columns.get_level_values(0)
        datos["bonos_10y"] = float(bonos["Close"].iloc[-1]) if not bonos.empty else 4.3

        # Petróleo
        petroleo = yf.download("CL=F", period="5d", interval="1d", progress=False)
        if isinstance(petroleo.columns, pd.MultiIndex):
            petroleo.columns = petroleo.columns.get_level_values(0)
        datos["petroleo"] = float(petroleo["Close"].iloc[-1]) if not petroleo.empty else 75.0

        # Estacionalidad
        mes = datetime.now().month
        datos["estacionalidad"] = "DESFAVORABLE (mayo-octubre históricamente débil)" if 5 <= mes <= 10 else "FAVORABLE (noviembre-abril históricamente fuerte)"

        # Interpretaciones
        datos["vix_nivel"]   = "PÁNICO" if datos["vix"] > 30 else "ELEVADO" if datos["vix"] > 20 else "NORMAL"
        datos["dolar_nivel"] = "FUERTE" if datos["dolar"] > 105 else "DÉBIL" if datos["dolar"] < 100 else "NEUTRO"

    except Exception as e:
        print(f"  ⚠️ Error en macro: {e}")

    resumen = f"""
=== MACRO AGENT ===
VIX (miedo):          {datos.get('vix', 'N/A'):.1f} — {datos.get('vix_nivel', 'N/A')}
Dólar (DXY):          {datos.get('dolar', 'N/A'):.1f} — {datos.get('dolar_nivel', 'N/A')}
S&P 500 tendencia 30d: {datos.get('sp500_tendencia_30d', 'N/A'):+.2f}%
Oro:                  ${datos.get('oro', 'N/A'):,.0f}
Bonos 10Y:            {datos.get('bonos_10y', 'N/A'):.2f}%
Petróleo:             ${datos.get('petroleo', 'N/A'):.1f}
Estacionalidad:       {datos.get('estacionalidad', 'N/A')}

Correlaciones clave:
- Oro subiendo = mercado asustado = cautela
- Bonos subiendo = tasas bajando = acciones pueden subir
- Dólar fuerte = Bitcoin y emergentes caen
- VIX > 30 = pánico = posible oportunidad de compra
"""
    print("  ✅ Macro completado")
    return resumen, datos

# ============================================================
# 📰  NEWS AGENT — noticias en tiempo real
# ============================================================
def news_agent(tickers):
    print("\n📰 News Agent buscando noticias...")
    noticias_por_accion = {}

    if not NEWS_API_KEY or NEWS_API_KEY == "TU_NEWS_API_KEY":
        print("  ⚠️ NewsAPI no configurada — usando noticias básicas")
        return "=== NEWS AGENT ===\nNewsAPI no configurada. Agrega tu key en la configuración.\n", {}

    try:
        ayer = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

        # Noticias generales de mercado
        url_mercado = (
            f"https://newsapi.org/v2/everything?"
            f"q=stock+market+NYSE+SP500&"
            f"from={ayer}&sortBy=publishedAt&"
            f"language=en&pageSize=5&"
            f"apiKey={NEWS_API_KEY}"
        )
        resp = requests.get(url_mercado, timeout=10).json()
        noticias_mercado = [
            f"- {a['title'][:100]}"
            for a in resp.get("articles", [])[:5]
        ]

        # Noticias por acción
        for ticker in list(tickers.keys())[:5]:
            empresa = tickers[ticker]
            url = (
                f"https://newsapi.org/v2/everything?"
                f"q={empresa}+stock&"
                f"from={ayer}&sortBy=publishedAt&"
                f"language=en&pageSize=3&"
                f"apiKey={NEWS_API_KEY}"
            )
            resp = requests.get(url, timeout=10).json()
            articulos = resp.get("articles", [])[:3]
            if articulos:
                noticias_por_accion[ticker] = [a["title"][:100] for a in articulos]

    except Exception as e:
        print(f"  ⚠️ Error NewsAPI: {e}")
        noticias_mercado = ["Error obteniendo noticias"]

    resumen = "=== NEWS AGENT ===\n"
    resumen += "NOTICIAS GENERALES DE MERCADO:\n"
    resumen += "\n".join(noticias_mercado) + "\n\n"
    resumen += "NOTICIAS POR ACCIÓN:\n"
    for ticker, nots in noticias_por_accion.items():
        resumen += f"\n{ticker}:\n"
        for n in nots:
            resumen += f"  - {n}\n"

    print("  ✅ Noticias completadas")
    return resumen, noticias_por_accion

# ============================================================
# 📊  TECHNICAL AGENT — indicadores técnicos
# ============================================================
def technical_agent(tickers):
    print("\n📊 Technical Agent calculando indicadores...")
    datos_tecnicos = {}
    resumen = "=== TECHNICAL AGENT ===\n"

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="90d", interval="1d", progress=False)
            if df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close  = df["Close"]
            volume = df["Volume"]

            # RSI
            delta = close.diff()
            gain  = delta.where(delta > 0, 0).rolling(14).mean()
            loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs    = gain / loss
            rsi   = float((100 - (100 / (1 + rs))).iloc[-1])

            # Medias móviles
            ma20 = float(close.rolling(20).mean().iloc[-1])
            ma50 = float(close.rolling(50).mean().iloc[-1])

            # MACD
            ema12      = close.ewm(span=12, adjust=False).mean()
            ema26      = close.ewm(span=26, adjust=False).mean()
            macd       = float((ema12 - ema26).iloc[-1])
            macd_signal = float((ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1])

            # Bollinger Bands
            bb_mid   = float(close.rolling(20).mean().iloc[-1])
            bb_std   = float(close.rolling(20).std().iloc[-1])
            bb_upper = bb_mid + 2 * bb_std
            bb_lower = bb_mid - 2 * bb_std

            # Precio y volumen
            precio       = float(close.iloc[-1])
            precio_5d    = float(close.iloc[-6]) if len(close) >= 6 else precio
            precio_20d   = float(close.iloc[-21]) if len(close) >= 21 else precio
            var_5d       = ((precio - precio_5d) / precio_5d) * 100
            var_20d      = ((precio - precio_20d) / precio_20d) * 100
            vol_hoy      = float(volume.iloc[-1])
            vol_prom     = float(volume.rolling(20).mean().iloc[-1])
            vol_ratio    = vol_hoy / vol_prom if vol_prom > 0 else 1

            # Soporte y resistencia (simple)
            soporte     = float(close.rolling(20).min().iloc[-1])
            resistencia = float(close.rolling(20).max().iloc[-1])

            datos_tecnicos[ticker] = {
                "precio": precio, "rsi": rsi, "ma20": ma20, "ma50": ma50,
                "macd": macd, "macd_signal": macd_signal,
                "bb_upper": bb_upper, "bb_lower": bb_lower,
                "var_5d": var_5d, "var_20d": var_20d, "vol_ratio": vol_ratio,
                "soporte": soporte, "resistencia": resistencia
            }

            rsi_label  = "SOBREVENDIDO 🔥" if rsi < 30 else "SOBRECOMPRADO ⚠️" if rsi > 70 else "neutral"
            macd_label = "alcista ↑" if macd > macd_signal else "bajista ↓"
            bb_label   = "cerca techo" if precio > bb_upper * 0.97 else "cerca piso 🔥" if precio < bb_lower * 1.03 else "zona media"
            vol_label  = f"{vol_ratio:.1f}x promedio {'📈 alto' if vol_ratio > 1.5 else ''}"

            resumen += f"""
{ticker} (${precio:.2f}):
  Variación:  5d {var_5d:+.1f}% | 20d {var_20d:+.1f}%
  RSI(14):    {rsi:.1f} — {rsi_label}
  MA20/50:    ${ma20:.1f} / ${ma50:.1f} — precio {"SOBRE" if precio > ma20 else "BAJO"} MA20
  MACD:       {macd:.3f} vs señal {macd_signal:.3f} — {macd_label}
  Bollinger:  ${bb_lower:.1f} | ${bb_upper:.1f} — {bb_label}
  Soporte:    ${soporte:.1f} | Resistencia: ${resistencia:.1f}
  Volumen:    {vol_label}
"""
        except Exception as e:
            print(f"  ⚠️ Error {ticker}: {e}")

    print("  ✅ Técnico completado")
    return resumen, datos_tecnicos

# ============================================================
# 🏢  FUNDAMENTAL AGENT — earnings, P/E, deuda
# ============================================================
def fundamental_agent(tickers):
    print("\n🏢 Fundamental Agent analizando empresas...")
    resumen = "=== FUNDAMENTAL AGENT ===\n"

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            pe          = info.get("trailingPE", "N/A")
            eps         = info.get("trailingEps", "N/A")
            deuda       = info.get("totalDebt", 0)
            caja        = info.get("totalCash", 0)
            margen      = info.get("profitMargins", 0)
            crecimiento = info.get("revenueGrowth", 0)
            beta        = info.get("beta", 1)
            dividendo   = info.get("dividendYield", 0)
            sector      = info.get("sector", "N/A")
            cap         = info.get("marketCap", 0)

            deuda_neta = (deuda - caja) / 1e9 if deuda and caja else 0

            resumen += f"""
{ticker} ({sector}):
  P/E ratio:      {pe if isinstance(pe, str) else f'{pe:.1f}'}
  EPS:            ${eps if isinstance(eps, str) else f'{eps:.2f}'}
  Margen neto:    {margen*100:.1f}% if isinstance(margen, float) else N/A
  Crecimiento:    {crecimiento*100:.1f}% if isinstance(crecimiento, float) else N/A
  Deuda neta:     ${deuda_neta:.1f}B
  Beta:           {beta:.2f} ({'alta volatilidad' if isinstance(beta, float) and beta > 1.5 else 'baja volatilidad' if isinstance(beta, float) and beta < 0.8 else 'normal'})
  Dividendo:      {dividendo*100:.2f}% if isinstance(dividendo, float) else N/A
  Market cap:     ${cap/1e9:.0f}B
"""
        except Exception as e:
            resumen += f"\n{ticker}: Error obteniendo datos ({e})\n"

    print("  ✅ Fundamentales completados")
    return resumen

# ============================================================
# 😰  SENTIMENT AGENT — Fear&Greed, VIX, short interest
# ============================================================
def sentiment_agent(vix):
    print("\n😰 Sentiment Agent midiendo sentimiento...")

    # Fear & Greed aproximado basado en VIX
    if vix > 40:
        fear_greed = 10
        label = "MIEDO EXTREMO 😱"
    elif vix > 30:
        fear_greed = 25
        label = "MIEDO 😰"
    elif vix > 20:
        fear_greed = 45
        label = "NEUTRO 😐"
    elif vix > 15:
        fear_greed = 65
        label = "CODICIA 😏"
    else:
        fear_greed = 80
        label = "CODICIA EXTREMA 🤑"

    # Interpretación para el agente
    if fear_greed < 25:
        estrategia = "Oportunidad de compra — mercado en pánico, históricamente buen momento para entrar"
    elif fear_greed > 75:
        estrategia = "Precaución — mercado eufórico, históricamente momento de tomar ganancias"
    else:
        estrategia = "Mercado equilibrado — seguir señales técnicas normalmente"

    resumen = f"""
=== SENTIMENT AGENT ===
Fear & Greed Index: {fear_greed}/100 — {label}
VIX actual:         {vix:.1f}
Estrategia:         {estrategia}

Regla de Warren Buffett:
"Sé temeroso cuando otros son codiciosos,
 sé codicioso cuando otros son temerosos"
→ Fear&Greed {fear_greed} sugiere: {"COMPRAR" if fear_greed < 30 else "VENDER PARCIALMENTE" if fear_greed > 75 else "OPERAR NORMAL"}
"""

    print("  ✅ Sentimiento completado")
    return resumen, fear_greed

# ============================================================
# ⚠️  RISK AGENT — riesgo del portafolio
# ============================================================
def risk_agent(historial, datos_tecnicos, vix, fear_greed):
    print("\n⚠️  Risk Agent evaluando riesgo...")

    ops_abiertas = [o for o in historial.get("operaciones", []) if o.get("estado") == "abierta"]
    capital_en_riesgo = sum(o.get("capital_invertido", 0) for o in ops_abiertas)
    pct_en_riesgo = (capital_en_riesgo / CAPITAL_USD) * 100 if CAPITAL_USD > 0 else 0

    # Concentración por sector (simplificado)
    sectores = {}
    for op in ops_abiertas:
        ticker = op.get("ticker", "")
        sector = "Tech" if ticker in ["AAPL", "MSFT", "GOOGL", "NVDA", "META"] else "Other"
        sectores[sector] = sectores.get(sector, 0) + op.get("capital_invertido", 0)

    # Nivel de riesgo
    if vix > 30 or fear_greed < 20:
        riesgo_nivel = "ALTO"
        max_capital  = 20
    elif vix > 20 or fear_greed < 35:
        riesgo_nivel = "MEDIO"
        max_capital  = 40
    else:
        riesgo_nivel = "BAJO"
        max_capital  = 60

    resumen = f"""
=== RISK AGENT ===
Capital en riesgo:    ${capital_en_riesgo:,.0f} ({pct_en_riesgo:.1f}%)
Capital disponible:   ${CAPITAL_USD - capital_en_riesgo:,.0f}
Posiciones abiertas:  {len(ops_abiertas)}
Nivel de riesgo:      {riesgo_nivel}
Max capital a usar:   {max_capital}% del portafolio hoy

Reglas de riesgo activas:
- Máximo 20% del capital en una sola acción
- Stop-loss obligatorio en cada operación (6-8%)
- Si VIX > 30: reducir exposición al 20%
- No operar contra la tendencia del S&P 500
- Diversificar sectores (máximo 40% en tech)
"""

    print("  ✅ Riesgo completado")
    return resumen, riesgo_nivel, max_capital

# ============================================================
# 🧠  CEO AGENT — decisión final
# ============================================================
def ceo_agent(macro, noticias, tecnico, fundamental, sentimiento, riesgo, historial):
    print("\n🧠 CEO Agent tomando decisión final...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Contexto histórico
    contexto = ""
    if historial["reportes"]:
        ultimos = historial["reportes"][-5:]
        contexto = "\nHISTORIAL RECIENTE:\n"
        for r in ultimos:
            contexto += f"- {r.get('fecha','')}: {r.get('resumen_breve','')}\n"

    if historial.get("aprendizajes"):
        contexto += "\nAPRENDIZAJES ACUMULADOS:\n"
        for a in historial["aprendizajes"][-5:]:
            contexto += f"- {a}\n"

    ops_abiertas = [o for o in historial.get("operaciones", []) if o.get("estado") == "abierta"]
    if ops_abiertas:
        contexto += "\nPOSICIONES ABIERTAS ACTUALMENTE:\n"
        for op in ops_abiertas:
            contexto += f"- {op['ticker']}: entrada ${op['precio_entrada']:.2f}, objetivo ${op['precio_objetivo']:.2f}, stop ${op['stop_loss']:.2f}\n"

    prompt = f"""Eres el CEO de una empresa de inversión con IA. Tu trabajo es tomar decisiones racionales de inversión basadas en múltiples fuentes de datos.

CAPITAL TOTAL: ${CAPITAL_USD:,} USD
MODO: {MODO.upper()} TRADING
FECHA: {datetime.now().strftime('%d/%m/%Y %H:%M')}
{contexto}

REPORTES DE TUS AGENTES ESPECIALIZADOS:

{macro}

{noticias}

{tecnico}

{fundamental}

{sentimiento}

{riesgo}

INSTRUCCIONES:
1. Analiza TODAS las variables en conjunto — no decidas solo con técnico o solo con noticias
2. Busca CONFLUENCIA — las mejores señales tienen múltiples factores alineados
3. El contexto macro manda — si el mercado está en pánico, sé conservador
4. Aprende del historial — no repitas errores pasados
5. Justifica cada decisión con datos concretos

Responde SOLO con este JSON exacto:
{{
  "resumen_mercado": "descripción del estado actual en 2 oraciones",
  "nivel_riesgo": "BAJO|MEDIO|ALTO",
  "señales_compra": [
    {{
      "ticker": "XXXX",
      "precio_entrada_sugerido": 000.00,
      "precio_objetivo": 000.00,
      "stop_loss": 000.00,
      "capital_asignar_pct": 00,
      "confianza": "ALTA|MEDIA|BAJA",
      "justificacion": "explicación detallada con los factores que convergen",
      "factores": ["RSI sobrevendido", "noticia positiva", "macro favorable"]
    }}
  ],
  "señales_venta": [
    {{
      "ticker": "XXXX",
      "razon": "explicación detallada"
    }}
  ],
  "acciones_mantener": ["XXXX"],
  "distribucion_capital": {{
    "en_operaciones": 00,
    "en_caja": 00,
    "nota": "estrategia del día"
  }},
  "aprendizaje_del_dia": "patrón o insight importante para recordar",
  "alerta_critica": "null o descripción de una alerta urgente"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    resultado = json.loads(raw)
    print("  ✅ CEO completó la decisión")
    return resultado

# ============================================================
# 🏦  ALPACA — ejecutar órdenes en broker
# ============================================================
def alpaca_headers():
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        "Content-Type": "application/json"
    }

def alpaca_obtener_precio(ticker):
    try:
        url = f"{ALPACA_URL}/v2/stocks/{ticker}/quotes/latest"
        resp = requests.get(url, headers=alpaca_headers(), timeout=10).json()
        return float(resp["quote"]["ap"])  # ask price
    except:
        return None

def alpaca_enviar_orden(ticker, cantidad, tipo="buy"):
    if ALPACA_API_KEY == "TU_ALPACA_API_KEY":
        print(f"  ⚠️ Alpaca no configurado — simulando orden {tipo} {ticker}")
        return {"status": "simulada"}
    try:
        url = f"{ALPACA_URL}/v2/orders"
        orden = {
            "symbol": ticker,
            "qty": cantidad,
            "side": tipo,
            "type": "market",
            "time_in_force": "day"
        }
        resp = requests.post(url, headers=alpaca_headers(), json=orden, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"  ❌ Error Alpaca: {e}")
        return None

def alpaca_obtener_posiciones():
    if ALPACA_API_KEY == "TU_ALPACA_API_KEY":
        return []
    try:
        url = f"{ALPACA_URL}/v2/positions"
        resp = requests.get(url, headers=alpaca_headers(), timeout=10)
        return resp.json()
    except:
        return []

# ============================================================
# 💼  EJECUTAR OPERACIONES
# ============================================================
def ejecutar_operaciones(analisis, historial, datos_tecnicos):
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    nuevas_ops = []

    # Registrar compras
    for señal in analisis.get("señales_compra", []):
        ticker  = señal["ticker"]
        precio  = señal["precio_entrada_sugerido"]
        pct     = señal["capital_asignar_pct"] / 100
        capital = CAPITAL_USD * pct
        cantidad = int(capital / precio) if precio > 0 else 0

        if cantidad <= 0:
            continue

        # Ejecutar en Alpaca si está configurado
        if MODO == "real" and ALPACA_API_KEY != "TU_ALPACA_API_KEY":
            resultado_alpaca = alpaca_enviar_orden(ticker, cantidad, "buy")
            print(f"  📤 Orden enviada a Alpaca: {resultado_alpaca}")
        elif MODO == "paper" and ALPACA_API_KEY != "TU_ALPACA_API_KEY":
            resultado_alpaca = alpaca_enviar_orden(ticker, cantidad, "buy")
            print(f"  📤 Orden paper enviada a Alpaca: {resultado_alpaca}")

        op = {
            "id": f"{ticker}_{hoy}",
            "ticker": ticker,
            "tipo": "compra",
            "modo": MODO,
            "fecha_entrada": hoy,
            "precio_entrada": precio,
            "precio_objetivo": señal["precio_objetivo"],
            "stop_loss": señal["stop_loss"],
            "cantidad": cantidad,
            "capital_invertido": round(cantidad * precio, 2),
            "confianza": señal.get("confianza", "MEDIA"),
            "estado": "abierta",
            "justificacion": señal["justificacion"],
            "factores": señal.get("factores", [])
        }
        historial["operaciones"].append(op)
        nuevas_ops.append(op)

    # Revisar stop-loss y targets
    precios_actuales = {t: datos_tecnicos[t]["precio"] for t in datos_tecnicos}
    for op in historial["operaciones"]:
        if op.get("estado") != "abierta":
            continue
        ticker = op["ticker"]
        if ticker not in precios_actuales:
            continue

        precio_actual = precios_actuales[ticker]
        ganancia_pct  = ((precio_actual - op["precio_entrada"]) / op["precio_entrada"]) * 100

        if precio_actual >= op["precio_objetivo"]:
            op["estado"]        = "cerrada_ganancia"
            op["fecha_salida"]  = hoy
            op["precio_salida"] = precio_actual
            op["resultado_pct"] = round(ganancia_pct, 2)
            op["resultado_usd"] = round((precio_actual - op["precio_entrada"]) * op["cantidad"], 2)
            if MODO == "real" and ALPACA_API_KEY != "TU_ALPACA_API_KEY":
                alpaca_enviar_orden(ticker, op["cantidad"], "sell")

        elif precio_actual <= op["stop_loss"]:
            op["estado"]        = "cerrada_stoploss"
            op["fecha_salida"]  = hoy
            op["precio_salida"] = precio_actual
            op["resultado_pct"] = round(ganancia_pct, 2)
            op["resultado_usd"] = round((precio_actual - op["precio_entrada"]) * op["cantidad"], 2)
            if MODO == "real" and ALPACA_API_KEY != "TU_ALPACA_API_KEY":
                alpaca_enviar_orden(ticker, op["cantidad"], "sell")

    return nuevas_ops

# ============================================================
# 📊  PERFORMANCE
# ============================================================
def calcular_performance(historial):
    ops      = historial.get("operaciones", [])
    cerradas = [o for o in ops if o.get("estado", "").startswith("cerrada")]
    ganadoras = [o for o in cerradas if o.get("resultado_usd", 0) > 0]
    ganancia  = sum(o.get("resultado_usd", 0) for o in cerradas)
    win_rate  = (len(ganadoras) / len(cerradas) * 100) if cerradas else 0
    abiertas  = [o for o in ops if o.get("estado") == "abierta"]
    invertido = sum(o.get("capital_invertido", 0) for o in abiertas)

    return {
        "ganancia_total_usd":    round(ganancia, 2),
        "capital_actual":        round(CAPITAL_USD + ganancia, 2),
        "operaciones_cerradas":  len(cerradas),
        "operaciones_ganadoras": len(ganadoras),
        "operaciones_abiertas":  len(abiertas),
        "capital_invertido":     round(invertido, 2),
        "win_rate":              round(win_rate, 1),
    }

# ============================================================
# 📲  FORMATEAR ALERTA TELEGRAM
# ============================================================
def formatear_alerta_telegram(analisis, nuevas_ops, perf):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = f"🤖 <b>Investment AI Agent</b>\n📅 {fecha}\n"
    msg += f"⚠️ Riesgo: <b>{analisis.get('nivel_riesgo','N/A')}</b>\n\n"
    msg += f"🌐 {analisis.get('resumen_mercado','')}\n\n"

    compras = analisis.get("señales_compra", [])
    if compras:
        msg += "✅ <b>SEÑALES DE COMPRA:</b>\n"
        for s in compras:
            msg += (
                f"  <b>{s['ticker']}</b> — entrada ${s['precio_entrada_sugerido']:.2f}\n"
                f"  Objetivo: ${s['precio_objetivo']:.2f} | Stop: ${s['stop_loss']:.2f}\n"
                f"  Confianza: {s.get('confianza','N/A')}\n"
                f"  → {s['justificacion'][:120]}...\n\n"
            )

    ventas = analisis.get("señales_venta", [])
    if ventas:
        msg += "❌ <b>EVITAR:</b>\n"
        for s in ventas:
            msg += f"  <b>{s['ticker']}</b>: {s['razon'][:100]}...\n"

    msg += f"\n📈 <b>Portfolio:</b> ${perf['capital_actual']:,.0f} | Win rate: {perf['win_rate']}%\n"
    msg += f"💡 {analisis.get('aprendizaje_del_dia','')}"

    alerta = analisis.get("alerta_critica")
    if alerta and alerta != "null":
        msg += f"\n\n🚨 <b>ALERTA CRÍTICA:</b> {alerta}"

    return msg

# ============================================================
# 🚀  MAIN
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("   🤖 INVESTMENT AI AGENT v2.0 — SISTEMA COMPLETO")
    print(f"   Modo: {MODO.upper()} TRADING")
    print("=" * 60)

    historial = cargar_historial()

    # ── 1. Macro Agent ──────────────────────────────────────
    resumen_macro, datos_macro = macro_agent()
    vix = datos_macro.get("vix", 18)

    # ── 2. News Agent ───────────────────────────────────────
    resumen_noticias, _ = news_agent(ACCIONES)

    # ── 3. Technical Agent ──────────────────────────────────
    resumen_tecnico, datos_tecnicos = technical_agent(ACCIONES)

    # ── 4. Fundamental Agent ────────────────────────────────
    resumen_fundamental = fundamental_agent(ACCIONES)

    # ── 5. Sentiment Agent ──────────────────────────────────
    resumen_sentimiento, fear_greed = sentiment_agent(vix)

    # ── 6. Risk Agent ───────────────────────────────────────
    resumen_riesgo, nivel_riesgo, max_capital = risk_agent(
        historial, datos_tecnicos, vix, fear_greed
    )

    # ── 7. CEO Agent ────────────────────────────────────────
    analisis = ceo_agent(
        resumen_macro, resumen_noticias, resumen_tecnico,
        resumen_fundamental, resumen_sentimiento, resumen_riesgo,
        historial
    )

    # ── 8. Ejecutar operaciones ─────────────────────────────
    nuevas_ops = ejecutar_operaciones(analisis, historial, datos_tecnicos)

    # ── 9. Guardar aprendizaje ──────────────────────────────
    aprendizaje = analisis.get("aprendizaje_del_dia", "")
    if aprendizaje:
        historial["aprendizajes"] = historial.get("aprendizajes", [])
        historial["aprendizajes"].append(f"{datetime.now().strftime('%Y-%m-%d')}: {aprendizaje}")

    # ── 10. Guardar reporte ─────────────────────────────────
    historial["reportes"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "analisis": analisis,
        "resumen_breve": analisis.get("resumen_mercado", ""),
        "nivel_riesgo": nivel_riesgo,
        "vix": vix,
        "fear_greed": fear_greed
    })
    guardar_historial(historial)

    # ── 11. Performance ─────────────────────────────────────
    perf = calcular_performance(historial)

    # ── 12. Mostrar reporte ─────────────────────────────────
    print("\n" + "=" * 60)
    print("📋 REPORTE FINAL DEL CEO")
    print("=" * 60)
    print(f"\n🌐 Mercado: {analisis.get('resumen_mercado','')}")
    print(f"⚠️  Riesgo:  {analisis.get('nivel_riesgo','')}")
    print(f"😰 Fear&Greed: {fear_greed}/100 | VIX: {vix:.1f}")

    print("\n✅ SEÑALES DE COMPRA:")
    for s in analisis.get("señales_compra", []):
        print(f"   {s['ticker']} ({s.get('confianza','')}) — entrada ${s['precio_entrada_sugerido']} | obj ${s['precio_objetivo']} | stop ${s['stop_loss']}")
        print(f"   → {s['justificacion'][:100]}...")

    print("\n❌ SEÑALES DE VENTA/EVITAR:")
    for s in analisis.get("señales_venta", []):
        print(f"   {s['ticker']}: {s['razon'][:100]}...")

    print(f"\n💡 Aprendizaje: {analisis.get('aprendizaje_del_dia','')}")

    alerta = analisis.get("alerta_critica")
    if alerta and alerta != "null":
        print(f"\n🚨 ALERTA CRÍTICA: {alerta}")

    print(f"\n📈 PORTFOLIO:")
    print(f"   Capital actual:    ${perf['capital_actual']:,.2f} USD")
    print(f"   Ganancia total:    ${perf['ganancia_total_usd']:+,.2f} USD")
    print(f"   Win rate:          {perf['win_rate']}%")
    print(f"   Ops abiertas:      {perf['operaciones_abiertas']}")
    print(f"   Ops cerradas:      {perf['operaciones_cerradas']}")

    if nuevas_ops:
        print(f"\n🚀 NUEVAS OPERACIONES ({len(nuevas_ops)}):")
        for op in nuevas_ops:
            print(f"   {op['modo'].upper()} {op['ticker']}: {op['cantidad']} acciones @ ${op['precio_entrada']:.2f} = ${op['capital_invertido']:,.2f}")

    # ── 13. Alertas ─────────────────────────────────────────
    msg_telegram = formatear_alerta_telegram(analisis, nuevas_ops, perf)
    enviar_telegram(msg_telegram)

    # Email con reporte completo
    enviar_email(
        asunto=f"📈 Investment AI Agent — {datetime.now().strftime('%d/%m/%Y')} — Riesgo {nivel_riesgo}",
        cuerpo=f"<pre>{msg_telegram}</pre>"
    )

    print("\n✅ Todo guardado en historial_v2.json")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
