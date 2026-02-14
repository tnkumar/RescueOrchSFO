# Setup Guide for AI Rescue Mission Demo

## 📦 Required Libraries

The demo script needs only **2 libraries**:

1. ✅ **`requests`** - For HTTP API calls (usually pre-installed)
2. ⚠️ **`google-generativeai`** - For Gemini AI (needs installation)

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Check if `requests` is installed

```bash
python -c "import requests; print('✅ requests installed')"
```

If you get an error, install it:
```bash
pip install requests
```

### Step 2: Install Gemini AI library

```bash
pip install google-generativeai
```

### Step 3: Verify installation

```bash
python -c "import google.generativeai as genai; print('✅ google-generativeai installed')"
```

---

## ✅ You're Ready!

Now you can run:

```bash
python demo_complete_mission.py
```

---

## 💡 Notes

- **No virtual environment needed** - You can run directly
- **Backend already running** - Your `run.bat` started it
- **Webots** - Just make sure it's open with the simulation running

---

## 🔍 If You Get Import Errors

If you see:
```
ModuleNotFoundError: No module named 'requests'
```

Run:
```bash
pip install requests
```

If you see:
```
ModuleNotFoundError: No module named 'google'
```

Run:
```bash
pip install google-generativeai
```

---

## ✅ Complete Setup Commands (Copy-Paste)

```bash
# Install both libraries
pip install requests google-generativeai

# Verify
python -c "import requests, google.generativeai; print('✅ All libraries installed!')"

# Run demo
python demo_complete_mission.py
```

That's it! 🎉
