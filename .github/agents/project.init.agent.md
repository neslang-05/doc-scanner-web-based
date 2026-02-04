# GitHub Copilot Agent Instructions
## Desktop-Controlled Web-Based Document Scanner

---

## Project Identity

You are assisting in building a **self-hosted, local-first document scanning application** that uses a desktop browser as the control interface and a smartphone as a wireless camera sensor. This is not a mobile app, not a SaaS platform, and not a cloud service.

---

## Core Architecture Principles

### Absolute Constraints (NEVER VIOLATE)

1. **No authentication system** - No logins, user accounts, or identity management
2. **No cloud dependencies** - Must work entirely on local network
3. **Smartphone = Camera only** - Phone streams video, desktop controls everything
4. **Desktop browser = Primary UI** - All capture, processing, and export controls live here
5. **Server-side processing** - All image processing happens on Flask backend
6. **Privacy by architecture** - No telemetry, analytics, or external services
7. **Non-destructive editing** - Original images preserved, processing parameters stored separately

### System Components

```
Desktop Browser (Control Surface)
    ↕ HTTP/WebSocket
Flask Server (Orchestrator)
    ↕ WebRTC/WebSocket
Mobile Browser (Camera Sensor)
```

---

## Technology Stack

### Backend
- **Framework**: Flask (Python 3.9+)
- **Image Processing**: OpenCV, Pillow, scikit-image
- **OCR**: Tesseract (optional, asynchronous)
- **PDF Generation**: reportlab or PyPDF2
- **Streaming**: WebRTC (aiortc) or WebSocket fallback
- **State Storage**: Filesystem-based (JSON metadata + image files)

### Frontend
- **Desktop UI**: Modern JavaScript (ES6+), HTML5, CSS3
- **Mobile Camera**: Minimal HTML page using MediaStream API
- **Communication**: WebSocket for control, WebRTC for video
- **No heavy frameworks** - Prefer vanilla JS unless complexity demands React/Vue

---

## Code Generation Guidelines

### When Writing Backend Code

```python
# ALWAYS preserve original images
def capture_image(session_id, frame_data):
    """
    Capture and store original image.
    Processing happens separately and is non-destructive.
    """
    original_path = f"sessions/{session_id}/originals/{timestamp}.jpg"
    save_image(frame_data, original_path)
    
    # Store metadata separately
    metadata = {
        "captured_at": timestamp,
        "original_path": original_path,
        "processing_params": {}  # Not applied yet
    }
    return metadata

# NEVER do this - destructive processing
def capture_and_enhance(frame_data):  # ❌ WRONG
    enhanced = apply_filters(frame_data)
    save_image(enhanced, path)  # Original lost!
```

### When Writing Frontend Code

```javascript
// Desktop UI controls everything
class DesktopScanner {
    constructor() {
        this.livePreview = null;
        this.capturedPages = [];
        this.processingParams = {};
    }
    
    // User triggers capture from desktop
    captureImage() {
        fetch('/api/capture', {
            method: 'POST',
            body: JSON.stringify({
                session_id: this.sessionId,
                resolution: 'high'  // Request high-res from phone
            })
        });
    }
}

// Mobile only streams - NO capture buttons
class MobileCameraStream {
    constructor(sessionToken) {
        this.sessionToken = sessionToken;
        this.stream = null;
    }
    
    async startStreaming() {
        this.stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        // Send to server, that's it
    }
}
```

---

## Module Implementation Order

Follow this sequence strictly:

### Phase 1: Foundation
1. Flask server skeleton with session management
2. QR code generation for pairing
3. Basic desktop UI shell
4. Mobile camera page (minimal)

### Phase 2: Streaming Validation
5. WebRTC or WebSocket video streaming
6. Live preview rendering on desktop
7. Latency and quality testing
8. **GATE: Must achieve <500ms latency before proceeding**

### Phase 3: Capture Pipeline
9. High-resolution still capture (decoupled from preview)
10. Image storage and session state
11. Desktop thumbnail gallery

### Phase 4: Image Processing
12. Document edge detection (OpenCV contours)
13. Perspective correction (cv2.getPerspectiveTransform)
14. Illumination normalization
15. Color filters (grayscale, B&W, color enhancement)

### Phase 5: Document Management
16. Multi-page session handling
17. Page reordering and deletion
18. Batch processing parameter application

### Phase 6: Export and OCR
19. PDF assembly with configurable DPI
20. Compression and optimization
21. Asynchronous OCR (Tesseract)
22. Searchable PDF text layer embedding

### Phase 7: Sharing
23. Temporary download links
24. Time-limited sharing tokens
25. Cleanup and garbage collection

