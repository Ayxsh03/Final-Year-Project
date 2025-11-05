#!/usr/bin/env bash
#
# Local Development Setup Script for FpelAICCTV
# Run this to prepare your environment for local development
#

set -euo pipefail

echo "============================================"
echo "FpelAICCTV - Local Development Setup"
echo "============================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
    if [ "$PYTHON_VERSION" = "3.12" ]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ ERROR: Python 3.12 is required but not found!"
    echo "   Install Python 3.12 first:"
    echo "   - macOS: brew install python@3.12"
    echo "   - Ubuntu: sudo apt install python3.12"
    exit 1
fi

echo "✓ Found $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js not found!"
    echo "   Install Node.js 20+ from https://nodejs.org/"
    exit 1
fi

echo "✓ Found Node.js"
node --version
npm --version
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p backend/static
mkdir -p backend/images
mkdir -p backend/logs
mkdir -p images
mkdir -p logs
echo "✓ Directories created"
echo ""

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel
echo "✓ pip upgraded"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Verify OpenCV is headless
echo "Verifying OpenCV installation..."
OPENCV_CHECK=$(pip list | grep opencv || true)
if echo "$OPENCV_CHECK" | grep -q "opencv-python-headless"; then
    echo "✓ opencv-python-headless installed correctly"
elif echo "$OPENCV_CHECK" | grep -q "opencv-python"; then
    echo "⚠️  Found opencv-python (GUI version), switching to headless..."
    pip uninstall -y opencv-python opencv-contrib-python
    pip install opencv-python-headless==4.10.0.84
    echo "✓ Switched to opencv-python-headless"
else
    echo "❌ OpenCV not found, installing headless version..."
    pip install opencv-python-headless==4.10.0.84
fi
echo ""

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install
echo "✓ Node.js dependencies installed"
echo ""

# Build frontend
echo "Building frontend..."
npm run build
echo "✓ Frontend built"
echo ""

# Copy frontend to backend/static
echo "Copying frontend to backend/static..."
rm -rf backend/static/*
cp -r dist/* backend/static/
if [ -f "backend/static/index.html" ]; then
    echo "✓ Frontend copied to backend/static/"
else
    echo "❌ ERROR: index.html not found in backend/static!"
    exit 1
fi
echo ""

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Setting up .env file..."
    cp .env.example .env
    echo "✓ .env created from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and configure your settings!"
    echo "   Required settings:"
    echo "   - DATABASE_URL (PostgreSQL connection string)"
    echo "   - API_KEY (change default key)"
    echo ""
else
    echo "✓ .env already exists"
    echo ""
fi

# Check for YOLO model
if [ ! -f "yolov8n.pt" ]; then
    echo "⚠️  WARNING: yolov8n.pt model file not found!"
    echo "   The detection worker will download it automatically on first run."
    echo "   Or download manually from: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
    echo ""
fi

echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment:"
echo "   nano .env"
echo ""
echo "2. Setup database (if using local PostgreSQL):"
echo "   psql -U postgres -d detection_db < database/schema.sql"
echo ""
echo "3. Start the development server:"
echo "   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "4. Or use Docker Compose:"
echo "   docker-compose up"
echo ""
echo "5. Access the application:"
echo "   Frontend & API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "6. Run detection worker (separate terminal):"
echo "   python detection_integration/multi_camera_detector.py"
echo ""
echo "For deployment to Azure or production servers, see:"
echo "   DEPLOYMENT_GUIDE.md"
echo ""
