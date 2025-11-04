#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Starting FpelAICCTV Azure Deployment"
echo "========================================"

# Create necessary directories with proper permissions
mkdir -p /home/images
mkdir -p /home/logs
chmod 755 /home/images
chmod 755 /home/logs

# Navigate to the application root
cd /home/site/wwwroot

# Export environment variables with defaults
export IMAGES_DIR=${IMAGES_DIR:-/home/images}
export STATIC_DIR=${STATIC_DIR:-/home/site/wwwroot/backend/static}
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH

# Verify critical files exist
echo "Verifying deployment files..."
if [ ! -f "backend/main.py" ]; then
    echo "ERROR: backend/main.py not found!"
    exit 1
fi

if [ ! -f "yolov8n.pt" ]; then
    echo "WARNING: yolov8n.pt not found at root. Checking detection_integration/"
    if [ -f "detection_integration/yolov8n.pt" ]; then
        echo "Copying YOLO model to root directory..."
        cp detection_integration/yolov8n.pt .
    else
        echo "ERROR: yolov8n.pt not found in either location!"
        echo "Detection system may not work properly."
    fi
fi

if [ ! -d "backend/static" ]; then
    echo "WARNING: backend/static directory not found. Frontend may not load."
fi

# Install Python dependencies if not already done
if [ -f "requirements.txt" ]; then
    echo "Ensuring Python dependencies are installed..."
    pip install --no-cache-dir -r requirements.txt > /home/logs/pip-install.log 2>&1
    echo "Dependencies installed."
fi

echo "Environment configured successfully."
echo "Starting FastAPI application on port 8000..."
echo "========================================"

# Start the FastAPI application
# Azure App Service expects the main process to run in foreground
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
