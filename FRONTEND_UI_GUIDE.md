# 🎯 Frontend UI Guide - What You Should See

## After Clicking "Start Mission"

### ✅ **Expected UI Elements:**

1. **📹 Camera Feed Section**
   - Shows Mavic drone camera
   - Black rectangle if camera not available

2. **🎛️ Control Panel**
   ```
   [⏹️ Stop Mission]  [🔥 Report Fire]  [🆘 Report Victim]  [⚠️ Report Gas Leak]
   ```
   - Stop Mission button (red)
   - Three incident report buttons (white with colored borders)

3. **📍 Incidents Section**
   - Header: "📍 Detected Incidents (0)"
   - Message: "No incidents reported yet..."

4. **🤖 Robot Status Section**
   - Header: "🤖 Robot Status"
   - Three cards showing:
     - TIAGO1 - Status: READY
     - TIAGO2 - Status: READY
     - TIAGO3 - Status: READY

---

## 🔧 **Troubleshooting: Buttons Not Showing**

### **Quick Fix:**

1. **Hard Refresh Browser**
   ```
   Ctrl + Shift + R  (Windows/Linux)
   Cmd + Shift + R   (Mac)
   ```

2. **Check Browser Console**
   - Press F12
   - Click "Console" tab
   - Look for errors (red text)

3. **Verify Mission Started**
   - You should see alert: "✅ AI-orchestrated rescue mission initialized"
   - If not, mission didn't start

### **If Still Not Working:**

**Test with curl:**
```bash
# Start mission
curl -X POST http://127.0.0.1:8000/mission/start

# Check status
curl http://127.0.0.1:8000/mission/status
```

Should return: `{"active": true, ...}`

**Then refresh browser** - buttons should appear!

---

## 📸 **What It Should Look Like**

See the generated image: `mission_control_ui_guide.webp`

The incident buttons appear ONLY when mission is active!
