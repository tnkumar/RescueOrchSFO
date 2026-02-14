# ⚡ Quick Start: Test & Demo in 5 Minutes

## 🎯 Fastest Way to Demo

### **Step 1: Get Real API Key** (1 minute)
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)
4. Update `.env`:
   ```
   HACKATHON_GEMINI_API_KEY="AIzaSy_YOUR_ACTUAL_KEY_HERE"
   ```

### **Step 2: Restart Backend** (30 seconds)
```bash
# Close the backend PowerShell window
# Run again:
./run.bat
```

### **Step 3: Open Webots** (30 seconds)
- Load `rescue_orch.wbt`
- Click ▶️ Play

### **Step 4: Open Frontend** (10 seconds)
- Browser: http://localhost:5173
- Click "🚀 AI Mission Control" tab

### **Step 5: Demo!** (2 minutes)
1. Click "▶️ Start Mission"
2. Click "🔥 Report Fire" → Watch robot move in Webots!
3. Click "🆘 Report Victim" → Watch another robot move!
4. Click "⚠️ Report Gas Leak" → Watch third robot move!

**Done!** You just demoed AI-orchestrated rescue! 🎉

---

## 🔍 Quick Verify Before Demo

```bash
# Test backend
curl http://127.0.0.1:8000/mission/status

# Should return JSON (not "Not Found")
```

If you get "Not Found" → Backend needs restart

---

## 🚨 Common Issues

| Issue | Fix |
|-------|-----|
| "Failed to start mission" | Need real API key in `.env` |
| Robots don't move | Restart Webots simulation |
| "Module not found" | Run: `pip install langchain-google-genai` |
| Frontend "Not Found" | Restart backend |

---

## 📊 What You'll See

**Frontend:**
- AI analysis text from Gemini
- Incident cards
- Robot assignments
- Progress bars

**Webots:**
- Robots teleport to incident locations
- Real-time 3D visualization

**That's it!** Simple and impressive! 🚀
