#!/bin/bash
# Verify Playwright setup and dependencies

echo "=== InvoiceFlow Testing Setup Verification ==="
echo ""

ERRORS=0

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js installed: $NODE_VERSION"
else
    echo "✗ Node.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ npm installed: $NPM_VERSION"
else
    echo "✗ npm not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✓ Python installed: $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "✓ Python installed: $PYTHON_VERSION"
else
    echo "✗ Python not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Frontend Dependencies ==="

# Check frontend node_modules
if [ -d "frontend/node_modules" ]; then
    echo "✓ frontend/node_modules exists"
else
    echo "✗ frontend/node_modules not found (run: cd frontend && npm install)"
    ERRORS=$((ERRORS + 1))
fi

# Check Playwright installed
if grep -q '@playwright/test' frontend/package.json; then
    echo "✓ @playwright/test in package.json"
    if [ -d "frontend/node_modules/@playwright/test" ]; then
        echo "✓ Playwright installed in node_modules"
    else
        echo "✗ Playwright not installed (run: cd frontend && npm install)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✗ @playwright/test not found in package.json"
    ERRORS=$((ERRORS + 1))
fi

# Check Playwright config
if [ -f "frontend/playwright.config.js" ]; then
    echo "✓ playwright.config.js exists"
else
    echo "✗ playwright.config.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check test directory
if [ -d "frontend/tests/e2e" ]; then
    echo "✓ frontend/tests/e2e directory exists"
    if [ -f "frontend/tests/e2e/invoicing-flow.spec.js" ]; then
        echo "✓ invoicing-flow.spec.js exists"
    else
        echo "✗ invoicing-flow.spec.js not found"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✗ frontend/tests/e2e directory not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Backend Setup ==="

# Check backend requirements
if [ -f "backend/requirements.txt" ] || [ -f "backend/pyproject.toml" ]; then
    echo "✓ Backend dependencies defined"
else
    echo "✗ Backend requirements not found"
    ERRORS=$((ERRORS + 1))
fi

# Check backend app
if [ -f "backend/app/main.py" ]; then
    echo "✓ backend/app/main.py exists"
else
    echo "✗ backend/app/main.py not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Test Files ==="

# Check documentation
if [ -f "frontend/tests/e2e/README.md" ]; then
    echo "✓ frontend/tests/e2e/README.md exists"
else
    echo "✗ frontend/tests/e2e/README.md not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "TESTING.md" ]; then
    echo "✓ TESTING.md exists"
else
    echo "✗ TESTING.md not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "run-tests.sh" ]; then
    echo "✓ run-tests.sh exists"
    if [ -x "run-tests.sh" ]; then
        echo "✓ run-tests.sh is executable"
    else
        echo "! run-tests.sh exists but not executable (fixing...)"
        chmod +x run-tests.sh
    fi
else
    echo "✗ run-tests.sh not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Service Availability ==="

# Check if services are running
if nc -z localhost 8000 2>/dev/null; then
    echo "✓ Backend running on localhost:8000"
else
    echo "- Backend not running on localhost:8000 (start with: cd backend && python -m uvicorn app.main:app --reload)"
fi

if nc -z localhost 5173 2>/dev/null; then
    echo "✓ Frontend dev server running on localhost:5173"
else
    echo "- Frontend dev server not running on localhost:5173 (start with: cd frontend && npm run dev)"
fi

echo ""
echo "=== Summary ==="

if [ $ERRORS -eq 0 ]; then
    echo "✓ All checks passed! Playwright setup is ready."
    echo ""
    echo "Next steps:"
    echo "1. Install Playwright browsers:  npx playwright install"
    echo "2. In terminal 1: cd backend && python -m uvicorn app.main:app --reload"
    echo "3. In terminal 2: cd frontend && npm run dev"
    echo "4. In terminal 3: cd frontend && npm run test:e2e"
    echo ""
    echo "Or use the helper script: ./run-tests.sh"
else
    echo "✗ $ERRORS issue(s) found. Please fix the errors above."
    exit 1
fi
