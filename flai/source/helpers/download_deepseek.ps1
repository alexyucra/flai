# Script completo de descarga
Write-Host "📥 DESCARGANDO DEEPSEEK-CODER 1.3B" -ForegroundColor Cyan
Write-Host "="*50

# 1. Verificar espacio
$freeSpace = (Get-PSDrive C).Free / 1GB
Write-Host "1. Espacio libre en C: $([math]::Round($freeSpace, 2)) GB"

if ($freeSpace -lt 2) {
    Write-Host "⚠️  Espacio bajo (<2GB)" -ForegroundColor Yellow
}

# 2. Descargar
Write-Host "2. Descargando modelo..." -ForegroundColor Yellow
ollama pull deepseek-coder:1.3b

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Descarga completada!" -ForegroundColor Green
} else {
    Write-Host "❌ Error en descarga" -ForegroundColor Red
}

# 3. Verificar
Write-Host "3. Verificando..." -ForegroundColor Yellow
ollama list | Select-String "deepseek-coder"