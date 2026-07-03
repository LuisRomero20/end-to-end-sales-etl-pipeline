import os
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard de Ventas - PYME",
    page_icon="📊",
    layout="wide"
)

# ── Bootstrap: genera la BD si no existe (necesario en Streamlit Cloud) ──────
@st.cache_resource
def inicializar_pipeline():
    if not os.path.exists("data/ventas_pyme.db"):
        os.makedirs("data", exist_ok=True)
        with st.spinner("Inicializando datos por primera vez..."):
            import generar_data
            import etl_ventas
            import modelo_forecast
            generar_data.generar()
            df_crudo  = etl_ventas.extraer_datos("data/ventas_crudas_semestre.csv")
            df_limpio = etl_ventas.transformar_datos(df_crudo)
            etl_ventas.cargar_datos(df_limpio, "data/ventas_limpias_mayo.csv", "data/ventas_pyme.db")
            df_hist = modelo_forecast.cargar_datos_historicos("data/ventas_pyme.db")
            df_pred = modelo_forecast.entrenar_y_predecir(df_hist, dias_futuro=30)
            modelo_forecast.guardar_forecast(df_pred, "data/ventas_pyme.db")

inicializar_pipeline()

# ── Carga de datos desde SQLite ──────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect("data/ventas_pyme.db")
    ventas    = pd.read_sql("SELECT * FROM ventas_limpias",  conn)
    forecast  = pd.read_sql("SELECT * FROM ventas_forecast", conn)
    conn.close()

    ventas['fecha'] = pd.to_datetime(ventas['fecha'])
    forecast['fecha'] = pd.to_datetime(forecast['fecha'])
    forecast['es_forecast'] = forecast['es_forecast'].astype(bool)
    return ventas, forecast

ventas, forecast = cargar_datos()

# Serie histórica diaria
historico = ventas.groupby('fecha')['ingreso_total'].sum().reset_index()

# Separar forecast en histórico ajustado y futuro
hist_fc  = forecast[~forecast['es_forecast']].copy()
fut_fc   = forecast[forecast['es_forecast']].copy()

# ── Sidebar — Filtros ────────────────────────────────────────────────────────
st.sidebar.title("🔎 Filtros")

productos   = ["Todos"] + sorted(ventas['producto'].unique().tolist())
clientes    = ["Todos"] + sorted(ventas['cliente'].unique().tolist())
estados     = ["Todos"] + sorted(ventas['estado'].unique().tolist())

sel_producto = st.sidebar.selectbox("Producto",  productos)
sel_cliente  = st.sidebar.selectbox("Cliente",   clientes)
sel_estado   = st.sidebar.selectbox("Estado",    estados)

fecha_min = ventas['fecha'].min().date()
fecha_max = ventas['fecha'].max().date()
rango_fecha = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

# Aplicar filtros
df_filtrado = ventas.copy()
if sel_producto != "Todos":
    df_filtrado = df_filtrado[df_filtrado['producto'] == sel_producto]
if sel_cliente != "Todos":
    df_filtrado = df_filtrado[df_filtrado['cliente'] == sel_cliente]
if sel_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['estado'] == sel_estado]
if len(rango_fecha) == 2:
    df_filtrado = df_filtrado[
        (df_filtrado['fecha'].dt.date >= rango_fecha[0]) &
        (df_filtrado['fecha'].dt.date <= rango_fecha[1])
    ]

# Periodo anterior (mismo nro. de días justo antes) para calcular deltas
if len(rango_fecha) == 2:
    dias_periodo  = (rango_fecha[1] - rango_fecha[0]).days + 1
    ant_fin = rango_fecha[0] - pd.Timedelta(days=1)
    ant_ini = rango_fecha[0] - pd.Timedelta(days=dias_periodo)
    df_ant = ventas.copy()
    if sel_producto != "Todos": df_ant = df_ant[df_ant['producto'] == sel_producto]
    if sel_cliente  != "Todos": df_ant = df_ant[df_ant['cliente']  == sel_cliente]
    if sel_estado   != "Todos": df_ant = df_ant[df_ant['estado']   == sel_estado]
    df_ant = df_ant[(df_ant['fecha'].dt.date >= ant_ini) & (df_ant['fecha'].dt.date <= ant_fin)]
