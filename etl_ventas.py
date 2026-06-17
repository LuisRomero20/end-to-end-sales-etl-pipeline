import pandas as pd
import datetime
import csv
import sqlite3

def extraer_datos(ruta_archivo):
    """Carga los datos crudos desde el CSV."""
    print("[1] Iniciando extracción de datos...")
    # TU MISIÓN 1: Usar pd.read_csv para leer el archivo
    df = pd.read_csv(ruta_archivo, quoting=csv.QUOTE_NONE)
    return df

def transformar_datos(df):
    """Limpia y estandariza la información."""
    print("[2] Iniciando limpieza de datos...")
    
    # 1. Limpieza extrema: Quitar comillas de TODAS las columnas
    # Esto arregla el "1002" y el "Completado"
    for col in df.columns:
        if df[col].dtype == 'object':  # Si la columna es de texto
            df[col] = df[col].str.replace('"', '', regex=False)
            
    # Forzamos la limpieza del ID por si Pandas lo leyó mal
    df['id_transaccion'] = df['id_transaccion'].astype(str).str.replace('"', '', regex=False)
    
    # 2. Eliminar duplicados
    df = df.drop_duplicates()
    
    # 3. Rellenar la cantidad vacía (asumimos 1 por defecto)
    df['cantidad'] = df['cantidad'].fillna(1)
    
    # 4. Filtrar cantidades negativas (solo mayores a 0)
    df = df[df['cantidad'] > 0]
    
    # 5. Estandarizar la fecha (El secreto: format='mixed')
    # Limpiamos espacios en blanco con strip() y le decimos que el formato es mixto
    df['fecha'] = pd.to_datetime(df['fecha'].astype(str).str.strip(), format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

    return df

def cargar_datos(df, ruta_csv, ruta_db):
    """Exporta los datos limpios a CSV y a una Base de Datos SQL."""
    
    # 1. Exportar a CSV (como backup)
    print(f"[3.1] Exportando backup limpio a: {ruta_csv}...")
    df.to_csv(ruta_csv, index=False)
    
    # 2. Exportar a Base de Datos SQLite (El verdadero Load)
    print(f"[3.2] Cargando datos en la base de datos: {ruta_db}...")
    try:
        # Creamos la conexión a la base de datos (si no existe, la crea sola)
        conexion = sqlite3.connect(ruta_db)
        
        # Insertamos el dataframe en una tabla llamada 'ventas_limpias'
        # if_exists='replace' hace que la tabla se actualice cada vez que corres el script
        df.to_sql('ventas_limpias', conexion, if_exists='replace', index=False)
        
        # Cerramos la conexión
        conexion.close()
        print("    -> Datos cargados exitosamente en la tabla SQL.")
    except Exception as e:
        print(f"    -> ERROR al cargar en la base de datos: {e}")

# === EJECUCIÓN PRINCIPAL DEL PIPELINE ===
if __name__ == "__main__":
    ruta_entrada = 'data/ventas_crudas_semestre.csv'
    ruta_csv_salida = 'data/ventas_limpias_mayo.csv'
    ruta_db_salida = 'data/ventas_pyme.db'
    
    # 1. Extraer
    df_crudo = extraer_datos(ruta_entrada)
    print("Datos crudos:\n", df_crudo.head(7))
    
    # 2. Transformar
    df_limpio = transformar_datos(df_crudo)
    
    # 3. Cargar
    cargar_datos(df_limpio, ruta_csv_salida, ruta_db_salida)
    
    print("\n¡Pipeline ETL ejecutado con éxito!")