---

## File Structure to Generate

```
project/
├── server/
│   ├── app.py                 # Flask application entry
│   ├── routes/
│   │   ├── session.py         # Session and pairing
│   │   ├── streaming.py       # Video streaming
│   │   ├── capture.py         # Image capture
│   │   ├── processing.py      # Image enhancement
│   │   └── export.py          # PDF generation
│   ├── services/
│   │   ├── session_manager.py
│   │   ├── image_processor.py
│   │   ├── ocr_service.py
│   │   └── pdf_builder.py
│   └── utils/
│       ├── qr_generator.py
│       └── file_storage.py
├── static/
│   ├── desktop/
│   │   ├── index.html         # Main scanning UI
│   │   ├── scanner.js         # Desktop controller
│   │   └── styles.css
│   └── mobile/
│       ├── camera.html        # Minimal camera page
│       └── camera.js
├── sessions/                  # Runtime data (gitignored)
│   └── {session_id}/
│       ├── originals/
│       ├── processed/
│       ├── metadata.json
│       └── exports/
├── requirements.txt
└── README.md
```

---

## API Design Patterns

### Session Management

```python
# POST /api/session/create
{
    "created_at": "2026-02-04T10:30:00Z",
    "session_id": "abc123",
    "qr_code_url": "/qr/abc123",
    "expires_at": "2026-02-04T14:30:00Z"  # 4 hour session
}

# GET /api/session/{session_id}/status
{
    "session_id": "abc123",
    "camera_connected": true,
    "page_count": 5,
    "last_activity": "2026-02-04T12:15:00Z"
}
```

### Capture and Processing

```python
# POST /api/capture
{
    "session_id": "abc123",
    "resolution": "high"  # Request high-res frame
}
→ Returns: {"page_id": "p001", "thumbnail_url": "/thumb/p001"}

# POST /api/process/{page_id}
{
    "detect_edges": true,
    "correct_perspective": true,
    "enhance_mode": "grayscale",  # "color" | "grayscale" | "bw"
    "normalize_lighting": true
}
→ Returns: {"processed_url": "/preview/p001_processed.jpg"}

# POST /api/batch/process
{
    "session_id": "abc123",
    "page_ids": ["p001", "p002", "p003"],
    "processing_params": { /* same as above */ }
}
```

### Export

```python
# POST /api/export/pdf
{
    "session_id": "abc123",
    "page_ids": ["p001", "p003", "p002"],  # Custom order
    "dpi": 300,
    "compression": "medium",
    "include_ocr": true
}
→ Returns: {
    "download_token": "xyz789",
    "download_url": "/download/xyz789",
    "expires_at": "2026-02-04T16:00:00Z",
    "file_size_mb": 2.4
}
```

---

## Image Processing Implementation

### Edge Detection

```python
def detect_document_edges(image):
    """
    Find document boundaries using contour detection.
    Returns the largest quadrilateral contour.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            return approx.reshape(4, 2)
    
    # Fallback to image bounds if no document detected
    h, w = image.shape[:2]
    return np.array([[0, 0], [w, 0], [w, h], [0, h]])
```

### Perspective Correction

```python
def correct_perspective(image, corners):
    """
    Apply perspective transform to flatten document.
    """
    # Order corners: top-left, top-right, bottom-right, bottom-left
    rect = order_points(corners)
    (tl, tr, br, bl) = rect
    
    # Compute target dimensions
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = int(max(width_a, width_b))
    
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = int(max(height_a, height_b))
    
    # Define destination points
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")
    
    # Apply perspective transform
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    return warped
```

---

## Error Handling Patterns

```python
# ALWAYS handle processing failures gracefully
def process_page(page_id, params):
    try:
        original = load_original_image(page_id)
        processed = apply_processing(original, params)
        save_processed_image(page_id, processed)
        return {"status": "success", "processed_url": f"/preview/{page_id}"}
    except DocumentNotDetectedError:
        # User can adjust manually
        return {"status": "warning", "message": "No document edges detected"}
    except Exception as e:
        # Log error, preserve original, return fallback
        log_error(page_id, e)
        return {"status": "error", "message": "Processing failed", "fallback_url": f"/originals/{page_id}"}

# NEVER let the server crash
@app.errorhandler(Exception)
def handle_error(error):
    log_error(error)
    return jsonify({"error": "Internal error", "recoverable": True}), 500
```

---

## Testing Expectations

When generating test code:

1. **Unit tests** for image processing functions
2. **Integration tests** for API endpoints
3. **Manual test scenarios** in README for streaming validation
4. **Performance benchmarks** for processing pipeline (target: <2s per page)

