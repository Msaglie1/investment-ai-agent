import anthropic
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN — CAMBIA ESTO
# ============================================
API_KEY = "TU_API_KEY_DE_ANTHROPIC"   # <-- pega tu API key aquí
CAPITAL_USD = 10500                    # $10 millones CLP ≈ $10.500 USD
ARCHIVO_HISTORIAL = "historial.json"   # memoria del agente

ACCIONES = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Google
    "AMZN",  # Amazon
    "NVDA",  # Nvidia
    "META",  # Meta
    "TSLA",  # Tesla
    "JPM",   # JPMorgan
    "JNJ",   # Johnson & Johnson
    "BRK-B"  # Berkshire Hathaway
]

# ============================================
# MEMORIA: carga y guarda historial
# ============================================
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"operaciones": [], "reportes": []}

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

# ============================================
# PASO 1: Descargar datos del mercado
# ============================================
def obtener_datos(ticker):
    df = yf.download(ticker, period="60d", interval="1d", progress=False)
    if df.empty:
        raise ValueError(f"No se obtuvieron datos para {ticker}")
    return df

# ============================================
# PASO 2: Calcular indicadores técnicos
# ============================================
def calcular_indicadores(df):
    # Aplanar columnas multi-nivel si es necesario
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"]

    # RSI manual (sin librería ta)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Medias móviles
    df["MA20"] = close.rolling(window=20).mean()
    df["MA50"] = close.rolling(window=50).mean()

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df["BB_mid"] = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df["BB_upper"] = df["BB_mid"] + (2 * bb_std)
    df["BB_lower"] = df["BB_mid"] - (2 * bb_std)

    return df

# ============================================
# PASO 3: Resumir datos para Claude
# ============================================
def resumir_accion(ticker, df):
    ultima = df.iloc[-1]

    precio    = float(ultima["Close"])
    rsi       = float(ultima["RSI"])
    ma20      = float(ultima["MA20"])
    ma50      = float(ultima["MA50"])
    macd      = float(ultima["MACD"])
    macd_sig  = float(ultima["MACD_signal"])
    bb_upper  = float(ultima["BB_upper"])
    bb_lower  = float(ultima["BB_lower"])

    precio_5d  = float(df["Close"].iloc[-6])
    precio_20d = float(df["Close"].iloc[-21]) if len(df) >= 21 else precio_5d
    var_5d  = ((precio - precio_5d)  / precio_5d)  * 100
    var_20d = ((precio - precio_20d) / precio_20d) * 100

    volumen_hoy  = float(df["Volume"].iloc[-1])
    volumen_prom = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_ratio    = volumen_hoy / volumen_prom if volumen_prom > 0 else 1

    rsi_label  = "SOBRECOMPRADO ⚠️" if rsi > 70 else "SOBREVENDIDO 🔥" if rsi < 30 else "neutral"
    macd_label = "alcista ↑" if macd > macd_sig else "bajista ↓"

    return f"""
{ticker}:
  Precio actual:  ${precio:.2f}
  Variación 5d:   {var_5d:+.2f}%
  Variación 20d:  {var_20d:+.2f}%
  RSI(14):        {rsi:.1f} — {rsi_label}
  MA20:           ${ma20:.2f}  |  MA50: ${ma50:.2f}
  Precio vs MA20: {"POR ENCIMA ↑" if precio > ma20 else "POR DEBAJO ↓"}
  Precio vs MA50: {"POR ENCIMA ↑" if precio > ma50 else "POR DEBAJO ↓"}
  MACD:           {macd:.3f} vs señal {macd_sig:.3f} — {macd_label}
  Bollinger:      superior ${bb_upper:.2f} | inferior ${bb_lower:.2f}
  Precio en BB:   {"cerca del techo" if precio > bb_upper * 0.97 else "cerca del piso" if precio < bb_lower * 1.03 else "en zona media"}
  Volumen hoy:    {vol_ratio:.1f}x respecto al promedio
"""

