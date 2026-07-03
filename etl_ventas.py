import pandas as pd
import csv
import sqlite3
import logging
from datetime import datetime

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


def extraer_datos(ruta_archivo):
    """Carga los datos crudos desde el CSV."""
    logger.info("PASO 1 — Extracción iniciada desde: %s", ruta_archivo)
    df = pd.read_csv(ruta_archivo, quoting=csv.QUOTE_NONE)
    logger.info("  -> %d filas cargadas.", len(df))
    return df


def transformar_datos(df):
    """Limpia, estandariza y enriquece la información."""
    logger.info("PASO 2 — Transformación iniciada...")
    total_inicial = len(df)

    # 1. Quitar comillas invasoras de columnas de texto
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace('"', '', regex=False)
    df['id_transaccion'] = df['id_transaccion'].astype(str).str.replace('"', '', regex=False)

    # 2. Eliminar duplicados
    antes = len(df)
    df = df.drop_duplicates()
    duplicados_eliminados = antes - len(df)
    logger.info("  -> Duplicados eliminados: %d", duplicados_eliminados)

    # 3. Imputar cantidad nula → 1
    nulos_cantidad = df['cantidad'].isna().sum()
    df['cantidad'] = df['cantidad'].fillna(1)
    logger.info("  -> Cantidades nulas imputadas a 1: %d", nulos_cantidad)

    # 4. Filtrar cantidades negativas
    antes = len(df)
    df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')
    df = df[df['cantidad'] > 0]
    negativos_eliminados = antes - len(df)
    logger.info("  -> Registros con cantidad negativa eliminados: %d", negativos_eliminados)

    # 5. Estandarizar fechas a YYYY-MM-DD
    df['fecha'] = pd.to_datetime(
        df['fecha'].astype(str).str.strip(),
        format='mixed', dayfirst=True, errors='coerce'
    ).dt.strftime('%Y-%m-%d')
    fechas_invalidas = df['fecha'].isna().sum()
    if fechas_invalidas > 0:
        logger.warning("  -> Filas con fecha inválida (serán descartadas): %d", fechas_invalidas)
        df = df.dropna(subset=['fecha'])

    # 6. Calcular ingreso_total
    df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors='coerce')
    df['ingreso_total'] = df['cantidad'] * df['precio_unitario']

    total_final = len(df)
    logger.info("  -> Filas originales: %d | Filas limpias: %d | Descartadas: %d",
                total_inicial, total_final, total_inicial - total_final)

    # 7. Reporte de calidad
    logger.info("--- REPORTE DE CALIDAD ---")
    logger.info("  Ingreso total del dataset: $%.2f", df['ingreso_total'].sum())
    logger.info("  Rango de fechas: %s → %s", df['fecha'].min(), df['fecha'].max())
    logger.info("  Productos únicos: %d", df['producto'].nunique())
    logger.info("  Clientes únicos: %d", df['cliente'].nunique())
    logger.info("--------------------------")

    return df


def cargar_datos(df, ruta_csv, ruta_db):
    """Exporta el CSV de backup y realiza carga incremental en SQLite."""

    # 1. Backup CSV
    logger.info("PASO 3.1 — Exportando backup CSV a: %s", ruta_csv)
    df.to_csv(ruta_csv, index=False)

    # 2. Carga incremental en SQLite
    logger.info("PASO 3.2 — Carga incremental en base de datos: %s", ruta_db)
    try:
        conexion = sqlite3.connect(ruta_db)
        cursor = conexion.cursor()

        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_limpias (
                id_transaccion  TEXT,
                fecha           TEXT,
                producto        TEXT,
                cantidad        REAL,
                precio_unitario REAL,
                cliente         TEXT,
                estado          TEXT,
                ingreso_total   REAL
            )
        """)
        conexion.commit()

        # Obtener IDs ya existentes en la BD
        ids_existentes = pd.read_sql("SELECT id_transaccion FROM ventas_limpias", conexion)
        ids_existentes = set(ids_existentes['id_transaccion'].astype(str))

        # Filtrar solo registros nuevos
        df['id_transaccion'] = df['id_transaccion'].astype(str)
        df_nuevos = df[~df['id_transaccion'].isin(ids_existentes)]

        if df_nuevos.empty:
            logger.info("  -> No hay registros nuevos para insertar.")
        else:
            df_nuevos.to_sql('ventas_limpias', conexion, if_exists='append', index=False)
            logger.info("  -> %d registros nuevos insertados.", len(df_nuevos))

        conexion.close()

    except Exception as e:
        logger.error("  -> ERROR al cargar en la base de datos: %s", e)
        raise


# === EJECUCIÓN PRINCIPAL DEL PIPELINE ===
if __name__ == "__main__":
    inicio = datetime.now()
    logger.info("========================================")
    logger.info("  PIPELINE ETL — INICIO: %s", inicio.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("========================================")

    ruta_entrada    = 'data/ventas_crudas_semestre.csv'
    ruta_csv_salida = 'data/ventas_limpias_mayo.csv'
    ruta_db_salida  = 'data/ventas_pyme.db'

    df_crudo  = extraer_datos(ruta_entrada)
    df_limpio = transformar_datos(df_crudo)
    cargar_datos(df_limpio, ruta_csv_salida, ruta_db_salida)

    duracion = (datetime.now() - inicio).total_seconds()
    logger.info("========================================")
    logger.info("  PIPELINE ETL — COMPLETADO en %.2f seg", duracion)
    logger.info("========================================")