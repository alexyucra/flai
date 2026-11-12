# flai/cli/helper/optimize_model.ps1
param (
    [string]$BaseModel = "qwen2.5-coder:3b",
    [string]$CustomName = "flai-coder"
)

Write-Host "--- OTIMIZANDO MODELO: $BaseModel -> $CustomName ---" -ForegroundColor Cyan

# 1. Definir o caminho do Modelfile
$modelfilePath = "$env:TEMP\flai-coder.Modelfile"

# 2. Criar o conteúdo do Modelfile
# Removidos parâmetros problemáticos como num_threads que devem ser via CLI/Env
$modelfileContent = @"
FROM $BaseModel
PARAMETER num_ctx 4096
PARAMETER num_batch 256
PARAMETER num_predict 768
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.05
"@

# 3. Salvar o arquivo de forma limpa (Encoding ASCII evita problemas de leitura no Ollama)
Set-Content -Path $modelfilePath -Value $modelfileContent -Encoding Ascii

# 4. Criar o modelo no Ollama
Write-Host "Gerando versao otimizada no Ollama..." -ForegroundColor Yellow
ollama create $CustomName -f $modelfilePath

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCESSO: Modelo $CustomName criado!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "ERRO: O Ollama nao conseguiu processar o Modelfile." -ForegroundColor Red
    exit 1
}