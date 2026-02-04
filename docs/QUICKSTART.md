# Quick Start Guide

## Installation & Setup (5 minutes)

### Step 1: Install Dependencies
```powershell
# Activate virtual environment (if you haven't already)
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### Step 2: Verify Installation
```powershell
# Run system check
python test_system.py
```

All checks should pass. If any fail, reinstall dependencies.

### Step 3: Start the Server
```powershell
python server/app.py
```

You should see:
```
Web-Based Document Scanner
Server starting on http://0.0.0.0:5000
```

---

## First Scan (2 minutes)

### On Desktop:

1. **Open browser** → `http://localhost:5000`

2. **Click "New Session"** 
   - A QR code will appear
   - Session valid for 4 hours

3. **Wait for mobile connection**
   - Status will change from "Disconnected" to "Connected"
   - Live preview will appear

4. **Capture pages**
   - Click "📷 Capture" button
   - Or press `Spacebar`
   - Pages appear in right panel

5. **Manage pages**
   - Click 👁️ to view full size
   - Click 🗑️ to delete

### On Mobile:

1. **Scan QR code** with phone camera

2. **Allow camera access** when prompted

3. **Point at document**
   - You'll see "Streaming video..." status
   - Keep phone steady

4. **That's it!**
   - Desktop controls everything
   - Just keep phone pointed at document

---

## HTTPS Setup for Mobile Camera

Mobile browsers require HTTPS for camera access. Choose one option:

### Option A: ngrok (Easiest - 2 minutes)

1. **Download ngrok**: https://ngrok.com/download

2. **Run ngrok**:
   ```powershell
   ngrok http 5000
   ```

3. **Use the HTTPS URL** shown (e.g., `https://abc123.ngrok.io`)

### Option B: mkcert (Local Network - 5 minutes)

1. **Install mkcert**:
   ```powershell
   choco install mkcert
   ```

2. **Create certificate**:
   ```powershell
   mkcert -install
   mkcert localhost 192.168.1.* ::1
   ```

3. **Start server with SSL** (modify app.py or use nginx)

### Option C: Temporary (Development Only)

On mobile Chrome:
1. Go to `chrome://flags`
2. Enable "Insecure origins treated as secure"
3. Add: `http://YOUR_LOCAL_IP:5000`
4. Restart Chrome

---

## Common Issues

### "Camera not connected" on desktop
- Ensure mobile phone scanned the QR code
- Check both devices on same WiFi network
- Refresh mobile page and try again

### Mobile shows "Camera Access Required"
- Grant camera permissions in browser settings
- Ensure using HTTPS (see setup above)
- Try different browser (Chrome recommended)

### Video stream is laggy
- Reduce distance between devices
- Close other apps on phone
- Check WiFi signal strength
- Normal latency: 100-300ms

### Captured images not showing
- Check browser console for errors
- Ensure sufficient disk space
- Refresh desktop page

---

## Performance Tips

**For Best Results:**

✓ Use modern smartphone (2020+)
✓ Strong WiFi signal
✓ Close unnecessary apps
✓ Keep phone within 10m of router
✓ Use Chrome browser on both devices

**Expected Performance:**
- Video: 15 FPS
- Latency: 100-300ms
- Capture resolution: 1920x1080
- Thumbnail generation: <1 second

---

## What's Working (Phase 1-3)

✅ Session creation and QR pairing
✅ Live video streaming (15 FPS)
✅ Image capture and storage
✅ Thumbnail gallery
✅ Page deletion

## Coming Soon (Phase 4-7)

🚧 Document edge detection
🚧 Perspective correction
🚧 Image enhancement filters
🚧 PDF export
🚧 OCR text extraction

---

## Need Help?

- Check `README.md` for detailed documentation
- Review `PROJECT_ARCHITECTURE.md` for system design
- Check browser console (F12) for error messages
- Ensure all dependencies installed: `python test_system.py`

---

**Ready to scan!** 📄✨
