#!/bin/bash
set -e

echo "🚀 Starting Agentic Analyst..."

# Wait for database if using PostgreSQL
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "⏳ Waiting for PostgreSQL..."
    until pg_isready -d "$DATABASE_URL" -t 1 2>/dev/null; do
        sleep 1
    done
    echo "✅ PostgreSQL is ready"
fi

# Create necessary directories
mkdir -p /app/agents/charts /app/logs

# Run database migrations if needed (uncomment if using Alembic)
# echo "📦 Running database migrations..."
# alembic upgrade head

echo "🎯 Starting FastAPI server..."
exec "$@"