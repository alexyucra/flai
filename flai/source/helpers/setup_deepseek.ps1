# save as: setup_deepseek.ps1
param(
    [string]$Version = "1.3b",
    [switch]$ForceDownload = $false
)

$MODEL_NAME = "deepseek-coder:$Version"
$REQUIRED_RAM = @{
    "1.3b" = "2GB";
    "6.7b" = "8GB";
    "33b" = "32GB"
}

Write-Host "🚀 CONFIGURANDO DEEPSEEK-CODER $Version" -ForegroundColor Cyan
Write-Host "="*50

# Verificar Ollama
Write-Host "1. Verificando Ollama..." -ForegroundColor Yellow
$ollamaCheck = ollama --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ollama no está instalado" -ForegroundColor Red
    Write-Host "📥 Descarga desde: https://ollama.com/download/windows" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ Ollama encontrado: $ollamaCheck" -ForegroundColor Green

# Verificar RAM recomendada
Write-Host "2. Verificando requisitos..." -ForegroundColor Yellow
$ramRequired = $REQUIRED_RAM[$Version]
Write-Host "   ℹ️  RAM recomendada: $ramRequired" -ForegroundColor Cyan

# Verificar si ya está descargado
Write-Host "3. Verificando modelo $MODEL_NAME..." -ForegroundColor Yellow
$modelExists = ollama list | Select-String $MODEL_NAME

if ($modelExists -and -not $ForceDownload) {
    Write-Host "   ✅ Modelo ya descargado" -ForegroundColor Green
} else {
    if ($modelExists -and $ForceDownload) {
        Write-Host "   🔄 Forzando redescarga..." -ForegroundColor Magenta
        ollama rm $MODEL_NAME 2>$null
    }
    
    Write-Host "   📥 Descargando $MODEL_NAME..." -ForegroundColor Yellow
    ollama pull $MODEL_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Descarga completada" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Error en la descarga" -ForegroundColor Red
        exit 1
    }
}

# Verificar modelo
Write-Host "4. Verificando modelo..." -ForegroundColor Yellow
ollama show $MODEL_NAME

Write-Host "`n🎉 CONFIGURACIÓN COMPLETADA!" -ForegroundColor Green
Write-Host "="*50
Write-Host "Modelo: $MODEL_NAME"
Write-Host "Para usar: ollama run $MODEL_NAME"
Write-Host "Ejemplo: ollama run $MODEL_NAME 'Escribe un código Python para...'"