else:
    df_ant = pd.DataFrame()

def delta_pct(actual, anterior):
    """Devuelve string de delta o None si no hay datos previos."""
    if df_ant.empty or anterior == 0:
        return None
    pct = ((actual - anterior) / anterior) * 100
    return f"{'+' if pct >= 0 else ''}{pct:.1f}%"

# ── Sidebar — Exportar ───────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("📥 Exportar")
cols_export = ['fecha', 'producto', 'cliente', 'cantidad', 'precio_unitario', 'ingreso_total', 'estado']
df_export = df_filtrado[cols_export].copy()
df_export['fecha'] = df_export['fecha'].dt.strftime('%Y-%m-%d')
st.sidebar.download_button(
    label="Descargar datos filtrados (.csv)",
    data=df_export.to_csv(index=False).encode('utf-8'),
    file_name="ventas_filtradas.csv",
    mime="text/csv"
)

# ── Título ───────────────────────────────────────────────────────────────────
col_titulo, col_fecha = st.columns([4, 1])
with col_titulo:
    st.title("📊 Dashboard Ejecutivo de Ventas")
    st.caption("Automotriz PYME · Pipeline ETL + Forecasting con Prophet")
with col_fecha:
    ultima_act = pd.Timestamp(os.path.getmtime("data/ventas_pyme.db"), unit='s').strftime('%d/%m/%Y %H:%M')
    st.metric("🔄 Última actualización", ultima_act)
st.divider()

# ── Fila 1 — KPIs ────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

ingreso_total    = df_filtrado['ingreso_total'].sum()
total_pedidos    = len(df_filtrado)
ticket_promedio  = df_filtrado['ingreso_total'].mean() if total_pedidos > 0 else 0
unidades_total   = df_filtrado['cantidad'].sum()
ingreso_forecast = fut_fc['ingreso_predicho'].sum()

# Métricas del periodo anterior
ant_ingreso   = df_ant['ingreso_total'].sum()   if not df_ant.empty else 0
ant_pedidos   = len(df_ant)                     if not df_ant.empty else 0
ant_ticket    = df_ant['ingreso_total'].mean()  if not df_ant.empty else 0
ant_unidades  = df_ant['cantidad'].sum()        if not df_ant.empty else 0

k1.metric("💰 Ingreso Total",     f"${ingreso_total:,.0f}",  delta=delta_pct(ingreso_total,   ant_ingreso))
k2.metric("🛒 Total Pedidos",     f"{total_pedidos:,}",      delta=delta_pct(total_pedidos,   ant_pedidos))
k3.metric("🎯 Ticket Promedio",   f"${ticket_promedio:,.0f}",delta=delta_pct(ticket_promedio, ant_ticket))
k4.metric("📦 Unidades Vendidas", f"{unidades_total:,.0f}",  delta=delta_pct(unidades_total,  ant_unidades))
k5.metric("🔮 Forecast 30 días",  f"${ingreso_forecast:,.0f}")

st.divider()

# ── Fila 2 — Tendencia histórica + Forecast ──────────────────────────────────
st.subheader("📈 Tendencia de Ventas + Predicción a 30 días")

serie_filtrada = df_filtrado.groupby('fecha')['ingreso_total'].sum().reset_index()

fig_tendencia = go.Figure()

# Área histórica
fig_tendencia.add_trace(go.Scatter(
    x=serie_filtrada['fecha'], y=serie_filtrada['ingreso_total'],
    name="Histórico real", fill='tozeroy',
    line=dict(color='#2196F3', width=2),
    fillcolor='rgba(33,150,243,0.15)'
))

