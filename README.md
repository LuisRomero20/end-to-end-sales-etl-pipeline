# 📊 Pipeline ETL + Forecasting + Dashboard de Ventas (End-to-End)

## 📌 Descripción del Proyecto
Proyecto de Ingeniería y Análisis de Datos end-to-end diseñado para resolver un problema clásico en las PYMES: la limpieza manual de reportes de ventas y la falta de visibilidad en tiempo real de los ingresos.

El proyecto automatiza la ingesta de datos sucios (CSVs con errores humanos, nulos y formatos inconsistentes), los procesa mediante un pipeline en Python, entrena un modelo de forecasting con Prophet para predecir los próximos 30 días de ingresos, y expone todo en un dashboard web interactivo accesible desde el navegador.

## 🌐 Demo en vivo
**[Ver Dashboard →](https://end-to-end-sales-etl-pipeline-6ao8esedhqua4app97w2o2g.streamlit.app/)**

## 🛠️ Stack Tecnológico
| Capa | Tecnología |
|---|---|
| Extracción y Transformación (ETL) | Python · Pandas |
| Base de Datos (Load) | SQLite |
| Forecasting / ML | Prophet (Meta) |
| Dashboard Web | Streamlit · Plotly |
| Automatización | Windows Task Scheduler · PowerShell |
| Visualización Ejecutiva | Power BI |

## ⚙️ Arquitectura del Pipeline

```
generar_data.py ──► etl_ventas.py ──► modelo_forecast.py ──► app.py (Streamlit)
                                                                    │
                                                              Power BI (.pbix)
        ▲
run_pipeline.ps1 (Task Scheduler · diario 7 AM)
```

### Etapas
1. **Extract** — Lectura de CSV con errores de delimitación, comillas invasoras y formatos mixtos.
2. **Transform**
   - Eliminación de duplicados
   - Imputación de cantidades nulas (valor `1`)
   - Filtrado de cantidades negativas
   - Estandarización de fechas a `YYYY-MM-DD` (`format='mixed'`)
   - Cálculo de `ingreso_total = cantidad × precio_unitario`
3. **Load** — Carga incremental en SQLite (solo inserta registros nuevos, nunca duplica).
4. **Forecast** — Prophet entrena sobre 181 días de historial y predice los próximos 30 días con banda de confianza.
5. **Visualize** — Dashboard Streamlit con KPIs, tendencia + forecast, ranking de productos, top clientes y tabla de transacciones. Filtros por producto, cliente, estado y rango de fechas.
6. **Automate** — `run_pipeline.ps1` orquesta ETL + Forecast. Registrado en Task Scheduler para ejecución diaria silenciosa.

## 📁 Estructura del Proyecto
```
├── generar_data.py               # Simula 2000 transacciones con datos sucios
├── etl_ventas.py                 # Pipeline ETL con logging y carga incremental
├── modelo_forecast.py            # Forecasting 30 días con Prophet → SQLite
├── app.py                        # Dashboard web con Streamlit + Plotly
├── run_pipeline.ps1              # Orquestador para automatización
├── requirements.txt              # Dependencias Python
├── Proyecto_01_Dashboard_Ventas.pbix  # Dashboard Power BI (ejecutivo)
└── data/                         # Generado en runtime (ignorado por git)
    ├── ventas_pyme.db            # SQLite: tablas ventas_limpias + ventas_forecast
    ├── ventas_limpias_mayo.csv   # Backup CSV limpio
    ├── etl_log.txt               # Log técnico del ETL y Forecast
    └── scheduler_log.txt         # Log de ejecuciones automáticas
```

## 🚀 Cómo ejecutarlo localmente
```bash
# 1. Clonar el repositorio
git clone https://github.com/LuisRomero20/end-to-end-sales-etl-pipeline.git
cd end-to-end-sales-etl-pipeline

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Generar datos simulados
python generar_data.py

# 4. Ejecutar el ETL
python etl_ventas.py

# 5. Entrenar el modelo de forecasting
python modelo_forecast.py

# 6. Lanzar el dashboard
streamlit run app.py
```

> **Streamlit Cloud:** La app se auto-inicializa sola. No requiere pasos previos.

## ⏰ Automatización
Para registrar el pipeline como tarea diaria en Windows:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "07:00"
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File run_pipeline.ps1"
Register-ScheduledTask -TaskName "ETL_Ventas_PYME" -Trigger $trigger -Action $action -Force
```
