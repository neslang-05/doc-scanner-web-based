# GitHub Copilot Agent Instructions - Pre-Deployment Validation
## Document Scanner: Feature Completeness, Testing & Railway Deployment Readiness

---

## Mission

You are conducting a **comprehensive pre-deployment audit** of the document scanner application. Your goal is to verify that:

1. All required features are implemented and functional
2. Code quality meets production standards
3. Tests are complete and passing
4. Application is configured correctly for Railway deployment
5. Project is ready to be pushed to GitHub and auto-deployed

This is a **gate-keeping review** - the application must not be deployed until all checks pass.

---

## Part 1: Feature Completeness Checklist

### 1.1 Desktop Web Interface ✓

Verify the following features exist and work:

- [ ] **Session Creation**: Desktop UI can initiate a new scanning session
- [ ] **QR Code Display**: QR code is generated and displayed for mobile pairing
- [ ] **Live Preview**: Real-time camera feed from mobile displays on desktop
- [ ] **Capture Control**: Desktop has a button/shortcut to trigger high-res capture
- [ ] **Thumbnail Gallery**: Captured pages display as thumbnails with order indicators
- [ ] **Page Selection**: User can select individual or multiple pages
- [ ] **Image Preview**: Clicking a thumbnail shows full-size preview
- [ ] **Processing Controls**: UI has controls for:
  - Edge detection toggle
  - Perspective correction toggle
  - Enhancement mode selector (color/grayscale/B&W)
  - Lighting normalization toggle
- [ ] **Batch Processing**: Can apply processing params to multiple pages at once
- [ ] **Page Reordering**: Drag-and-drop or up/down buttons to reorder pages
- [ ] **Page Deletion**: Can remove unwanted pages from session
- [ ] **Export Options**: PDF export form with:
  - DPI selection
  - Compression level
  - OCR toggle
  - Page order confirmation
- [ ] **Download Link**: Generated PDF provides download link or auto-downloads
- [ ] **Session Status**: Shows connection status, page count, last activity

**Validation Test:**
```javascript
// Run this in browser console on desktop UI
async function testDesktopFeatures() {
    console.log("Testing session creation...");
    const createBtn = document.querySelector('[data-action="create-session"]');
    if (!createBtn) return console.error("❌ No session create button");
    
    console.log("Testing QR code display...");
    const qrElement = document.querySelector('[data-qr-code]');
    if (!qrElement) return console.error("❌ No QR code element");
    
    console.log("Testing capture controls...");
    const captureBtn = document.querySelector('[data-action="capture"]');
    if (!captureBtn) return console.error("❌ No capture button");
    
    console.log("Testing processing controls...");
    const processingForm = document.querySelector('[data-form="processing"]');
    if (!processingForm) return console.error("❌ No processing form");
    
    console.log("✅ All desktop UI elements present");
}
testDesktopFeatures();
```

---

### 1.2 Mobile Camera Interface ✓

Verify the mobile page has:

- [ ] **Camera Permission Request**: Prompts for camera access on load
- [ ] **Environment Camera**: Uses rear camera by default (`facingMode: 'environment'`)
- [ ] **Stream Initiation**: Automatically connects to server with session token
- [ ] **Minimal UI**: No capture buttons or controls (desktop controls everything)
- [ ] **Connection Indicator**: Shows when connected/disconnected from desktop
- [ ] **Error Handling**: Displays clear messages if camera access denied

**Validation Test:**
```javascript
// Run on mobile browser at /camera/{session_token}
async function testMobileCamera() {
    console.log("Testing camera stream...");
    const videoElement = document.querySelector('video');
    if (!videoElement) return console.error("❌ No video element");
    
    if (!videoElement.srcObject) return console.error("❌ No camera stream");
    
    const stream = videoElement.srcObject;
    const videoTracks = stream.getVideoTracks();
    
    if (videoTracks.length === 0) return console.error("❌ No video track");
    
    const settings = videoTracks[0].getSettings();
    console.log("Camera facing mode:", settings.facingMode);
    
    if (settings.facingMode !== 'environment') {
        console.warn("⚠️  Not using rear camera");
    }
    
    console.log("✅ Camera stream active");
}
testMobileCamera();
```

