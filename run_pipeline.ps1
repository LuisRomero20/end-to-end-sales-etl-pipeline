# ============================================================
#  run_pipeline.ps1  -  Pipeline automatico diario
#  Ejecuta: ETL -> Forecast -> Log de resultado
# ============================================================

$ErrorActionPreference = "Stop"

$PYTHON   = "C:\Python313\python.exe"
$PROYECTO = "C:\Users\Luis Romero\Documents\Proyectos\Proyecto_01_ETL_Ventas"
$LOG      = "$PROYECTO\data\scheduler_log.txt"

Set-Location $PROYECTO

function Write-Log($msg) {
    $linea = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
    Add-Content -Path $LOG -Value $linea
    Write-Host $linea
}

Write-Log "======================================================"
Write-Log "  PIPELINE PROGRAMADO - INICIO"
Write-Log "======================================================"

# --- PASO 1: ETL ---
Write-Log "Ejecutando ETL..."
& $PYTHON "$PROYECTO\etl_ventas.py"
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: ETL fallo con codigo $LASTEXITCODE. Pipeline detenido."
    exit 1
}
Write-Log "ETL completado OK."

# --- PASO 2: Forecast ---
Write-Log "Ejecutando modelo de forecasting..."
& $PYTHON "$PROYECTO\modelo_forecast.py"
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: Forecast fallo con codigo $LASTEXITCODE."
    exit 1
}
Write-Log "Forecast completado OK."

Write-Log "======================================================"
Write-Log "  PIPELINE PROGRAMADO - COMPLETADO"
Write-Log "======================================================"
