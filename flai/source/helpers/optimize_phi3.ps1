# optimize_phi3.ps1
Write-Host "⚡ OPTIMIZANDO PHI-3 MINI PARA POCA RAM" -ForegroundColor Cyan
Write-Host "="*50

# 1. Crear configuración optimizada
$configContent = @"
FROM phi3:mini

# Optimizaciones para poca RAM
PARAMETER num_ctx 2048           # Contexto reducido (ahorra RAM)
PARAMETER num_batch 256          # Batch pequeño
PARAMETER num_threads 4          # Usar 4 núcleos máximo
PARAMETER repeat_penalty 1.1
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"@

# Guardar configuración
$configContent | Out-File -FilePath "phi3-optimized.Modelfile" -Encoding UTF8

Write-Host "1. Configuración creada: phi3-optimized.Modelfile" -ForegroundColor Green

# 2. Crear modelo optimizado
Write-Host "2. Creando modelo optimizado..." -ForegroundColor Yellow
ollama create phi3-optimized -f "phi3-optimized.Modelfile"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Modelo optimizado creado: phi3-optimized" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Usando modelo estándar con opciones runtime" -ForegroundColor Yellow
}

# 3. Probar
Write-Host "3. Probando modelo optimizado..." -ForegroundColor Yellow
$testPrompt = "Responde brevemente: ¿Qué es Python?"
ollama run phi3-optimized $testPrompt

Write-Host "`n🎉 Optimización completada!" -ForegroundColor Green
Write-Host "Uso:" -ForegroundColor Cyan
Write-Host "  ollama run phi3-optimized 'tu pregunta'"
Write-Host "  ollama run phi3:mini --options 'num_ctx=2048,num_threads=4'"