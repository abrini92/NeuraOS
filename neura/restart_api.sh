#!/bin/bash

echo "🔄 Redémarrage de Neura API..."

# Trouver et tuer le processus uvicorn sur port 8000
PID=$(lsof -ti:8000)

if [ -n "$PID" ]; then
    echo "✓ Arrêt de l'API (PID: $PID)..."
    kill -9 $PID
    sleep 2
else
    echo "ℹ Aucune API en cours sur port 8000"
fi

# Relancer l'API
echo "🚀 Démarrage de l'API..."
cd /Users/abderrahim/Desktop/Neura/neura
poetry run uvicorn neura.core.api:app --reload --port 8000
