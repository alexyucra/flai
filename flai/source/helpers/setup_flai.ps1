# setup_flai.ps1
Write-Host "🚀 CONFIGURANDO FLAI CON DEEPSEEK-CODER" -ForegroundColor Cyan

# 1. Verificar Ollama
Write-Host "`n1. Verificando Ollama..." -ForegroundColor Yellow
ollama list
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ollama no responde" -ForegroundColor Red
    Write-Host "💡 Asegúrate de tener 'ollama serve' corriendo en otra terminal" -ForegroundColor Yellow
    exit 1
}

# 2. Descargar modelo si no existe
Write-Host "`n2. Verificando DeepSeek-Coder..." -ForegroundColor Yellow
$hasModel = ollama list | Select-String "deepseek-coder:1.3b"
if (-not $hasModel) {
    Write-Host "📥 Descargando modelo..." -ForegroundColor Green
    ollama pull deepseek-coder:1.3b
}

# 3. Navegar a proyecto
Write-Host "`n3. Configurando Flai..." -ForegroundColor Yellow
Set-Location "C:\Users\ThinkPad\Documents\python\mvc"

# 4. Inicializar Flai
python -m flai.cli init deepseek-coder --path app

Write-Host "`n🎉 ¡CONFIGURACIÓN COMPLETADA!" -ForegroundColor Green
Write-Host "Comandos disponibles:" -ForegroundColor Cyan
Write-Host "  flai analyze app          # Analizar proyecto"
Write-Host "  flai chat --project app   # Chat con AI"
Write-Host "  ollama run deepseek-coder:1.3b 'tu pregunta'  # Directo con Ollama"