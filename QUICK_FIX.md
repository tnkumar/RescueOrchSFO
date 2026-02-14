# 🔧 Quick Fix: Mission Start Failed

## Problem
The mission endpoint returns `404 Not Found` because the backend needs to be **restarted** to load the new mission router code.

## Solution (2 Steps)

### Step 1: Restart Backend

Your backend is running from `run.bat`. You need to restart it:

1. **Find the backend window** (PowerShell window running uvicorn)
2. **Press `Ctrl+C`** to stop it
3. **Close the window**
4. **Run `./run.bat` again** in the main directory

### Step 2: Verify Mission Endpoint

After restart, test:
```bash
curl http://127.0.0.1:8000/mission/status
```

Should return mission status (not 404).

---

## Alternative: Manual Backend Restart

If `run.bat` doesn't work:

```bash
# Stop current backend (Ctrl+C)

# Restart manually
cd backend
uvicorn app.main:app --reload --port 8000
```

---

## Why This Happens

- You added new `mission.py` router
- Backend was already running
- Python doesn't auto-reload new modules
- Need restart to import mission router

---

## After Restart

✅ Mission endpoints will work
✅ Frontend "Start Mission" button will work  
✅ Python demo script will work

Just restart the backend and try again!
