# save as: install_deepseek_optimized.ps1
Write-Host "🚀 INSTALANDO DEEPSEEK-CODER 1.3B OPTIMIZADO" -ForegroundColor Cyan
Write-Host "="*50

# Verificar RAM
$ramAvailable = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
Write-Host "📊 RAM disponible: $ramAvailable GB" -ForegroundColor Yellow

if ($ramAvailable -lt 1.5) {
    Write-Host "⚠️  RAM MUY BAJA (<1.5 GB)" -ForegroundColor Red
    Write-Host "   Usando configuración ULTRA-OPTIMIZADA" -ForegroundColor Yellow
}

# Descargar base
Write-Host "`n1. Descargando DeepSeek-Coder 1.3b..." -ForegroundColor Green
ollama pull deepseek-coder:1.3b

# Configuración según RAM
if ($ramAvailable -lt 1.5) {
    $config = @"
FROM deepseek-coder:1.3b
PARAMETER num_ctx 512
PARAMETER num_batch 64
PARAMETER num_threads 2
PARAMETER num_predict 128
PARAMETER temperature 0.7
"@
    $modelName = "deepseek-ultralow"
} else {
    $config = @"
FROM deepseek-coder:1.3b  
PARAMETER num_ctx 2048
PARAMETER num_batch 256
PARAMETER num_threads 4
PARAMETER num_predict 512
PARAMETER temperature 0.8
"@
    $modelName = "deepseek-optimized"
}

# Crear modelo optimizado
Write-Host "`n2. Creando modelo optimizado: $modelName" -ForegroundColor Green
$config | Out-File -FilePath "$modelName.Modelfile" -Encoding UTF8
ollama create $modelName -f "$modelName.Modelfile"

# Probar
Write-Host "`n3. Probando modelo..." -ForegroundColor Green
ollama run $modelName "def suma(a,b): return a+b"

Write-Host "`n🎉 INSTALACIÓN COMPLETADA!" -ForegroundColor Cyan
Write-Host "Modelo: $modelName" -ForegroundColor Yellow
Write-Host "Uso: ollama run $modelName 'tu pregunta'" -ForegroundColor Green