```python
def test_edge_detection():
    # Test with known document image
    image = cv2.imread('test_fixtures/receipt.jpg')
    corners = detect_document_edges(image)
    assert len(corners) == 4
    assert is_roughly_rectangular(corners)

def test_capture_preserves_original():
    # Ensure originals are never modified
    session_id = create_test_session()
    capture_image(session_id, test_frame)
    
    original_hash = hash_file(f'sessions/{session_id}/originals/latest.jpg')
    
    # Process with multiple filter sets
    process_page(page_id, {"enhance_mode": "grayscale"})
    process_page(page_id, {"enhance_mode": "bw"})
    
    # Original must remain unchanged
    assert hash_file(f'sessions/{session_id}/originals/latest.jpg') == original_hash
```

---

## Common Pitfalls to Avoid

### ❌ Don't Do This

```python
# Mixing concerns
def capture_and_enhance_and_save(frame):  # Too many responsibilities
    enhanced = process(frame)
    pdf = generate_pdf([enhanced])
    return pdf

# Destructive processing
def apply_filter(image_path):
    img = load(image_path)
    filtered = filter(img)
    save(filtered, image_path)  # Original lost!

# Blocking OCR
def export_pdf(pages):
    for page in pages:
        text = run_ocr(page)  # Blocks entire export
        add_to_pdf(page, text)
```

### ✅ Do This Instead

```python
# Single responsibility
def capture_image(session_id, frame_data):
    return save_original(session_id, frame_data)

def process_image(page_id, params):
    original = load_original(page_id)
    processed = apply_pipeline(original, params)
    save_processed(page_id, processed)

# Non-destructive
def apply_filter(page_id, filter_type):
    original = load_original(page_id)  # Always start from original
    filtered = apply(original, filter_type)
    save_processed(page_id, filtered)  # Separate file

# Asynchronous OCR
def export_pdf(session_id, include_ocr=False):
    pdf = build_pdf(session_id)
    if include_ocr:
        queue_ocr_job(session_id, pdf_id)  # Background job
    return pdf_download_link
```

---

## Documentation Requirements

When generating code, include:

1. **Docstrings** for all functions with parameters and return types
2. **Inline comments** for non-obvious logic (especially image processing math)
3. **API endpoint documentation** with request/response examples
4. **Configuration examples** in README
5. **Troubleshooting section** for common issues (camera permissions, HTTPS requirement)

---

## Security Considerations

Even without authentication, implement:

1. **Session token validation** - Reject invalid/expired tokens
2. **Path traversal prevention** - Sanitize all file paths
3. **Resource limits** - Max pages per session, max file size
4. **HTTPS requirement** for camera access (document in README)
5. **CORS configuration** - Only allow configured origins
6. **Cleanup jobs** - Auto-delete expired sessions

```python
# Session expiration
def cleanup_expired_sessions():
    cutoff = datetime.now() - timedelta(hours=4)
    for session_dir in glob('sessions/*'):
        if get_last_activity(session_dir) < cutoff:
            shutil.rmtree(session_dir)

# Path sanitization
def get_page_path(session_id, page_id):
    # Prevent directory traversal
    safe_session = re.match(r'^[a-zA-Z0-9_-]+$', session_id)
    safe_page = re.match(r'^[a-zA-Z0-9_-]+$', page_id)
    if not (safe_session and safe_page):
        raise ValueError("Invalid session or page ID")
    return f'sessions/{session_id}/originals/{page_id}.jpg'
```

---

## Development Workflow

1. **Start with minimal viable implementation** for each subsystem
2. **Validate assumptions** (especially streaming latency) before building on top
3. **Test on actual devices** (laptop + phone) as early as possible
4. **Prioritize correctness over features** - a working 80% is better than broken 100%
5. **Document tradeoffs** when making architectural decisions

---

## When Unsure

If you're generating code and encounter ambiguity:

1. **Prefer simple over clever** - readability and maintainability win
2. **Preserve user data** - when in doubt, don't delete or overwrite
3. **Fail explicitly** - return error messages, don't silently degrade
4. **Ask for clarification** - suggest options rather than guessing
5. **Reference this document** - these instructions are the source of truth

---

## Success Criteria

Code is correct when:

- A user can scan multi-page documents using desktop + phone without accounts or cloud
- Processing is non-destructive and batch editable
- PDFs are generated with proper DPI and optional OCR
- The system recovers gracefully from errors
- Code is maintainable by a single developer

---

**Remember**: This is a privacy-focused, local-first tool for power users. Every design decision should reinforce autonomy, transparency, and reliability over convenience or features.