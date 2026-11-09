#!/bin/bash
# Script de otimização para Linux/macOS

BASE_MODEL=${1:-"deepseek-coder:1.3b"}
CUSTOM_NAME=${2:-"flai-coder"}

echo "--- OTIMIZANDO MODELO: $BASE_MODEL -> $CUSTOM_NAME ---"

# Criar Modelfile temporário
MODELFILE_PATH="/tmp/flai-coder.Modelfile"

cat > "$MODELFILE_PATH" << EOF
FROM $BASE_MODEL
PARAMETER num_ctx 1024
PARAMETER num_batch 128
PARAMETER num_predict 256
PARAMETER temperature 0.8
PARAMETER repeat_penalty 1.1
EOF

# Criar modelo no Ollama
echo "Gerando versão otimizada no Ollama..."
ollama create "$CUSTOM_NAME" -f "$MODELFILE_PATH"

if [ $? -eq 0 ]; then
    echo "SUCESSO: Modelo $CUSTOM_NAME criado!"
    exit 0
else
    echo "ERRO: O Ollama não conseguiu processar o Modelfile."
    exit 1
fi