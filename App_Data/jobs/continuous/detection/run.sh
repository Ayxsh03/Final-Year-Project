#!/usr/bin/env bash
set -euo pipefail

# Ensure images directory exists on the persistent disk
mkdir -p /home/images

# Move to site root (where code is deployed)
cd "$HOME/site/wwwroot"

# If your script needs a model file, ensure path correct (yolov8n.pt is at repo root)
# Export same env vars the backend uses (App Service sets them globally)
export IMAGES_DIR=${IMAGES_DIR:-/home/images}

# Start the worker
exec python3 -u detection_integration/multi_camera_detector.py
