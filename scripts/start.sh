#!/bin/bash

echo "🚀 Starting AI Knowledge & Incident Management Platform..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
until pg_isready -h db -p 5432 -U demouser; do
  echo "Database is unavailable - sleeping..."
  sleep 2
done
echo "✅ Database is ready!"

# Wait for Redis
echo "⏳ Waiting for Redis..."
until redis-cli -h redis -p 6379 ping; do
  echo "Redis is unavailable - sleeping..."
  sleep 2
done
echo "✅ Redis is ready!"

# Wait for ChromaDB
echo "⏳ Waiting for ChromaDB..."
until curl -f http://chromadb:8000/api/v1/heartbeat; do
  echo "ChromaDB is unavailable - sleeping..."
  sleep 2
done
echo "✅ ChromaDB is ready!"

# Wait for Ollama (this might take longer for model download)
echo "⏳ Waiting for Ollama..."
for i in {1..60}; do
  if curl -f http://ollama:11434/api/tags; then
    echo "✅ Ollama is ready!"
    break
  fi
  echo "Ollama is unavailable - sleeping ($i/60)..."
  sleep 5
done

# Run database migrations (if any)
echo "📊 Running database setup..."
python -c "
import asyncio
import sys
sys.path.append('/app/src')
from database import init_db
asyncio.run(init_db())
"

echo "🎯 Starting FastAPI application..."
cd /app
exec uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload