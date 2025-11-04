#!/usr/bin/env bash

# Don't exit on error immediately - we want to log issues
set -u

echo "========================================"
echo "FpelAICCTV Startup Script"
echo "Time: $(date)"
echo "========================================"

# Create directories
echo "Creating directories..."
mkdir -p /home/images 2>&1 || echo "Warning: Could not create /home/images"
mkdir -p /home/logs 2>&1 || echo "Warning: Could not create /home/logs"

# Navigate to app root
echo "Navigating to /home/site/wwwroot..."
cd /home/site/wwwroot || {
    echo "FATAL: Cannot access /home/site/wwwroot"
    exit 1
}

echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la | head -20

# Set environment variables
echo "Setting environment variables..."
export IMAGES_DIR=${IMAGES_DIR:-/home/images}
export STATIC_DIR=${STATIC_DIR:-/home/site/wwwroot/backend/static}
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot

# Check critical files
echo "Checking critical files..."
if [ -f "backend/main.py" ]; then
    echo "✓ backend/main.py found"
else
    echo "✗ ERROR: backend/main.py not found!"
    echo "Listing backend directory:"
    ls -la backend/ 2>&1 || echo "backend/ directory not found"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt found"
else
    echo "✗ WARNING: requirements.txt not found"
fi

if [ -d "backend/static" ]; then
    echo "✓ backend/static directory found"
    echo "Static files count: $(find backend/static -type f 2>/dev/null | wc -l)"
else
    echo "✗ WARNING: backend/static not found - frontend may not load"
fi

# Check Python
echo "Checking Python..."
which python || which python3 || {
    echo "ERROR: Python not found!"
    exit 1
}
python --version 2>&1 || python3 --version 2>&1

# Try to start the app
echo "========================================"
echo "Starting FastAPI application..."
echo "Command: python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo "========================================"

# Start uvicorn - let it handle errors
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info
