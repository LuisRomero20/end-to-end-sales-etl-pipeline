# 📊 Pipeline ETL y Dashboard de Ventas (End-to-End)

## 📌 Descripción del Proyecto
Este es un proyecto de Ingeniería y Análisis de Datos diseñado para resolver un problema clásico en las PYMES: la limpieza manual de reportes de ventas diarios y la falta de visibilidad en tiempo real de los ingresos.

El proyecto automatiza la ingesta de datos sucios (CSVs con errores humanos, nulos y formatos inconsistentes), los procesa mediante un pipeline en Python, los almacena en una base de datos relacional y los conecta a un dashboard interactivo para la toma de decisiones.

## 🛠️ Stack Tecnológico
* **Extracción y Transformación (ETL):** Python (Pandas)
* **Base de Datos (Load):** SQLite
* **Visualización de Datos:** Power BI

## ⚙️ Arquitectura del Pipeline
1. **Extract:** Lectura de archivos CSV crudos tolerando errores de delimitación y comillas invasoras.
2. **Transform:** * Eliminación de registros duplicados.
   * Imputación de valores nulos (Cantidades vacías asumen valor 1).
   * Filtrado de anomalías (Cantidades negativas).
   * Estandarización de fechas (Casteo dinámico a `YYYY-MM-DD`).
3. **Load:** Inserción de datos limpios automatizada a una base de datos local `SQLite`.
4. **Visualize:** Conexión de Power BI a la base de datos vía Python Scripting para generar métricas clave (Ingresos Totales, Tendencia de Ventas, Rendimiento por Producto).

## 🚀 Cómo ejecutarlo
1. Clona este repositorio.
2. Instala las dependencias: `pip install pandas matplotlib`.
3. Ejecuta `generar_data.py` para simular la data cruda de todo un semestre.
4. Ejecuta `etl_ventas.py` para limpiar los datos y cargar la base de datos.
5. Abre `Proyecto_01_Dashboard_Ventas.pbix` y actualiza las fuentes de datos.