---

### 1.3 Streaming and Capture Pipeline ✓

Verify the following:

- [ ] **WebRTC or WebSocket**: Streaming implementation exists
- [ ] **Low Latency**: Preview latency < 500ms (measure with timestamp overlay)
- [ ] **Decoupled Capture**: High-res still capture is separate from preview stream
- [ ] **Preview Resolution**: Preview uses lower res for efficiency (e.g., 640x480)
- [ ] **Capture Resolution**: Still captures use high res (e.g., 1920x1080 or higher)
- [ ] **Frame Rate**: Preview maintains 15+ fps
- [ ] **Reconnection**: Mobile can reconnect without breaking desktop session

**Validation Test:**
```python
# Test streaming endpoints
import requests
import time

def test_streaming_pipeline(base_url):
    # Create session
    resp = requests.post(f"{base_url}/api/session/create")
    assert resp.status_code == 200
    session_id = resp.json()['session_id']
    
    # Check session status
    resp = requests.get(f"{base_url}/api/session/{session_id}/status")
    assert resp.status_code == 200
    
    # Simulate camera connection
    # (Manual step: scan QR code with phone)
    print(f"Scan QR code: {base_url}/camera/{session_id}")
    input("Press Enter after connecting camera...")
    
    # Verify camera connected
    resp = requests.get(f"{base_url}/api/session/{session_id}/status")
    status = resp.json()
    assert status['camera_connected'] == True, "❌ Camera not connected"
    
    # Test capture
    start = time.time()
    resp = requests.post(f"{base_url}/api/capture", json={
        "session_id": session_id,
        "resolution": "high"
    })
    latency = time.time() - start
    
    assert resp.status_code == 200
    assert latency < 2.0, f"❌ Capture too slow: {latency}s"
    
    print("✅ Streaming pipeline functional")
```

---

### 1.4 Image Processing Engine ✓

Verify all processing features work:

- [ ] **Edge Detection**: Detects document boundaries using contour detection
- [ ] **Fallback Handling**: Falls back to image bounds if no document detected
- [ ] **Perspective Correction**: Applies perspective transform to flatten document
- [ ] **Illumination Normalization**: Removes shadows and evens out lighting
- [ ] **Color Enhancement**: Offers multiple modes:
  - Original/color mode
  - Grayscale conversion
  - Black & white (binarization)
- [ ] **Original Preservation**: Original images never modified
- [ ] **Processing Parameters Storage**: Params stored separately, can be changed
- [ ] **Batch Reprocessing**: Can reprocess multiple pages with new params

**Validation Test:**
```python
# test_image_processing.py
import cv2
import numpy as np
from server.services.image_processor import detect_document_edges, correct_perspective

def test_edge_detection():
    # Create test image with clear document
    img = np.zeros((1000, 800, 3), dtype=np.uint8)
    # White document on dark background
    cv2.rectangle(img, (100, 100), (700, 900), (255, 255, 255), -1)
    
    corners = detect_document_edges(img)
    assert len(corners) == 4, "Should detect 4 corners"
    
    # Check corners are roughly correct
    assert corners[0][1] < 200, "Top-left Y should be near top"
    assert corners[2][1] > 800, "Bottom-right Y should be near bottom"
    
    print("✅ Edge detection works")

def test_perspective_correction():
    # Create skewed document image
    img = cv2.imread('test_fixtures/skewed_doc.jpg')
    corners = np.array([[100, 50], [700, 100], [650, 900], [50, 850]])
    
    corrected = correct_perspective(img, corners)
    
    # Check output is rectangular
    assert corrected.shape[0] > 0 and corrected.shape[1] > 0
    
    print("✅ Perspective correction works")

def test_original_preservation():
    # Ensure originals never change
    import shutil
    import hashlib
    
    # Copy test image
    shutil.copy('test_fixtures/doc.jpg', '/tmp/test_original.jpg')
    original_hash = hashlib.md5(open('/tmp/test_original.jpg', 'rb').read()).hexdigest()
    
    # Process multiple times with different params
    from server.services.image_processor import process_image
    
    process_image('/tmp/test_original.jpg', {"enhance_mode": "grayscale"})
    process_image('/tmp/test_original.jpg', {"enhance_mode": "bw"})
    process_image('/tmp/test_original.jpg', {"normalize_lighting": True})
    
    # Verify original unchanged
    current_hash = hashlib.md5(open('/tmp/test_original.jpg', 'rb').read()).hexdigest()
    assert original_hash == current_hash, "❌ Original was modified!"
    
    print("✅ Original images preserved")

if __name__ == "__main__":
    test_edge_detection()
    test_perspective_correction()
    test_original_preservation()
```