# ============================================
# PASO 4: Claude analiza el mercado
# ============================================
def analizar_con_claude(resumen_mercado, historial):
    client = anthropic.Anthropic(api_key=API_KEY)

    # Preparar contexto histórico
    contexto_historico = ""
    if historial["reportes"]:
        ultimos = historial["reportes"][-3:]
        contexto_historico = "\n\nCONTEXTO HISTÓRICO (últimos reportes):\n"
        for r in ultimos:
            contexto_historico += f"- {r['fecha']}: {r['resumen_breve']}\n"

    if historial["operaciones"]:
        contexto_historico += "\nOPERACIONES PAPER TRADING ACTIVAS:\n"
        for op in historial["operaciones"]:
            if op.get("estado") == "abierta":
                contexto_historico += (
                    f"- {op['ticker']}: comprado a ${op['precio_entrada']:.2f}, "
                    f"cantidad {op['cantidad']} acciones\n"
                )

    prompt = f"""Eres el CEO de una empresa de inversión en paper trading. 
Tu objetivo es maximizar retornos gestionando el riesgo de forma inteligente.
Capital total disponible: ${CAPITAL_USD:,} USD
Fecha de análisis: {datetime.now().strftime('%d/%m/%Y %H:%M')}
{contexto_historico}

DATOS TÉCNICOS DEL MERCADO HOY:
{resumen_mercado}

Genera un reporte estructurado en JSON con exactamente este formato:
{{
  "resumen_mercado": "descripción breve del estado general del mercado en 2 oraciones",
  "nivel_riesgo": "BAJO|MEDIO|ALTO",
  "señales_compra": [
    {{
      "ticker": "XXXX",
      "precio_entrada_sugerido": 000.00,
      "precio_objetivo": 000.00,
      "stop_loss": 000.00,
      "capital_asignar_pct": 00,
      "justificacion": "explicación técnica clara"
    }}
  ],
  "señales_venta": [
    {{
      "ticker": "XXXX",
      "razon": "explicación técnica clara"
    }}
  ],
  "acciones_mantener": ["XXXX", "XXXX"],
  "distribucion_capital": {{
    "en_operaciones": 00,
    "en_caja": 00,
    "nota": "explicación de la estrategia"
  }},
  "aprendizaje_del_dia": "qué señal o patrón destacó hoy que el agente debe recordar"
}}

Responde SOLO con el JSON, sin texto adicional."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ============================================
# PASO 5: Ejecutar operaciones en papel
# ============================================
def ejecutar_operaciones_papel(analisis, historial, precios_actuales):
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    operaciones_nuevas = []

    # Registrar compras sugeridas
    for señal in analisis.get("señales_compra", []):
        ticker  = señal["ticker"]
        precio  = señal["precio_entrada_sugerido"]
        pct     = señal["capital_asignar_pct"] / 100
        capital = CAPITAL_USD * pct
        cantidad = int(capital / precio) if precio > 0 else 0

        if cantidad > 0:
            op = {
                "id": f"{ticker}_{hoy}",
                "ticker": ticker,
                "tipo": "compra",
                "fecha_entrada": hoy,
                "precio_entrada": precio,
                "precio_objetivo": señal["precio_objetivo"],
                "stop_loss": señal["stop_loss"],
                "cantidad": cantidad,
                "capital_invertido": round(cantidad * precio, 2),
                "estado": "abierta",
                "justificacion": señal["justificacion"]
            }
            historial["operaciones"].append(op)
            operaciones_nuevas.append(op)

    # Revisar stop-loss y targets en operaciones abiertas
    for op in historial["operaciones"]:
        if op.get("estado") != "abierta":
            continue
        ticker = op["ticker"]
        if ticker not in precios_actuales:
            continue

        precio_actual = precios_actuales[ticker]
        ganancia_pct  = ((precio_actual - op["precio_entrada"]) / op["precio_entrada"]) * 100

        if precio_actual >= op["precio_objetivo"]:
            op["estado"]       = "cerrada_ganancia"
            op["fecha_salida"] = hoy
            op["precio_salida"]= precio_actual
            op["resultado_pct"]= round(ganancia_pct, 2)
            op["resultado_usd"]= round((precio_actual - op["precio_entrada"]) * op["cantidad"], 2)

        elif precio_actual <= op["stop_loss"]:
            op["estado"]       = "cerrada_stoploss"
            op["fecha_salida"] = hoy
            op["precio_salida"]= precio_actual
            op["resultado_pct"]= round(ganancia_pct, 2)
            op["resultado_usd"]= round((precio_actual - op["precio_entrada"]) * op["cantidad"], 2)

    return operaciones_nuevas

# ============================================
# PASO 6: Calcular performance del portafolio
# ============================================
def calcular_performance(historial):
    ops = historial["operaciones"]
    if not ops:
        return {"ganancia_total_usd": 0, "operaciones_cerradas": 0, "win_rate": 0}

    cerradas  = [o for o in ops if o.get("estado", "").startswith("cerrada")]
    ganadoras = [o for o in cerradas if o.get("resultado_usd", 0) > 0]
    ganancia  = sum(o.get("resultado_usd", 0) for o in cerradas)
    win_rate  = (len(ganadoras) / len(cerradas) * 100) if cerradas else 0

    return {
        "ganancia_total_usd": round(ganancia, 2),
        "operaciones_cerradas": len(cerradas),
        "operaciones_ganadoras": len(ganadoras),
        "win_rate": round(win_rate, 1),
        "operaciones_abiertas": len([o for o in ops if o.get("estado") == "abierta"])
    }

# ============================================
# MAIN
# ============================================
def main():
    print("\n" + "=" * 55)
    print("   🤖 INVESTMENT AI AGENT — PAPER TRADING")
    print("=" * 55)

    historial = cargar_historial()

    # --- Recopilar datos ---
    print("\n📊 Descargando datos del mercado...")
    resumen_total   = ""
    precios_actuales = {}

    for ticker in ACCIONES:
        try:
            print(f"   ↳ {ticker}...", end=" ")
            df = obtener_datos(ticker)
            df = calcular_indicadores(df)

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            precios_actuales[ticker] = float(df["Close"].iloc[-1])
            resumen_total += resumir_accion(ticker, df)
            print("✅")
        except Exception as e:
            print(f"❌ ({e})")

    # --- Análisis con Claude ---
    print("\n🧠 Claude analizando el mercado...")
    try:
        analisis = analizar_con_claude(resumen_total, historial)
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        return

    # --- Ejecutar operaciones papel ---
    nuevas_ops = ejecutar_operaciones_papel(analisis, historial, precios_actuales)

    # --- Guardar en historial ---
    historial["reportes"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "analisis": analisis,
        "resumen_breve": analisis.get("resumen_mercado", "")
    })
    guardar_historial(historial)

    # --- Performance ---
    perf = calcular_performance(historial)

    # --- Mostrar reporte ---
    print("\n" + "=" * 55)
    print("📋 REPORTE DEL DÍA")
    print("=" * 55)
    print(f"\n🌐 Mercado: {analisis.get('resumen_mercado', '')}")
    print(f"⚠️  Riesgo:  {analisis.get('nivel_riesgo', 'N/A')}")

    print("\n✅ SEÑALES DE COMPRA:")
    for s in analisis.get("señales_compra", []):
        print(f"   {s['ticker']}: entrada ${s['precio_entrada_sugerido']} | "
              f"objetivo ${s['precio_objetivo']} | stop ${s['stop_loss']}")
        print(f"   → {s['justificacion'][:80]}...")

    print("\n❌ SEÑALES DE VENTA/EVITAR:")
    for s in analisis.get("señales_venta", []):
        print(f"   {s['ticker']}: {s['razon'][:80]}...")

    print(f"\n💡 Aprendizaje del día: {analisis.get('aprendizaje_del_dia', '')}")

    print("\n📈 PERFORMANCE DEL PORTAFOLIO:")
    print(f"   Capital inicial:       ${CAPITAL_USD:,} USD")
    print(f"   Ganancia acumulada:    ${perf['ganancia_total_usd']:,.2f} USD")
    print(f"   Operaciones cerradas:  {perf['operaciones_cerradas']}")
    print(f"   Win rate:              {perf['win_rate']}%")
    print(f"   Posiciones abiertas:   {perf['operaciones_abiertas']}")

    if nuevas_ops:
        print(f"\n🚀 OPERACIONES REGISTRADAS HOY: {len(nuevas_ops)}")
        for op in nuevas_ops:
            print(f"   COMPRA {op['ticker']}: {op['cantidad']} acciones "
                  f"@ ${op['precio_entrada']:.2f} = ${op['capital_invertido']:,.2f}")

    print("\n✅ Todo guardado en historial.json")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    main()