# Banda de incertidumbre del forecast
fig_tendencia.add_trace(go.Scatter(
    x=pd.concat([fut_fc['fecha'], fut_fc['fecha'][::-1]]),
    y=pd.concat([fut_fc['ingreso_max'], fut_fc['ingreso_min'][::-1]]),
    fill='toself', fillcolor='rgba(255,152,0,0.15)',
    line=dict(color='rgba(0,0,0,0)'),
    name="Banda de confianza", showlegend=True
))

# Línea de predicción
fig_tendencia.add_trace(go.Scatter(
    x=fut_fc['fecha'], y=fut_fc['ingreso_predicho'],
    name="Forecast", line=dict(color='#FF9800', width=2, dash='dash')
))

fig_tendencia.update_layout(
    height=380, margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    xaxis_title="Fecha", yaxis_title="Ingreso ($)"
)
st.plotly_chart(fig_tendencia, use_container_width=True)

st.divider()

# ── Fila 3 — Barras por producto y dona por estado ───────────────────────────
col_bar, col_dona = st.columns([3, 2])

with col_bar:
    st.subheader("🏆 Ingresos por Producto")
    por_producto = (
        df_filtrado.groupby('producto')['ingreso_total']
        .sum().sort_values(ascending=True).reset_index()
    )
    fig_bar = go.Figure(go.Bar(
        x=por_producto['ingreso_total'],
        y=por_producto['producto'],
        orientation='h',
        marker_color='#2196F3',
        text=por_producto['ingreso_total'].apply(lambda v: f"${v:,.0f}"),
        textposition='outside'
    ))
    fig_bar.update_layout(height=320, margin=dict(l=0, r=60, t=10, b=0),
                          xaxis_title="Ingreso ($)")
    st.plotly_chart(fig_bar, use_container_width=True)

with col_dona:
    st.subheader("📋 Pedidos por Estado")
    por_estado = df_filtrado['estado'].value_counts().reset_index()
    por_estado.columns = ['estado', 'cantidad']
    fig_dona = go.Figure(go.Pie(
        labels=por_estado['estado'],
        values=por_estado['cantidad'],
        hole=0.5,
        marker_colors=['#4CAF50', '#FF9800', '#F44336']
    ))
    fig_dona.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_dona, use_container_width=True)

st.divider()

# ── Fila 4 — Top clientes y tabla de datos ───────────────────────────────────
col_clientes, col_tabla = st.columns([2, 3])

with col_clientes:
    st.subheader("👥 Top Clientes")
    top_clientes = (
        df_filtrado.groupby('cliente')['ingreso_total']
        .sum().sort_values(ascending=False).head(7).reset_index()
    )
    fig_clientes = go.Figure(go.Bar(
        x=top_clientes['ingreso_total'],
        y=top_clientes['cliente'],
        orientation='h',
        marker_color='#9C27B0',
        text=top_clientes['ingreso_total'].apply(lambda v: f"${v:,.0f}"),
        textposition='outside'
    ))
    fig_clientes.update_layout(height=300, margin=dict(l=0, r=60, t=10, b=0),
                               xaxis_title="Ingreso ($)")
    st.plotly_chart(fig_clientes, use_container_width=True)

with col_tabla:
    st.subheader("🗃️ Últimas Transacciones")
    columnas = ['fecha', 'producto', 'cliente', 'cantidad', 'precio_unitario', 'ingreso_total', 'estado']
    df_tabla = df_filtrado[columnas].sort_values('fecha', ascending=False).head(50).copy()
    df_tabla['fecha'] = df_tabla['fecha'].dt.strftime('%Y-%m-%d')
    df_tabla['ingreso_total']   = df_tabla['ingreso_total'].apply(lambda v: f"${v:,.2f}")
    df_tabla['precio_unitario'] = df_tabla['precio_unitario'].apply(lambda v: f"${v:,.2f}")
    st.dataframe(df_tabla, use_container_width=True, height=300, hide_index=True)
