#!/bin/bash

# Script para iniciar a aplicação FastAPI
# Pode ser usado localmente ou no ambiente de deploy

# Definir a porta padrão se não estiver definida
export PORT=${PORT:-8000}

echo "Iniciando API de Análise de Sentimentos na porta $PORT"

# Iniciar o servidor Uvicorn
uvicorn main:app --host=0.0.0.0 --port=$PORT --log-level=info
