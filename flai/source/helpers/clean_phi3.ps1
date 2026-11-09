# clean_phi3.ps1
Write-Host "🧹 DESINSTALANDO PHI-3 MINI" -ForegroundColor Cyan
Write-Host "="*50

# 1. Ver modelos actuales
Write-Host "1. Modelos instalados:" -ForegroundColor Yellow
$models = ollama list
Write-Host $models

# 2. Verificar que phi3:mini existe
if ($models -match "phi3:mini") {
    Write-Host "`n✅ Phi-3 Mini encontrado" -ForegroundColor Green
    
    # 3. Eliminar
    Write-Host "2. Eliminando Phi-3 Mini..." -ForegroundColor Yellow
    ollama rm phi3:mini --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Phi-3 Mini eliminado" -ForegroundColor Green
        
        # 4. Limpiar espacio
        Write-Host "3. Limpiando espacio..." -ForegroundColor Yellow
        ollama prune
        
        # 5. Verificar
        Write-Host "4. Verificando..." -ForegroundColor Yellow
        $newModels = ollama list
        Write-Host $newModels
        
        # 6. Calcular espacio liberado
        if ($models -match "2\.2 GB") {
            Write-Host "`n🎉 Espacio liberado: ~2.2 GB" -ForegroundColor Green
        }
    } else {
        Write-Host "   ❌ Error eliminando Phi-3" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️  Phi-3 Mini no está instalado" -ForegroundColor Yellow
}

# 7. Recomendar DeepSeek-Coder
Write-Host "`n💡 RECOMENDACIÓN:" -ForegroundColor Cyan
Write-Host "   Ahora puedes instalar DeepSeek-Coder 1.3B:" -ForegroundColor Yellow
Write-Host "   ollama pull deepseek-coder:1.3b" -ForegroundColor Green