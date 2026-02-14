#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

# Check for port conflicts
if lsof -i:8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port 8000 is in use. Stopping existing process..."
  lsof -ti:8000 | xargs kill -9 2>/dev/null || true
  sleep 2
fi
if lsof -i:5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port 5173 is in use. Stopping existing process..."
  lsof -ti:5173 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# Backend
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo "Starting backend on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi
echo "Starting frontend on http://localhost:5173"
npm run dev > /tmp/vite.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready, then open browser
echo "Waiting for frontend server to start..."
BROWSER_OPENED=false
for i in {1..30}; do
  if lsof -i:5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✓ Frontend server is ready on port 5173!"
    sleep 2  # Give it a moment to fully initialize
    echo ""
    echo "Opening browser at http://localhost:5173..."
    if command -v open >/dev/null 2>&1; then
      # macOS
      open http://localhost:5173 && BROWSER_OPENED=true
    elif command -v xdg-open >/dev/null 2>&1; then
      # Linux
      xdg-open http://localhost:5173 && BROWSER_OPENED=true
    else
      echo "⚠️  Could not auto-open browser. Please open http://localhost:5173 manually"
    fi
    break
  fi
  sleep 1
done

# If still not ready after 30 seconds, try opening anyway
if [ "$BROWSER_OPENED" = false ]; then
  echo ""
  echo "⚠️  Frontend may still be starting. Opening browser anyway..."
  echo "   If it doesn't load, check the terminal output or /tmp/vite.log for errors"
  if command -v open >/dev/null 2>&1; then
    open http://localhost:5173
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173
  fi
fi

echo ""
echo "Rescue Command Center running:"
echo "  Backend:  http://localhost:8000 (docs: /docs)"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both"
wait
