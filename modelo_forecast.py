import pandas as pd
import sqlite3
import logging
from datetime import datetime
from prophet import Prophet

# === CONFIGURACIÓN DE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("data/etl_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Silenciar logs internos de Prophet/cmdstanpy
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


def cargar_datos_historicos(ruta_db):
    """Lee ventas_limpias desde SQLite y agrega ingreso por día."""
    logger.info("FORECAST — Cargando datos históricos desde: %s", ruta_db)
    conexion = sqlite3.connect(ruta_db)
    df = pd.read_sql("SELECT fecha, ingreso_total FROM ventas_limpias", conexion)
    conexion.close()

    # Agregar ingreso total por día
    df['fecha'] = pd.to_datetime(df['fecha'])
    df_diario = df.groupby('fecha')['ingreso_total'].sum().reset_index()
    df_diario.columns = ['ds', 'y']  # Prophet requiere columnas 'ds' y 'y'
    df_diario = df_diario.sort_values('ds').reset_index(drop=True)

    logger.info("  -> %d días de historial cargados (%s → %s)",
                len(df_diario), df_diario['ds'].min().date(), df_diario['ds'].max().date())
    return df_diario


def entrenar_y_predecir(df_historico, dias_futuro=30):
    """Entrena el modelo Prophet y genera predicción para los próximos días."""
    logger.info("FORECAST — Entrenando modelo Prophet con %d días de historial...", len(df_historico))

    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05  # Sensibilidad a cambios de tendencia
    )
    modelo.fit(df_historico)

    # Crear dataframe de fechas futuras
    futuro = modelo.make_future_dataframe(periods=dias_futuro)
    prediccion = modelo.predict(futuro)

    # Quedarse solo con las columnas relevantes
    resultado = prediccion[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    resultado.columns = ['fecha', 'ingreso_predicho', 'ingreso_min', 'ingreso_max']

    # Redondear a 2 decimales y evitar negativos en el ingreso
    resultado['ingreso_predicho'] = resultado['ingreso_predicho'].clip(lower=0).round(2)
    resultado['ingreso_min']      = resultado['ingreso_min'].clip(lower=0).round(2)
    resultado['ingreso_max']      = resultado['ingreso_max'].round(2)
    resultado['fecha']            = resultado['fecha'].dt.strftime('%Y-%m-%d')

    # Marcar qué filas son históricas y cuáles son predicciones futuras
    ultima_fecha = df_historico['ds'].max().strftime('%Y-%m-%d')
    resultado['es_forecast'] = resultado['fecha'] > ultima_fecha

    solo_futuro = resultado[resultado['es_forecast']]
    logger.info("  -> Predicción generada: %s → %s",
                solo_futuro['fecha'].iloc[0], solo_futuro['fecha'].iloc[-1])
    logger.info("  -> Ingreso promedio diario predicho: $%.2f",
                solo_futuro['ingreso_predicho'].mean())
    logger.info("  -> Ingreso total predicho (%d días): $%.2f",
                dias_futuro, solo_futuro['ingreso_predicho'].sum())

    return resultado


def guardar_forecast(df_forecast, ruta_db):
    """Guarda las predicciones en la tabla ventas_forecast de SQLite."""
    logger.info("FORECAST — Guardando predicciones en: %s", ruta_db)
    conexion = sqlite3.connect(ruta_db)
    df_forecast.to_sql('ventas_forecast', conexion, if_exists='replace', index=False)
    conexion.close()
    logger.info("  -> %d filas guardadas en tabla 'ventas_forecast'.", len(df_forecast))


# === EJECUCIÓN PRINCIPAL ===
if __name__ == "__main__":
    inicio = datetime.now()
    logger.info("========================================")
    logger.info("  MODELO FORECAST — INICIO: %s", inicio.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("========================================")

    ruta_db = 'data/ventas_pyme.db'

    df_historico  = cargar_datos_historicos(ruta_db)
    df_prediccion = entrenar_y_predecir(df_historico, dias_futuro=30)
    guardar_forecast(df_prediccion, ruta_db)

    duracion = (datetime.now() - inicio).total_seconds()
    logger.info("========================================")
    logger.info("  MODELO FORECAST — COMPLETADO en %.2f seg", duracion)
    logger.info("========================================")
