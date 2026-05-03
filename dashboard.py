import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Investment AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# ESTILOS
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    padding: 2rem 2.5rem 3rem;
    max-width: 1200px;
}

.main-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #e8e4dc;
}

.main-title {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    color: #1a1a18;
    font-family: 'DM Sans', sans-serif;
}

.main-sub {
    font-size: 0.875rem;
    color: #888780;
    margin-top: 4px;
    font-weight: 400;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
    font-family: 'DM Mono', monospace;
}

.pill-live { background: #EAF3DE; color: #3B6D11; }
.pill-paper { background: #FAEEDA; color: #854F0B; }

.metric-card {
    background: #faf9f6;
    border: 1px solid #e8e4dc;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
}

.metric-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #888780;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 1.75rem;
    font-weight: 600;
    color: #1a1a18;
    letter-spacing: -0.02em;
    font-family: 'DM Mono', monospace;
}

.metric-delta-pos { color: #3B6D11; font-size: 0.8rem; margin-top: 4px; }
.metric-delta-neg { color: #A32D2D; font-size: 0.8rem; margin-top: 4px; }
.metric-delta-neu { color: #888780; font-size: 0.8rem; margin-top: 4px; }

.section-title {
    font-size: 0.7rem;
    font-weight: 600;
    color: #b4b2a9;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem;
}

.card {
    background: #ffffff;
    border: 1px solid #e8e4dc;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.signal-buy {
    background: #EAF3DE;
    border-left: 3px solid #639922;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}

.signal-sell {
    background: #FCEBEB;
    border-left: 3px solid #E24B4A;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}

.signal-ticker {
    font-family: 'DM Mono', monospace;
    font-size: 1rem;
    font-weight: 500;
    letter-spacing: 0.05em;
}

.signal-text {
    font-size: 0.85rem;
    color: #5F5E5A;
    margin-top: 4px;
    line-height: 1.5;
}

.op-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.875rem 0;
    border-bottom: 1px solid #f1efe8;
}

.op-ticker {
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    font-weight: 500;
    color: #1a1a18;
}

.op-detail {
    font-size: 0.8rem;
    color: #888780;
    margin-top: 2px;
}

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.04em;
}

.badge-open { background: #E6F1FB; color: #185FA5; }
.badge-win  { background: #EAF3DE; color: #3B6D11; }
.badge-loss { background: #FCEBEB; color: #A32D2D; }
.badge-stop { background: #FAEEDA; color: #854F0B; }

.risk-low  { color: #3B6D11; font-weight: 600; }
.risk-med  { color: #854F0B; font-weight: 600; }
.risk-high { color: #A32D2D; font-weight: 600; }

.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #b4b2a9;
    font-size: 0.875rem;
    line-height: 1.7;
}

.learn-box {
    background: #f1efe8;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-size: 0.875rem;
    color: #444441;
    line-height: 1.6;
    font-style: italic;
}

.step-row {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    margin-bottom: 1.25rem;
}

.step-num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #f1efe8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 600;
    color: #888780;
    flex-shrink: 0;
    font-family: 'DM Mono', monospace;
}

.step-title { font-size: 0.9rem; font-weight: 500; color: #1a1a18; margin-bottom: 2px; }
.step-desc  { font-size: 0.8rem; color: #888780; line-height: 1.5; }

code {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    background: #f1efe8;
    padding: 2px 6px;
    border-radius: 4px;
    color: #444441;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid #e8e4dc;
    padding-bottom: 0;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    font-weight: 400;
    color: #888780;
    background: transparent;
    border: none;
    padding: 8px 16px;
    border-radius: 8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    font-weight: 500;
    color: #1a1a18;
    background: #faf9f6;
    border: 1px solid #e8e4dc;
    border-bottom: 1px solid #faf9f6;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem;
}

div[data-testid="stMetric"] {
    background: #faf9f6;
    border: 1px solid #e8e4dc;
    border-radius: 12px;
    padding: 1rem 1.25rem;
}

div[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace;
    font-size: 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

CAPITAL_INICIAL = 10500
ARCHIVO_HISTORIAL = "historial.json"

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data(ttl=60)
def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"operaciones": [], "reportes": []}

def calcular_metricas(historial):
    ops = historial.get("operaciones", [])
    cerradas  = [o for o in ops if o.get("estado", "").startswith("cerrada")]
    ganadoras = [o for o in cerradas if o.get("resultado_usd", 0) > 0]
    ganancia  = sum(o.get("resultado_usd", 0) for o in cerradas)
    abiertas  = [o for o in ops if o.get("estado") == "abierta"]
    invertido = sum(o.get("capital_invertido", 0) for o in abiertas)
    win_rate  = (len(ganadoras) / len(cerradas) * 100) if cerradas else 0

    return {
        "ganancia_total": round(ganancia, 2),
        "capital_actual": round(CAPITAL_INICIAL + ganancia, 2),
        "invertido_ahora": round(invertido, 2),
        "en_caja": round(CAPITAL_INICIAL + ganancia - invertido, 2),
        "operaciones_cerradas": len(cerradas),
        "operaciones_ganadoras": len(ganadoras),
        "operaciones_abiertas": len(abiertas),
        "win_rate": round(win_rate, 1),
        "total_operaciones": len(ops),
    }

# ============================================
# HEADER
# ============================================
historial = cargar_historial()
metricas  = calcular_metricas(historial)
reportes  = historial.get("reportes", [])
ultimo    = reportes[-1] if reportes else None

st.markdown("""
<div class="main-header">
  <div>
    <div class="main-title">Investment AI Agent</div>
    <div class="main-sub">Paper trading · Acciones USA · S&P 500</div>
  </div>
  <span class="status-pill pill-paper">● PAPER TRADING</span>
</div>
""", unsafe_allow_html=True)

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
c1, c2, c3, c4, c5 = st.columns(5)

ganancia_color = "normal" if metricas["ganancia_total"] >= 0 else "inverse"
ganancia_delta = f"${metricas['ganancia_total']:+,.2f} USD"

with c1:
    st.metric("Capital actual", f"${metricas['capital_actual']:,.0f}", ganancia_delta)
with c2:
    pct = ((metricas['capital_actual'] - CAPITAL_INICIAL) / CAPITAL_INICIAL * 100)
    st.metric("Retorno total", f"{pct:+.2f}%", "vs capital inicial")
with c3:
    st.metric("Win rate", f"{metricas['win_rate']}%", f"{metricas['operaciones_ganadoras']} de {metricas['operaciones_cerradas']} ops")
with c4:
    st.metric("Posiciones abiertas", metricas["operaciones_abiertas"], f"${metricas['invertido_ahora']:,.0f} invertidos")
with c5:
    st.metric("En caja", f"${metricas['en_caja']:,.0f}", "disponible")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# TABS
# ============================================
tab1, tab2, tab3, tab4 = st.tabs(["📋 Último reporte", "📊 Operaciones", "📈 Performance", "⚙️ Configuración"])

# ─── TAB 1: ÚLTIMO REPORTE ────────────────────────────────
with tab1:
    if not ultimo:
        st.markdown("""
        <div class="empty-state">
            Aún no hay reportes.<br>
            Corre <code>python investment_agent.py</code> para generar el primer análisis.
        </div>
        """, unsafe_allow_html=True)
    else:
        analisis = ultimo.get("analisis", {})
        fecha    = ultimo.get("fecha", "—")

        col_a, col_b = st.columns([2, 1])

        with col_a:
            st.markdown(f'<div class="section-title">Análisis del {fecha}</div>', unsafe_allow_html=True)

            resumen = analisis.get("resumen_mercado", "Sin datos")
            nivel   = analisis.get("nivel_riesgo", "—")
            nivel_class = {"BAJO": "risk-low", "MEDIO": "risk-med", "ALTO": "risk-high"}.get(nivel, "risk-neu")

            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem">
                    <div style="font-size:0.9rem;color:#444441;line-height:1.6;max-width:80%">{resumen}</div>
                    <div style="text-align:right;flex-shrink:0;margin-left:1rem">
                        <div style="font-size:0.7rem;color:#b4b2a9;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">Riesgo</div>
                        <div class="{nivel_class}" style="font-size:1rem">{nivel}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Señales compra
            st.markdown('<div class="section-title">Señales de compra</div>', unsafe_allow_html=True)
            compras = analisis.get("señales_compra", [])
            if compras:
                for s in compras:
                    st.markdown(f"""
                    <div class="signal-buy">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span class="signal-ticker" style="color:#27500A">{s.get('ticker','')}</span>
                            <span style="font-family:'DM Mono',monospace;font-size:0.8rem;color:#3B6D11">
                                entrada ${s.get('precio_entrada_sugerido',0):.2f} &nbsp;→&nbsp;
                                obj ${s.get('precio_objetivo',0):.2f} &nbsp;|&nbsp;
                                stop ${s.get('stop_loss',0):.2f}
                            </span>
                        </div>
                        <div class="signal-text">{s.get('justificacion','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state" style="padding:1.5rem">Sin señales de compra hoy</div>', unsafe_allow_html=True)

            # Señales venta
            st.markdown('<div class="section-title" style="margin-top:1.25rem">Señales de venta / evitar</div>', unsafe_allow_html=True)
            ventas = analisis.get("señales_venta", [])
            if ventas:
                for s in ventas:
                    st.markdown(f"""
                    <div class="signal-sell">
                        <span class="signal-ticker" style="color:#791F1F">{s.get('ticker','')}</span>
                        <div class="signal-text">{s.get('razon','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state" style="padding:1.5rem">Sin señales de venta hoy</div>', unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="section-title">Distribución del capital</div>', unsafe_allow_html=True)
            dist = analisis.get("distribucion_capital", {})
            en_ops = dist.get("en_operaciones", 0)
            en_caja = dist.get("en_caja", 100)

            fig_pie = go.Figure(go.Pie(
                values=[en_ops, en_caja],
                labels=["En operaciones", "En caja"],
                hole=0.65,
                marker_colors=["#639922", "#e8e4dc"],
                textinfo="none",
                hovertemplate="%{label}: %{value}%<extra></extra>"
            ))
            fig_pie.update_layout(
                height=200,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            nota = dist.get("nota", "")
            if nota:
                st.markdown(f'<div class="learn-box">{nota}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title" style="margin-top:1.25rem">Aprendizaje del día</div>', unsafe_allow_html=True)
            aprendizaje = analisis.get("aprendizaje_del_dia", "—")
            st.markdown(f'<div class="learn-box">{aprendizaje}</div>', unsafe_allow_html=True)

            mantener = analisis.get("acciones_mantener", [])
            if mantener:
                st.markdown('<div class="section-title" style="margin-top:1.25rem">Mantener posición</div>', unsafe_allow_html=True)
                for t in mantener:
                    st.markdown(f'<span class="badge badge-open" style="margin-right:6px;margin-bottom:6px">{t}</span>', unsafe_allow_html=True)

# ─── TAB 2: OPERACIONES ───────────────────────────────────
with tab2:
    ops = historial.get("operaciones", [])

    if not ops:
        st.markdown("""
        <div class="empty-state">
            No hay operaciones registradas todavía.<br>
            Aparecerán aquí cuando el agente haga su primera recomendación.
        </div>
        """, unsafe_allow_html=True)
    else:
        col_ab, col_bb = st.columns([3, 2])

        with col_ab:
            abiertas = [o for o in ops if o.get("estado") == "abierta"]
            st.markdown(f'<div class="section-title">Posiciones abiertas ({len(abiertas)})</div>', unsafe_allow_html=True)

            if abiertas:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                for op in abiertas:
                    entrada  = op.get("precio_entrada", 0)
                    objetivo = op.get("precio_objetivo", 0)
                    stop     = op.get("stop_loss", 0)
                    rango    = objetivo - stop
                    progreso = max(0, min(100, ((entrada - stop) / rango * 100))) if rango > 0 else 0
                    st.markdown(f"""
                    <div class="op-row">
                        <div>
                            <div class="op-ticker">{op.get('ticker','')} <span class="badge badge-open">ABIERTA</span></div>
                            <div class="op-detail">Entrada ${entrada:.2f} · Obj ${objetivo:.2f} · Stop ${stop:.2f}</div>
                            <div class="op-detail">{op.get('cantidad',0)} acciones · ${op.get('capital_invertido',0):,.2f} invertidos</div>
                        </div>
                        <div style="text-align:right;font-family:'DM Mono',monospace;font-size:0.85rem;color:#185FA5">
                            {op.get('fecha_entrada','')[:10]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state" style="padding:1.5rem">Sin posiciones abiertas</div>', unsafe_allow_html=True)

            cerradas = [o for o in ops if o.get("estado", "").startswith("cerrada")]
            st.markdown(f'<div class="section-title" style="margin-top:1.5rem">Historial cerradas ({len(cerradas)})</div>', unsafe_allow_html=True)

            if cerradas:
                rows = []
                for op in reversed(cerradas):
                    estado = op.get("estado", "")
                    badge  = "badge-win" if "ganancia" in estado else "badge-loss" if "stop" in estado else "badge-stop"
                    label  = "GANANCIA" if "ganancia" in estado else "STOP-LOSS" if "stop" in estado else "CERRADA"
                    res    = op.get("resultado_usd", 0)
                    res_pct = op.get("resultado_pct", 0)
                    color  = "#3B6D11" if res >= 0 else "#A32D2D"
                    rows.append(f"""
                    <div class="op-row">
                        <div>
                            <div class="op-ticker">{op.get('ticker','')} <span class="badge {badge}">{label}</span></div>
                            <div class="op-detail">Entrada ${op.get('precio_entrada',0):.2f} → Salida ${op.get('precio_salida',0):.2f}</div>
                        </div>
                        <div style="text-align:right;font-family:'DM Mono',monospace">
                            <div style="color:{color};font-weight:500">${res:+,.2f}</div>
                            <div style="font-size:0.75rem;color:#888780">{res_pct:+.1f}%</div>
                        </div>
                    </div>
                    """)
                st.markdown('<div class="card">' + "".join(rows) + '</div>', unsafe_allow_html=True)

        with col_bb:
            st.markdown('<div class="section-title">Breakdown de resultados</div>', unsafe_allow_html=True)
            cerradas = [o for o in ops if o.get("estado","").startswith("cerrada")]
            if cerradas:
                ganadoras = len([o for o in cerradas if o.get("resultado_usd",0) > 0])
                perdedoras = len(cerradas) - ganadoras
                fig_donut = go.Figure(go.Pie(
                    values=[ganadoras, perdedoras],
                    labels=["Ganadoras", "Perdedoras"],
                    hole=0.6,
                    marker_colors=["#639922", "#E24B4A"],
                    textinfo="none",
                    hovertemplate="%{label}: %{value}<extra></extra>"
                ))
                fig_donut.update_layout(
                    height=220,
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.markdown('<div class="empty-state" style="padding:2rem">Sin operaciones cerradas</div>', unsafe_allow_html=True)

# ─── TAB 3: PERFORMANCE ───────────────────────────────────
with tab3:
    if len(reportes) < 2:
        st.markdown("""
        <div class="empty-state">
            Necesitas al menos 2 días de datos para ver la curva de performance.<br>
            Sigue corriendo el agente cada día y aparecerá aquí automáticamente.
        </div>
        """, unsafe_allow_html=True)
    else:
        fechas    = [r.get("fecha", "")[:10] for r in reportes]
        ganancias = []
        acum = 0
        for r in reportes:
            ops_del_dia = [
                o for o in historial.get("operaciones", [])
                if o.get("fecha_salida", "")[:10] == r.get("fecha","")[:10]
            ]
            acum += sum(o.get("resultado_usd", 0) for o in ops_del_dia)
            ganancias.append(round(CAPITAL_INICIAL + acum, 2))

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=fechas, y=ganancias,
            mode="lines+markers",
            line=dict(color="#639922", width=2.5),
            marker=dict(size=6, color="#639922"),
            fill="tozeroy",
            fillcolor="rgba(99,153,34,0.08)",
            hovertemplate="Fecha: %{x}<br>Capital: $%{y:,.2f}<extra></extra>"
        ))
        fig_line.add_hline(
            y=CAPITAL_INICIAL,
            line_dash="dot",
            line_color="#e8e4dc",
            annotation_text="Capital inicial",
            annotation_position="bottom right"
        )
        fig_line.update_layout(
            title="Evolución del portafolio",
            height=380,
            margin=dict(t=40, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#f1efe8", tickformat="$,.0f", tickfont=dict(size=11)),
            font=dict(family="DM Sans")
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Tabla de reportes
        st.markdown('<div class="section-title" style="margin-top:1rem">Historial de reportes</div>', unsafe_allow_html=True)
        rows_rep = []
        for r in reversed(reportes):
            an = r.get("analisis", {})
            nivel = an.get("nivel_riesgo", "—")
            compras_n = len(an.get("señales_compra", []))
            ventas_n  = len(an.get("señales_venta", []))
            rows_rep.append({
                "Fecha": r.get("fecha","")[:16],
                "Riesgo": nivel,
                "Compras": compras_n,
                "Ventas": ventas_n,
                "Resumen": an.get("resumen_mercado","")[:80] + "..."
            })
        df_rep = pd.DataFrame(rows_rep)
        st.dataframe(df_rep, use_container_width=True, hide_index=True)

# ─── TAB 4: CONFIGURACIÓN ─────────────────────────────────
with tab4:
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown('<div class="section-title">Cómo activar el agente</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div class="step-row">
                <div class="step-num">1</div>
                <div>
                    <div class="step-title">Instalar dependencias</div>
                    <div class="step-desc"><code>pip install anthropic yfinance pandas plotly streamlit</code></div>
                </div>
            </div>
            <div class="step-row">
                <div class="step-num">2</div>
                <div>
                    <div class="step-title">Obtener API Key</div>
                    <div class="step-desc">Ir a <code>console.anthropic.com</code> → API Keys → Create Key</div>
                </div>
            </div>
            <div class="step-row">
                <div class="step-num">3</div>
                <div>
                    <div class="step-title">Configurar el agente</div>
                    <div class="step-desc">Pegar la key en <code>investment_agent.py</code> donde dice <code>TU_API_KEY_DE_ANTHROPIC</code></div>
                </div>
            </div>
            <div class="step-row">
                <div class="step-num">4</div>
                <div>
                    <div class="step-title">Correr el agente</div>
                    <div class="step-desc"><code>python investment_agent.py</code> — idealmente después del cierre del mercado (17:00 Chile)</div>
                </div>
            </div>
            <div class="step-row" style="margin-bottom:0">
                <div class="step-num">5</div>
                <div>
                    <div class="step-title">Ver el dashboard</div>
                    <div class="step-desc"><code>streamlit run dashboard.py</code> o acceder a tu URL pública en Streamlit Cloud</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        st.markdown('<div class="section-title">Parámetros actuales</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <div class="op-row">
                <div class="op-ticker">Capital inicial</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.9rem">${CAPITAL_INICIAL:,} USD</div>
            </div>
            <div class="op-row">
                <div class="op-ticker">Mercado</div>
                <div style="font-size:0.85rem;color:#888780">Acciones USA (S&P 500)</div>
            </div>
            <div class="op-row">
                <div class="op-ticker">Acciones monitoreadas</div>
                <div style="font-size:0.85rem;color:#888780">10 (AAPL, MSFT, NVDA...)</div>
            </div>
            <div class="op-row">
                <div class="op-ticker">Estrategia</div>
                <div style="font-size:0.85rem;color:#888780">Swing trading (2–7 días)</div>
            </div>
            <div class="op-row">
                <div class="op-ticker">Indicadores</div>
                <div style="font-size:0.85rem;color:#888780">RSI, MA20/50, MACD, Bollinger</div>
            </div>
            <div class="op-row" style="border-bottom:none">
                <div class="op-ticker">Modelo IA</div>
                <div style="font-size:0.85rem;color:#888780">Claude Sonnet 4</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:1.25rem">Próximas mejoras</div>', unsafe_allow_html=True)
        mejoras = [
            "Multi-agente (CEO + Research + Risk)",
            "Alertas por email / Telegram",
            "Conexión con Alpaca (broker real)",
            "Análisis de sentimiento en noticias",
            "Backtesting histórico",
            "Extended Thinking para decisiones complejas",
        ]
        items = "".join([f'<div style="font-size:0.8rem;color:#888780;padding:5px 0;border-bottom:1px solid #f1efe8">+ {m}</div>' for m in mejoras])
        st.markdown(f'<div class="card">{items}</div>', unsafe_allow_html=True)

    st.markdown('<br><div class="section-title">Estructura de archivos del proyecto</div>', unsafe_allow_html=True)
    st.code("""
investment-ai-agent/
├── investment_agent.py   # el agente principal (corre cada día)
├── dashboard.py          # esta app (Streamlit)
├── historial.json        # memoria del agente (se genera automático)
├── requirements.txt      # dependencias para el hosting
└── .streamlit/
    └── secrets.toml      # tu API key (no se sube a GitHub)
    """, language="bash")

# Footer
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;font-size:0.75rem;color:#b4b2a9;border-top:1px solid #e8e4dc;margin-top:2rem">
    Investment AI Agent · Paper trading · Para uso educativo únicamente
</div>
""", unsafe_allow_html=True)