---

### 1.5 Document Session Management ✓

Verify session handling:

- [ ] **Session Creation**: Generates unique session IDs
- [ ] **Session Expiration**: Sessions expire after configured time (default 4 hours)
- [ ] **Multi-Page Support**: Can store 20+ pages per session
- [ ] **Page Metadata**: Stores capture time, processing params, order
- [ ] **Page Ordering**: Maintains page sequence
- [ ] **Session Persistence**: Survives server restart (or gracefully fails)
- [ ] **Cleanup Jobs**: Expired sessions are automatically deleted

**Validation Test:**
```python
# test_session_management.py
import os
import json
import time
from datetime import datetime, timedelta

def test_session_lifecycle():
    from server.services.session_manager import SessionManager
    
    manager = SessionManager()
    
    # Create session
    session = manager.create_session()
    session_id = session['session_id']
    
    assert os.path.exists(f'sessions/{session_id}'), "Session directory not created"
    
    # Add pages
    for i in range(5):
        manager.add_page(session_id, f'/tmp/test_page_{i}.jpg', {
            "captured_at": datetime.now().isoformat(),
            "processing_params": {"enhance_mode": "grayscale"}
        })
    
    # Verify page count
    status = manager.get_session_status(session_id)
    assert status['page_count'] == 5
    
    # Test page reordering
    manager.reorder_pages(session_id, [4, 3, 2, 1, 0])
    pages = manager.get_pages(session_id)
    assert pages[0]['page_id'].endswith('4')
    
    print("✅ Session management works")

def test_session_expiration():
    from server.services.session_manager import SessionManager, cleanup_expired_sessions
    
    # Create old session
    old_session_dir = 'sessions/old_test_session'
    os.makedirs(old_session_dir, exist_ok=True)
    
    metadata = {
        "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        "last_activity": (datetime.now() - timedelta(hours=5)).isoformat()
    }
    with open(f'{old_session_dir}/metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    # Run cleanup
    cleanup_expired_sessions(max_age_hours=4)
    
    # Verify old session deleted
    assert not os.path.exists(old_session_dir), "❌ Expired session not cleaned up"
    
    print("✅ Session expiration works")

if __name__ == "__main__":
    test_session_lifecycle()
    test_session_expiration()
```

---

### 1.6 PDF Export and OCR ✓

Verify export functionality:

- [ ] **PDF Generation**: Creates valid PDF files
- [ ] **Page Ordering**: Respects custom page order in export
- [ ] **DPI Configuration**: Supports 150, 200, 300 DPI options
- [ ] **Compression**: Offers low/medium/high compression
- [ ] **OCR Toggle**: Can enable/disable OCR
- [ ] **Async OCR**: OCR runs in background, doesn't block export
- [ ] **Text Layer**: OCR text embedded as searchable layer (not visible)
- [ ] **Download Links**: Generates time-limited download tokens
- [ ] **Link Expiration**: Download links expire after configured time

