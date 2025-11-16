#!/bin/bash
set -e

echo "Starting FastAPI Backend..."
cd "$(dirname "$0")/.."

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Run backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000