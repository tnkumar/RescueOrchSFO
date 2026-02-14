# 🔧 COMPLETE FIX: Backend Not Loading Mission Router

## Current Status
- ✅ `google-generativeai` is installed
- ❌ Backend window crashed on startup (import error)
- ❌ Mission endpoints return 404

## Complete Solution

### Step 1: Stop All Running Processes

```bash
# Press Ctrl+C in any open PowerShell windows
# Or close all PowerShell windows that run.bat opened
```

### Step 2: Restart Backend Properly

```bash
cd c:\Users\Avina\Downloads\Hackathon\KUMAR_FILES\RescueOrchSFO
./run.bat
```

**IMPORTANT**: Watch the backend window for errors!

### Step 3: Verify Backend is Running

Open browser: http://127.0.0.1:8000/docs

You should see:
- ✅ `/mission/start` endpoint
- ✅ `/mission/status` endpoint
- ✅ `/mission/incident/report` endpoint

### Step 4: Test Mission Endpoint

```bash
curl http://127.0.0.1:8000/mission/status
```

Should return JSON (not "Not Found").

---

## If Backend Still Crashes

The backend window might show an error. Common issues:

### Issue 1: Missing .env file in backend folder

**Solution**: Copy `.env` to backend folder
```bash
copy .env backend\.env
```

### Issue 2: GEMINI_API_KEY not loaded

**Solution**: Add python-dotenv to requirements
```bash
cd backend
pip install python-dotenv
```

### Issue 3: Import error persists

**Solution**: Restart Python environment
```bash
# Close ALL PowerShell windows
# Open fresh terminal
cd c:\Users\Avina\Downloads\Hackathon\KUMAR_FILES\RescueOrchSFO
./run.bat
```

---

## Quick Test After Fix

1. **Backend running**: http://127.0.0.1:8000/docs shows mission endpoints
2. **Frontend running**: http://localhost:5173 shows UI
3. **Test mission**: Click "Start Mission" in frontend

If all 3 work → ✅ Ready to demo!
