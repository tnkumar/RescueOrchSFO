# Quick Test: Check if Mission Endpoints Are Loaded

Run this to see if mission endpoints exist:

```bash
curl http://127.0.0.1:8000/openapi.json | findstr mission
```

If you see `/mission/start`, `/mission/status` etc. → Backend is correct
If you DON'T see them → Backend needs hard restart

## Hard Restart Steps:

1. **Kill ALL Python processes**:
   ```powershell
   taskkill /F /IM python.exe
   ```

2. **Delete Python cache**:
   ```bash
   cd backend
   rmdir /S /Q __pycache__
   rmdir /S /Q app\__pycache__
   rmdir /S /Q app\routers\__pycache__
   rmdir /S /Q app\services\__pycache__
   ```

3. **Start fresh**:
   ```bash
   cd ..
   ./run.bat
   ```

This will force Python to reload all modules from scratch.