**Validation Test:**
```python
# test_pdf_export.py
import os
import PyPDF2
from PIL import Image

def test_pdf_generation():
    from server.services.pdf_builder import build_pdf
    
    session_id = 'test_session'
    page_ids = ['p001', 'p002', 'p003']
    
    pdf_path = build_pdf(
        session_id=session_id,
        page_ids=page_ids,
        dpi=300,
        compression='medium',
        include_ocr=False
    )
    
    assert os.path.exists(pdf_path), "PDF not generated"
    
    # Verify PDF is valid
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        assert len(pdf.pages) == 3, f"Expected 3 pages, got {len(pdf.pages)}"
    
    print("✅ PDF generation works")

def test_pdf_with_ocr():
    from server.services.pdf_builder import build_pdf_with_ocr
    
    session_id = 'test_session'
    page_ids = ['p001']
    
    # This should return immediately and queue OCR job
    result = build_pdf_with_ocr(session_id, page_ids)
    
    assert 'job_id' in result, "OCR job not created"
    assert 'pdf_path' in result, "PDF not generated"
    
    # Wait for OCR to complete (or timeout)
    import time
    timeout = 30
    start = time.time()
    
    while time.time() - start < timeout:
        status = get_ocr_job_status(result['job_id'])
        if status['status'] == 'completed':
            break
        time.sleep(1)
    
    assert status['status'] == 'completed', "OCR did not complete"
    
    # Verify text layer exists
    with open(result['pdf_path'], 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        text = pdf.pages[0].extract_text()
        assert len(text) > 0, "No OCR text found in PDF"
    
    print("✅ PDF with OCR works")

def test_download_links():
    from server.routes.export import generate_download_token
    
    pdf_path = '/tmp/test.pdf'
    token = generate_download_token(pdf_path, expires_in_hours=1)
    
    assert len(token) > 20, "Token too short"
    
    # Verify token validates
    from server.routes.export import validate_download_token
    valid_path = validate_download_token(token)
    assert valid_path == pdf_path
    
    print("✅ Download links work")

if __name__ == "__main__":
    test_pdf_generation()
    test_pdf_with_ocr()
    test_download_links()
```

---

## Part 2: Code Quality Audit

### 2.1 Architecture Compliance ✓

Verify the codebase follows architecture spec:

- [ ] **No Authentication**: Confirm no login/signup/auth code exists
- [ ] **No Cloud APIs**: Grep for AWS, Google Cloud, Azure API calls
- [ ] **Server-Side Processing**: All OpenCV code is in backend, not frontend
- [ ] **Original Preservation**: No code modifies files in `sessions/*/originals/`
- [ ] **Desktop Control**: Mobile camera page has no capture buttons
- [ ] **Separation of Concerns**: Each subsystem in separate module

**Validation Commands:**
```bash
# Check for forbidden patterns
echo "Checking for authentication code..."
grep -r "login\|signup\|authenticate\|password" server/ --exclude-dir=venv
if [ $? -eq 0 ]; then echo "❌ Found auth code"; exit 1; fi

echo "Checking for cloud API calls..."
grep -r "aws\|google.cloud\|azure\|s3\|gcs" server/ --exclude-dir=venv
if [ $? -eq 0 ]; then echo "⚠️  Found cloud API references"; fi

echo "Checking for client-side processing..."
grep -r "cv2\|opencv" static/ 
if [ $? -eq 0 ]; then echo "❌ OpenCV in frontend!"; exit 1; fi

echo "Checking original preservation..."
grep -r "save.*originals/" server/ | grep -v "# Save original"
if [ $? -eq 0 ]; then echo "⚠️  Code may modify originals"; fi

echo "✅ Architecture compliance verified"
```

---

### 2.2 Error Handling ✓

Verify robust error handling:

- [ ] **Try-Catch Blocks**: All external operations wrapped
- [ ] **Graceful Degradation**: Processing failures return fallback images
- [ ] **User-Facing Errors**: Clear error messages, not stack traces
- [ ] **Logging**: Errors logged to file/console
- [ ] **Recovery**: No single failure crashes entire server

