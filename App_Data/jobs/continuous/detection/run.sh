#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Starting Detection Worker (WebJob)"
echo "========================================"

# Ensure necessary directories exist
mkdir -p /home/images
mkdir -p /home/logs

# Move to site root (where code is deployed)
cd "$HOME/site/wwwroot"

# Export environment variables for detection worker
# These should match your Azure App Service Configuration
export IMAGES_DIR=${IMAGES_DIR:-/home/images}
export API_BASE_URL=${API_BASE_URL:-http://localhost:8000/api/v1}
export API_KEY=${API_KEY:-111-1111-1-11-1-11-1-1}
export CONFIDENCE_THRESHOLD=${CONFIDENCE_THRESHOLD:-0.5}
export DETECTION_WIDTH=${DETECTION_WIDTH:-640}
export DETECTION_HEIGHT=${DETECTION_HEIGHT:-480}
export FRAME_STRIDE=${FRAME_STRIDE:-5}
export EVENT_COOLDOWN_SECONDS=${EVENT_COOLDOWN_SECONDS:-5}
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH

# Verify the YOLO model file exists
if [ ! -f "yolov8n.pt" ]; then
    echo "ERROR: yolov8n.pt not found at $HOME/site/wwwroot/"
    if [ -f "detection_integration/yolov8n.pt" ]; then
        echo "Copying model from detection_integration/"
        cp detection_integration/yolov8n.pt .
    else
        echo "FATAL: Cannot find yolov8n.pt model file!"
        exit 1
    fi
fi

echo "Model file verified: yolov8n.pt"
echo "API Base URL: $API_BASE_URL"
echo "Images Directory: $IMAGES_DIR"
echo "Starting detection worker..."
echo "========================================"

# Start the detection worker
# -u flag ensures unbuffered output for logging
exec python3 -u detection_integration/multi_camera_detector.py
