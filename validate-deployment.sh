#!/usr/bin/env bash
#
# Deployment Validation Script
# Checks if the project is ready for Linux deployment
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}FpelAICCTV - Deployment Validation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check 1: Python version alignment
echo -e "${BLUE}[1/12] Checking Python version alignment...${NC}"
RUNTIME_VERSION=$(grep -o "python-[0-9.]*" runtime.txt | cut -d'-' -f2)
DOCKERFILE_VERSION=$(grep "FROM python:" backend/Dockerfile | cut -d':' -f2 | cut -d'-' -f1)

if [ "$RUNTIME_VERSION" = "$DOCKERFILE_VERSION" ]; then
    echo -e "${GREEN}✓ Python versions match: $RUNTIME_VERSION${NC}"
else
    echo -e "${RED}✗ Python version mismatch!${NC}"
    echo "  runtime.txt: $RUNTIME_VERSION"
    echo "  Dockerfile: $DOCKERFILE_VERSION"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: NumPy versions aligned
echo -e "${BLUE}[2/12] Checking NumPy version consistency...${NC}"
ROOT_NUMPY=$(grep "numpy" requirements.txt || echo "not found")
BACKEND_NUMPY=$(grep "numpy" backend/requirements.txt || echo "not found")

if [ "$ROOT_NUMPY" = "$BACKEND_NUMPY" ]; then
    echo -e "${GREEN}✓ NumPy versions match${NC}"
    echo "  $ROOT_NUMPY"
else
    echo -e "${RED}✗ NumPy versions differ!${NC}"
    echo "  Root: $ROOT_NUMPY"
    echo "  Backend: $BACKEND_NUMPY"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 3: OpenCV headless in requirements
echo -e "${BLUE}[3/12] Checking OpenCV configuration...${NC}"
if grep -q "opencv-python-headless" requirements.txt && grep -q "opencv-python-headless" backend/requirements.txt; then
    echo -e "${GREEN}✓ OpenCV is headless in both requirements files${NC}"
else
    echo -e "${RED}✗ OpenCV not configured as headless!${NC}"
    grep "opencv" requirements.txt backend/requirements.txt || true
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 4: Dockerfile has minimal dependencies
echo -e "${BLUE}[4/12] Checking Dockerfile dependencies...${NC}"
if grep -q "libgl1\|libgtk" backend/Dockerfile; then
    echo -e "${YELLOW}⚠ Dockerfile contains GUI dependencies (libgl1/libgtk)${NC}"
    echo "  These are not needed for opencv-python-headless"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Dockerfile has minimal dependencies${NC}"
fi
echo ""

# Check 5: startup.sh is executable
echo -e "${BLUE}[5/12] Checking file permissions...${NC}"
if [ -x "startup.sh" ]; then
    echo -e "${GREEN}✓ startup.sh is executable${NC}"
else
    echo -e "${RED}✗ startup.sh is not executable${NC}"
    echo "  Run: chmod +x startup.sh"
    ERRORS=$((ERRORS + 1))
fi

if [ -x "App_Data/jobs/continuous/detection/run.sh" ]; then
    echo -e "${GREEN}✓ WebJob run.sh is executable${NC}"
else
    echo -e "${YELLOW}⚠ WebJob run.sh is not executable${NC}"
    echo "  Run: chmod +x App_Data/jobs/continuous/detection/run.sh"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 6: .env exists
echo -e "${BLUE}[6/12] Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    
    # Check for default API key
    if grep -q "API_KEY=111-1111-1-11-1-11-1-1" .env; then
        echo -e "${YELLOW}⚠ Using default API_KEY - change this for production!${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "  Create from template: cp .env.example .env"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 7: .gitignore is comprehensive
echo -e "${BLUE}[7/12] Checking .gitignore...${NC}"
if grep -q "node_modules" .gitignore && grep -q "__pycache__" .gitignore && grep -q "\.env" .gitignore; then
    echo -e "${GREEN}✓ .gitignore includes essential exclusions${NC}"
else
    echo -e "${RED}✗ .gitignore is incomplete${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 8: Frontend build directory exists
echo -e "${BLUE}[8/12] Checking frontend build...${NC}"
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo -e "${GREEN}✓ Frontend build exists (dist/)${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not built (dist/ missing)${NC}"
    echo "  Run: npm run build"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "backend/static/index.html" ]; then
    echo -e "${GREEN}✓ Frontend copied to backend/static/${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not in backend/static/${NC}"
    echo "  For local dev: cp -r dist/* backend/static/"
    echo "  (GitHub Actions handles this for Azure)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 9: YOLO model exists
echo -e "${BLUE}[9/12] Checking YOLO model...${NC}"
if [ -f "yolov8n.pt" ]; then
    echo -e "${GREEN}✓ yolov8n.pt found${NC}"
elif [ -f "detection_integration/yolov8n.pt" ]; then
    echo -e "${GREEN}✓ yolov8n.pt found in detection_integration/${NC}"
else
    echo -e "${YELLOW}⚠ yolov8n.pt not found${NC}"
    echo "  Will auto-download on first detection run"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 10: Database schema exists
echo -e "${BLUE}[10/12] Checking database schema...${NC}"
if [ -f "database/schema.sql" ]; then
    echo -e "${GREEN}✓ database/schema.sql found${NC}"
else
    echo -e "${RED}✗ database/schema.sql missing${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 11: WebJob uses 'python' not 'python3'
echo -e "${BLUE}[11/12] Checking WebJob script...${NC}"
if grep -q "exec python -u" App_Data/jobs/continuous/detection/run.sh; then
    echo -e "${GREEN}✓ WebJob uses 'python' command (Azure compatible)${NC}"
elif grep -q "exec python3 -u" App_Data/jobs/continuous/detection/run.sh; then
    echo -e "${RED}✗ WebJob uses 'python3' - should be 'python' for Azure${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${YELLOW}⚠ Could not verify WebJob python command${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 12: Required files exist
echo -e "${BLUE}[12/12] Checking required files...${NC}"
REQUIRED_FILES=(
    "backend/main.py"
    "requirements.txt"
    "backend/requirements.txt"
    "runtime.txt"
    "startup.sh"
    "docker-compose.yml"
    "backend/Dockerfile"
    ".env.example"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ All required files present${NC}"
else
    ERRORS=$((ERRORS + MISSING))
fi
echo ""

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}============================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Your project is ready for deployment to:"
    echo "  ✓ Azure App Service"
    echo "  ✓ Docker Compose"
    echo "  ✓ Bare metal Linux server"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env configuration"
    echo "  2. Deploy: git push origin main (for Azure)"
    echo "  3. Or: docker-compose up (for Docker)"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo "  Review warnings above before deploying"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found${NC}"
    echo "  Fix errors before deploying!"
    echo ""
    exit 1
fi
