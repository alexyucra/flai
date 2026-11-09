# Script de verificación completo
Write-Host "🔍 VERIFICACIÓN COMPLETA" -ForegroundColor Cyan
Write-Host "="*50

# 1. Ollama
Write-Host "1. Ollama:" -ForegroundColor Yellow
ollama --version
if ($LASTEXITCODE -eq 0) { Write-Host "   ✅ OK" -ForegroundColor Green }

# 2. Servicio
Write-Host "2. Servicio:" -ForegroundColor Yellow
ollama list
if ($LASTEXITCODE -eq 0) { 
    Write-Host "   ✅ Servicio funcionando" -ForegroundColor Green 
} else {
    Write-Host "   ❌ Servicio no responde" -ForegroundColor Red
}

# 3. Modelos
Write-Host "3. Modelos instalados:" -ForegroundColor Yellow
$models = ollama list
Write-Host "   $models"

# 4. DeepSeek-Coder específico
Write-Host "4. DeepSeek-Coder 1.3B:" -ForegroundColor Yellow
if ($models -match "deepseek-coder:1.3b") {
    Write-Host "   ✅ Instalado" -ForegroundColor Green
    
    # Test rápido
    Write-Host "5. Test rápido del modelo:" -ForegroundColor Yellow
    echo "print('Hello')" | ollama run deepseek-coder:1.3b "¿Qué hace este código Python?"
    
} else {
    Write-Host "   ❌ No instalado" -ForegroundColor Red
    Write-Host "   💡 Ejecuta: ollama pull deepseek-coder:1.3b" -ForegroundColor Yellow
}

Write-Host "`n🎉 Verificación completada!" -ForegroundColor Green