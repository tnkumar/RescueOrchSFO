# 🚨 GEMINI API KEY REQUIRED

## Problem
Your `.env` file has a dummy API key. The AI coordinator needs a real Gemini API key to work.

## Solution

### Option 1: Get a Free Gemini API Key (Recommended)

1. **Visit**: https://aistudio.google.com/app/apikey
2. **Click**: "Create API Key"
3. **Copy** the key
4. **Update** `.env` file:

```env
GEMINI_API_KEY="YOUR_ACTUAL_KEY_HERE"
```

5. **Restart** backend (stop and run `./run.bat` again)

### Option 2: Run Without AI (Demo Mode)

If you just want to test the system without AI analysis, I can create a mock version that simulates AI responses.

---

## Quick Fix

**Replace this line in `.env`:**
```
GEMINI_API_KEY="sdskjdkjsdfdf"
```

**With your real key:**
```
GEMINI_API_KEY="AIzaSy..."
```

Then restart the backend!

---

## How to Get Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)
5. Paste into `.env` file

**The API is FREE** with generous limits!

---

## After Adding Key

1. Stop backend (Ctrl+C in backend window)
2. Run `./run.bat` again
3. Try starting mission again

The mission will work once you have a valid API key!