**Check these patterns exist:**
```python
# Good error handling example
@app.route('/api/process/<page_id>', methods=['POST'])
def process_page(page_id):
    try:
        params = request.json
        result = image_processor.process(page_id, params)
        return jsonify(result), 200
    except FileNotFoundError:
        return jsonify({"error": "Page not found"}), 404
    except ProcessingError as e:
        logging.error(f"Processing failed for {page_id}: {e}")
        return jsonify({
            "error": "Processing failed",
            "fallback_url": f"/originals/{page_id}"
        }), 500
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return jsonify({"error": "Internal error"}), 500
```

---

### 2.3 Security Hardening ✓

Even without auth, verify basic security:

- [ ] **Path Traversal Prevention**: All file paths sanitized
- [ ] **Session Token Validation**: Regex check on session IDs
- [ ] **Resource Limits**: Max file size, max pages per session
- [ ] **CORS Configuration**: Only allows configured origins
- [ ] **Input Validation**: All API inputs validated
- [ ] **No Eval**: No `eval()` or `exec()` calls

**Validation:**
```bash
# Check for dangerous patterns
echo "Checking for eval/exec..."
grep -r "eval(\|exec(" server/
if [ $? -eq 0 ]; then echo "❌ Found eval/exec"; exit 1; fi

echo "Checking for unsafe file operations..."
grep -r "os.path.join.*request" server/
# Should have validation before join

echo "Checking for resource limits..."
grep -r "MAX_FILE_SIZE\|MAX_PAGES" server/
if [ $? -ne 0 ]; then echo "⚠️  No resource limits found"; fi

echo "✅ Basic security checks passed"
```

---

## Part 3: Railway Deployment Readiness

### 3.1 Required Files ✓

Verify these files exist at project root:

- [ ] **requirements.txt**: All Python dependencies listed
- [ ] **runtime.txt** (optional): Specifies Python version
- [ ] **Procfile** (optional): Specifies start command
- [ ] **.gitignore**: Excludes `sessions/`, `venv/`, `__pycache__/`, `.env`
- [ ] **README.md**: Setup and deployment instructions

**Create missing files:**

```bash
# Generate requirements.txt if missing
pip freeze > requirements.txt

# Create runtime.txt
echo "python-3.11.0" > runtime.txt

# Create Procfile
echo "web: gunicorn app:app --bind 0.0.0.0:\$PORT" > Procfile

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Session data (runtime only)
sessions/
*.jpg
*.png
*.pdf

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF
```

---

### 3.2 Environment Variables ✓

Verify the app uses environment variables for configuration:

- [ ] **PORT**: Server listens on `$PORT` (Railway provides this)
- [ ] **HOST**: Defaults to `0.0.0.0` in production
- [ ] **SESSION_EXPIRY_HOURS**: Configurable session lifetime
- [ ] **MAX_PAGES_PER_SESSION**: Resource limit
- [ ] **MAX_FILE_SIZE_MB**: Upload size limit

**Check app.py has:**
```python
import os

# Railway compatibility
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
```

---

### 3.3 Production Dependencies ✓

Verify production-ready server:

- [ ] **Gunicorn**: Production WSGI server (not Flask dev server)
- [ ] **Gevent/Eventlet**: For WebSocket support
- [ ] **Worker Configuration**: Appropriate worker count

**Update requirements.txt:**
```txt
Flask==3.0.0
gunicorn==21.2.0
gevent==23.9.1  # For WebSocket support
opencv-python-headless==4.8.1.78  # Headless version for servers
Pillow==10.1.0
qrcode==7.4.2
pytesseract==0.3.10  # OCR
PyPDF2==3.0.1
reportlab==4.0.7
```

**Update Procfile:**
```
web: gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT app:app
```

---

### 3.4 Static File Handling ✓

Verify static files are served correctly:

- [ ] **Flask Static**: `/static` route configured
- [ ] **Session Files**: `/sessions` is NOT in static (use send_file)
- [ ] **MIME Types**: Correct content-type headers

**Check routing:**
```python
# Good: Controlled file access
@app.route('/download/<token>')
def download_file(token):
    path = validate_download_token(token)
    if not path:
        abort(404)
    return send_file(path, as_attachment=True)

# Bad: Direct static access to sessions
# app.static_folder should NOT include sessions/
```

