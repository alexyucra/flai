# install_deepseek_only.ps1
Write-Host "🚀 INSTALANDO DEEPSEEK-CODER 1.3B" -ForegroundColor Cyan
Write-Host "="*50

# 1. Verificar que Ollama está corriendo
Write-Host "1. Verificando Ollama..." -ForegroundColor Yellow
try {
    $ollamaCheck = ollama list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ollama no responde" -ForegroundColor Red
        Write-Host "💡 Asegúrate de tener 'ollama serve' corriendo en otra terminal" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "   ✅ Ollama funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

# 1. Verificar espacio libre
Write-Host "1. Verificando espacio..." -ForegroundColor Yellow
$ollamaDir = "$env:USERPROFILE\.ollama"
if (Test-Path $ollamaDir) {
    $size = (Get-ChildItem $ollamaDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "   📦 Espacio usado por Ollama: $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
}

# 2. Descargar DeepSeek-Coder 1.3B
Write-Host "`n2. Descargando DeepSeek-Coder 1.3b..." -ForegroundColor Green
ollama pull deepseek-coder:1.3b

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ Error en descarga" -ForegroundColor Red
    exit 1
}

# 3. Crear versión optimizada para poca RAM
Write-Host "`n3. Creando versión optimizada..." -ForegroundColor Green
$modelfile = @"
FROM deepseek-coder:1.3b

# OPTIMIZACIÓN PARA POCA RAM (<2GB)
PARAMETER num_ctx 1024           # Contexto reducido
PARAMETER num_batch 128          # Batch pequeño
PARAMETER num_threads 3          # 3 hilos máximo
PARAMETER num_predict 256        # Respuestas cortas
PARAMETER temperature 0.8
PARAMETER repeat_penalty 1.1
PARAMETER top_k 40
PARAMETER top_p 0.95
"@ | Out-File -FilePath "$env:TEMP\flai-coder.Modelfile" -Encoding UTF8

ollama create flai-coder -f "$env:TEMP\flai-coder.Modelfile"

# 4. Probar
Write-Host "`n4. Probando modelo optimizado..." -ForegroundColor Green
ollama run flai-coder "def hello(): print('world')"

# 5. Verificar
Write-Host "`n5. Verificando instalación..." -ForegroundColor Yellow
ollama list

Write-Host "`n🎉 INSTALACIÓN COMPLETADA!" -ForegroundColor Cyan
Write-Host "="*50
Write-Host "Modelos disponibles:" -ForegroundColor Green
ollama list

Write-Host "`n💡 USO:" -ForegroundColor Yellow
Write-Host "   • ollama run deepseek-opt 'tu pregunta'" -ForegroundColor Green
Write-Host "   • Para Flai: flai init deepseek-opt --path app" -ForegroundColor Green