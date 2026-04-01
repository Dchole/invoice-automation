#!/bin/bash
# Helper script to run Playwright e2e tests for InvoiceFlow
# This script manages both backend and frontend services

set -e

BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
FRONTEND_DIR="$(cd "$(dirname "$0")/frontend" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup on exit
cleanup() {
  echo "Cleaning up..."
  [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
}

trap cleanup EXIT

# Check if services are already running
check_service() {
  local port=$1
  local name=$2
  if nc -z localhost $port 2>/dev/null; then
    echo "✓ $name is already running on port $port"
    return 0
  fi
  return 1
}

# Start backend if not running
if ! check_service 8000 "Backend"; then
  echo "Starting backend..."
  cd "$BACKEND_DIR"
  python -m uvicorn app.main:app --reload &
  BACKEND_PID=$!
  echo "Backend PID: $BACKEND_PID"
  sleep 3
fi

# Start frontend dev server if not running
if ! check_service 5173 "Frontend"; then
  echo "Starting frontend dev server..."
  cd "$FRONTEND_DIR"
  npm run dev &
  FRONTEND_PID=$!
  echo "Frontend PID: $FRONTEND_PID"
  sleep 3
fi

# Run Playwright tests
cd "$FRONTEND_DIR"
echo "Running Playwright tests..."
npm run test:e2e "$@"