---

### 3.5 Database/Filesystem Considerations ✓

**Important Railway Limitation:**
- Railway uses **ephemeral filesystem** - files are lost on restart/redeploy
- Session data in `sessions/` directory will be cleared

**Solutions:**

**Option A: Document Ephemeral Nature (Recommended for MVP)**
```python
# Add warning to README and UI
"""
⚠️  IMPORTANT: Session data is temporary
- Sessions expire after 4 hours
- Server restarts clear all sessions
- Download PDFs immediately after creation
"""
```

**Option B: Add Railway Volume (Persistent Storage)**
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT app:app"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[volumes]]
mountPath = "/app/sessions"
```

**Option C: External Storage (Future Enhancement)**
- Use Railway's Postgres/Redis for metadata
- Store images in S3-compatible storage
- **This violates "no cloud" constraint - only do if user approves**

---

### 3.6 HTTPS and CORS ✓

Railway provides HTTPS automatically, but verify:

- [ ] **Camera Access**: Works over HTTPS (required for getUserMedia)
- [ ] **CORS Headers**: Configured if frontend/backend on different domains
- [ ] **Secure Cookies**: If using cookies, set `Secure` and `SameSite`

**Check CORS configuration:**
```python
from flask_cors import CORS

# If frontend is separate domain
CORS(app, origins=[
    "https://yourdomain.railway.app",
    "http://localhost:3000"  # For local development
])
```

---

### 3.7 Health Check Endpoint ✓

Railway needs a health check endpoint:

```python
@app.route('/health')
def health_check():
    """Railway health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200
```

---

### 3.8 Logging Configuration ✓

Verify production logging:

- [ ] **Structured Logs**: JSON format for Railway logs
- [ ] **Log Levels**: Use INFO in production, DEBUG in development
- [ ] **No Sensitive Data**: Don't log session tokens, file contents

```python
import logging
import sys

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Railway captures stdout
)

logger = logging.getLogger(__name__)
```

---

## Part 4: GitHub Readiness

### 4.1 Repository Structure ✓

Verify clean repository structure:

```
document-scanner/
├── .github/
│   └── copilot-instructions.md
├── server/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   └── utils/
├── static/
│   ├── desktop/
│   └── mobile/
├── tests/
│   ├── test_image_processing.py
│   ├── test_session_management.py
│   └── test_pdf_export.py
├── .gitignore
├── requirements.txt
├── runtime.txt
├── Procfile
├── README.md
└── LICENSE (optional)
```

---

### 4.2 README Documentation ✓

Verify README contains:

- [ ] **Project Description**: What it does, why it exists
- [ ] **Features List**: All major capabilities
- [ ] **Local Setup**: Step-by-step installation
- [ ] **Usage Guide**: How to use desktop + mobile
- [ ] **Railway Deployment**: One-click deploy button
- [ ] **Environment Variables**: Configuration options
- [ ] **Troubleshooting**: Common issues (camera permissions, HTTPS)
- [ ] **License**: MIT or other open-source license

**Add Railway Deploy Button:**
```markdown
## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/document-scanner)

1. Click the button above
2. Connect your GitHub account
3. Configure environment variables (optional)
4. Deploy!

Your app will be live at `https://your-app.railway.app`
```

---

### 4.3 .gitignore Verification ✓

Ensure sensitive files are not committed:

```bash
# Check for accidentally committed files
echo "Checking for sensitive files..."

if [ -d "sessions/" ]; then
    echo "⚠️  sessions/ directory exists - should be in .gitignore"
fi

if [ -f ".env" ]; then
    echo "⚠️  .env file exists - should be in .gitignore"
fi

if [ -d "__pycache__/" ]; then
    echo "⚠️  __pycache__/ exists - should be in .gitignore"
fi

# Verify .gitignore catches these
git check-ignore sessions/ .env __pycache__/
if [ $? -ne 0 ]; then
    echo "❌ .gitignore not configured correctly"
    exit 1
fi

echo "✅ .gitignore properly configured"
```

---

### 4.4 License File ✓

Add an open-source license (optional but recommended):

```bash
# Create MIT License
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

---

## Part 5: Pre-Push Testing Checklist

### 5.1 Local Environment Test ✓

Run complete local test:

```bash
#!/bin/bash
# local_test.sh

echo "=== Local Environment Test ==="

# 1. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# 2. Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

# 3. Start server
echo "Starting server..."
python server/app.py &
SERVER_PID=$!
sleep 5

# 4. Test endpoints
echo "Testing endpoints..."
curl -f http://localhost:5000/health || { echo "❌ Health check failed"; kill $SERVER_PID; exit 1; }
curl -f http://localhost:5000/ || { echo "❌ Homepage failed"; kill $SERVER_PID; exit 1; }

# 5. Create test session
echo "Creating test session..."
SESSION=$(curl -s -X POST http://localhost:5000/api/session/create | jq -r '.session_id')
if [ -z "$SESSION" ]; then
    echo "❌ Session creation failed"
    kill $SERVER_PID
    exit 1
fi

echo "Test session: $SESSION"

# 6. Stop server
kill $SERVER_PID

echo "✅ All local tests passed"
```

---

### 5.2 Production Simulation Test ✓

Test with production configuration:

```bash
#!/bin/bash
# production_test.sh

echo "=== Production Simulation Test ==="

# Set production environment
export PORT=8080
export HOST=0.0.0.0
export DEBUG=False

# Start with Gunicorn
echo "Starting with Gunicorn..."
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT app:app &
GUNICORN_PID=$!
sleep 5

# Test production server
echo "Testing production server..."
curl -f http://localhost:8080/health
if [ $? -ne 0 ]; then
    echo "❌ Production server failed"
    kill $GUNICORN_PID
    exit 1
fi

kill $GUNICORN_PID

echo "✅ Production simulation passed"
```

---

### 5.3 Mobile Camera Test ✓

**Manual test checklist** (cannot be automated):

1. [ ] Start local server with HTTPS (use ngrok or mkcert)
2. [ ] Create session and get QR code
3. [ ] Scan QR code with phone
4. [ ] Verify camera permission prompt appears
5. [ ] Verify live preview shows on desktop
6. [ ] Verify latency is acceptable (<500ms)
7. [ ] Test capture button on desktop
8. [ ] Verify high-res image captured
9. [ ] Test processing on captured image
10. [ ] Test PDF export with OCR

```bash
# Use ngrok for HTTPS testing
ngrok http 5000

# Or use mkcert for local HTTPS
mkcert -install
mkcert localhost
python app.py --cert localhost.pem --key localhost-key.pem
```

---

## Part 6: Final Deployment Checklist

### Before Pushing to GitHub:

- [ ] All tests pass (`pytest tests/`)
- [ ] Local server runs without errors
- [ ] requirements.txt is complete and minimal
- [ ] .gitignore excludes all sensitive files
- [ ] README.md has deployment instructions
- [ ] No hardcoded secrets or API keys in code
- [ ] Production dependencies installed (gunicorn, gevent)
- [ ] Environment variable configuration documented
- [ ] Health check endpoint works
- [ ] Static files serve correctly

### Before Railway Deployment:

- [ ] GitHub repository is public (or Railway has access)
- [ ] requirements.txt uses production-ready packages
- [ ] Procfile has correct start command
- [ ] App listens on $PORT environment variable
- [ ] HTTPS camera access tested
- [ ] Session expiration documented
- [ ] Ephemeral storage limitations documented
- [ ] Railway deploy button added to README

### After Railway Deployment:

- [ ] App builds successfully on Railway
- [ ] Health check returns 200 OK
- [ ] Desktop UI loads at Railway URL
- [ ] QR code generates correctly
- [ ] Mobile camera connects over HTTPS
- [ ] Capture and processing work end-to-end
- [ ] PDF export and download work
- [ ] Session cleanup runs automatically
- [ ] Logs show no critical errors

---

## Automated Validation Script

Run this comprehensive check before pushing:

```bash
#!/bin/bash
# pre_deploy_check.sh

set -e  # Exit on any error

echo "=========================================="
echo "  Document Scanner Pre-Deployment Check"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. File Structure
echo ""
echo "1. Checking File Structure..."
[ -f "requirements.txt" ]; check "requirements.txt exists"
[ -f "Procfile" ]; check "Procfile exists"
[ -f "README.md" ]; check "README.md exists"
[ -f ".gitignore" ]; check ".gitignore exists"
[ -f "server/app.py" ]; check "server/app.py exists"
[ -d "static/desktop" ]; check "static/desktop/ exists"
[ -d "static/mobile" ]; check "static/mobile/ exists"
[ -d "tests" ]; check "tests/ directory exists"

# 2. Dependencies
echo ""
echo "2. Checking Dependencies..."
grep -q "Flask" requirements.txt; check "Flask in requirements.txt"
grep -q "gunicorn" requirements.txt; check "gunicorn in requirements.txt"
grep -q "opencv" requirements.txt; check "opencv in requirements.txt"
grep -q "gevent" requirements.txt; check "gevent/eventlet in requirements.txt"

# 3. Configuration
echo ""
echo "3. Checking Configuration..."
grep -q "PORT" server/app.py; check "PORT environment variable used"
grep -q "0.0.0.0" server/app.py; check "Binds to 0.0.0.0"

# 4. Security
echo ""
echo "4. Checking Security..."
! grep -r "eval(" server/ --exclude-dir=venv; check "No eval() usage"
! grep -r "exec(" server/ --exclude-dir=venv; check "No exec() usage"
grep -q "sessions/" .gitignore; check "sessions/ in .gitignore"
grep -q ".env" .gitignore; check ".env in .gitignore"

# 5. Architecture Compliance
echo ""
echo "5. Checking Architecture Compliance..."
! grep -r "login\|signup\|authenticate" server/ --exclude-dir=venv; check "No authentication code"
! grep -r "aws\|google.cloud" server/ --exclude-dir=venv; check "No cloud APIs"

# 6. Tests
echo ""
echo "6. Running Tests..."
python -m pytest tests/ --tb=short > /dev/null 2>&1; check "All tests pass"

# 7. Health Check
echo ""
echo "7. Testing Server Start..."
timeout 10 python server/app.py > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3
kill $SERVER_PID 2>/dev/null
[ $? -eq 0 ]; check "Server starts without errors"

# Summary
echo ""
echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Initial deployment-ready version'"
    echo "  3. git push origin main"
    echo "  4. Deploy to Railway"
    exit 0
else
    echo ""
    echo -e "${RED}✗ DEPLOYMENT BLOCKED - FIX FAILURES ABOVE${NC}"
    exit 1
fi
```

**Usage:**
```bash
chmod +x pre_deploy_check.sh
./pre_deploy_check.sh
```

---

## Success Criteria

The application is **deployment-ready** when:

1. ✅ All features from architecture spec are implemented
2. ✅ All tests pass with >90% coverage
3. ✅ Local server runs without errors
4. ✅ Mobile camera connects and streams reliably
5. ✅ Capture, processing, and export work end-to-end
6. ✅ Code follows architecture constraints (no auth, no cloud, etc.)
7. ✅ Production dependencies configured (gunicorn, gevent)
8. ✅ Environment variables properly used
9. ✅ .gitignore prevents committing sensitive files
10. ✅ README documents setup and deployment
11. ✅ Railway-specific requirements met (PORT, health check, etc.)

**Only when all criteria are met should the code be pushed to GitHub and deployed to Railway.**

---

## Final Notes

- **Test locally first** - Always verify the app works on your machine before deploying
- **Monitor Railway logs** - Check for errors after first deployment
- **Test on real devices** - Desktop browser + mobile phone over HTTPS
- **Document limitations** - Make ephemeral storage clear to users
- **Iterate carefully** - Railway auto-deploys on push, so test branches first

**This is a gate-keeping document. Do not skip checks. Quality over speed.**