# Web-Based Document Scanner

A self-hosted, privacy-focused document scanning application that uses your desktop browser as the control interface and your smartphone as a wireless camera. No accounts, no cloud services, no data leaves your local network.

## Project Status

**Phase 1: Foundation** **COMPLETE**
- Flask server with session management
- QR code pairing system
- Desktop UI shell
- Mobile camera interface

**Phase 2: Streaming Validation** **COMPLETE**
- WebSocket video streaming (15 FPS)
- Live preview on desktop
- Latency monitoring (<500ms target)
- Bandwidth optimization

**Phase 3: Capture Pipeline** **COMPLETE**
- High-resolution still capture
- Image storage with thumbnails
- Desktop gallery with thumbnails
- Page deletion

**Phases 4-7: Coming Soon**
- Document edge detection and enhancement
- Multi-page reordering
- PDF export and OCR

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Smartphone with camera
- Local network connection

### Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```powershell
   python server/app.py
   ```

5. **Access the application**
   - Desktop: Open `http://localhost:5000` in your browser
   - Mobile: You'll get the URL via QR code

### Important: HTTPS for Mobile Camera

Modern browsers require HTTPS to access the camera on mobile devices. For development:

**Option 1: Use ngrok (Easiest)**
```powershell
# Install ngrok from https://ngrok.com
ngrok http 5000
```
Use the HTTPS URL provided by ngrok.

**Option 2: Self-signed certificate with mkcert**
```powershell
# Install mkcert
choco install mkcert

# Create local certificate
mkcert -install
mkcert localhost 192.168.1.* ::1

# Run Flask with SSL
python server/app.py --cert=localhost+2.pem --cert-key=localhost+2-key.pem
```

**Option 3: Temporary workaround (Chrome only)**
On mobile Chrome, you can enable camera on localhost:
1. Navigate to `chrome://flags`
2. Enable "Insecure origins treated as secure"
3. Add your local IP (e.g., `http://192.168.1.100:5000`)

## How to Use

### Basic Workflow

1. **Start the server** on your desktop/laptop
2. **Open the desktop interface** in your browser
3. **Click "New Session"** to create a scanning session
4. **Scan the QR code** with your smartphone
5. **Grant camera permissions** on your phone
6. **View live preview** on your desktop
7. **Click capture** (or press Space) to take photos
8. **Process and export** your multi-page documents as PDF

### Keyboard Shortcuts

- `Space` - Capture image from live camera preview
- (More shortcuts will be added in future phases)

## How It Works

### Video Streaming
- Mobile camera streams at 15 FPS via WebSocket
- JPEG compression (70% quality) for bandwidth optimization
- Real-time latency monitoring
- Typical latency: 100-300ms on local network

### Image Capture
- Captures full-resolution frames on demand
- Non-destructive storage (originals preserved)
- Automatic thumbnail generation
- Individual page management

## Project Architecture

### System Components

```
Desktop Browser          Mobile Browser          Flask Server
(Control Surface)        (Camera Sensor)         (Orchestrator)
      ↕                       ↕                       ↕
  Controls UI    ←→    Streams Video    ←→    Processes Images
      ↕                                             ↕
  Export PDFs                               Manages Sessions
```

### File Structure

```
web-based-scanner/
├── server/
│   ├── app.py                  # Flask application entry
│   ├── routes/
│   │   └── session.py          # Session management API
│   ├── services/
│   │   └── session_manager.py  # Session logic
│   └── utils/
│       └── qr_generator.py     # QR code creation
├── static/
│   ├── desktop/
│   │   ├── index.html          # Desktop scanning UI
│   │   ├── scanner.js          # Desktop controller
│   │   └── styles.css          # Desktop styles
│   └── mobile/
│       ├── camera.html         # Mobile camera page
│       └── camera.js           # Camera streaming
├── sessions/                   # Runtime data (auto-created)
│   └── {session_id}/
│       ├── originals/
│       ├── processed/
│       └── metadata.json
├── requirements.txt
└── README.md
```

## Deployment

### Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/web-based-scanner)

1. Click the button above.
2. Connect your GitHub account.
3. Render will use the `render.yaml` blueprint to set up the service.
4. Your scanner will be live at `https://web-document-scanner.onrender.com`.

**Note**: Since Render's free tier uses an ephemeral filesystem, session data will be lost when the service spins down or restarts. Download your PDFs immediately.

### Local Deployment

1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start the server: `python server/app.py`.
4. Access via `http://localhost:5000`.

## Privacy & Security

### Privacy by Architecture

- **No user accounts** - No registration, no passwords
- **Local-only processing** - Everything happens on your network
- **No telemetry** - Zero data collection or tracking
- **Session-based** - Data auto-expires after 4 hours
- **Non-destructive** - Original images always preserved

### Security Considerations

While this app doesn't require authentication (by design), it implements:

- Session token validation
- Path traversal prevention
- Resource limits (max pages, file sizes)
- Automatic session expiration and cleanup
- Input sanitization

**Important**: This application is designed for **private, local use**. Do not expose it to the public internet without adding authentication and additional security measures.

## Development

### Running in Development Mode

```powershell
# Enable debug mode
$env:FLASK_ENV = "development"
python server/app.py
```

### Project Phases

1. **Phase 1: Foundation** 
   - Session management, QR pairing, basic UI

2. **Phase 2: Streaming Validation** 
   - WebRTC/WebSocket video streaming
   - **Gate**: Must achieve <500ms latency

3. **Phase 3: Capture Pipeline**
   - High-res still capture
   - Image storage

4. **Phase 4: Image Processing**
   - Edge detection
   - Perspective correction
   - Enhancement filters

5. **Phase 5: Document Management**
   - Multi-page handling
   - Reordering and deletion

6. **Phase 6: Export and OCR**
   - PDF assembly
   - Optional OCR

7. **Phase 7: Sharing**
   - Temporary download links

### Adding Features

See [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) for detailed implementation guidelines.

## Troubleshooting

### Camera won't connect on mobile

- **Check HTTPS**: Camera requires HTTPS on mobile (except localhost)
- **Grant permissions**: Ensure camera access is allowed
- **Check network**: Desktop and mobile must be on same network
- **Session expired**: Create a new session if QR code is old

### Video preview not showing

- **Check session status**: Verify camera is connected in desktop UI
- **Browser compatibility**: Use Chrome, Firefox, or Safari
- **Check console**: Open browser DevTools for error messages
- **WebSocket connection**: Ensure port 5000 is accessible
- **Try reconnecting**: Refresh mobile page to reconnect stream

### Captured images not appearing

- **Check network**: Ensure stable connection during capture
- **Storage space**: Verify sufficient disk space in sessions/ directory
- **Refresh gallery**: Reload desktop page if thumbnails don't appear

### Session expires too quickly

Edit `server/services/session_manager.py`:
```python
def __init__(self, sessions_dir: str = "sessions", session_duration_hours: int = 8):
    # Changed from 4 to 8 hours
```

## API Documentation

### Create Session
```
POST /api/session/create
Response: {
  "session_id": "abc123",
  "created_at": "2026-02-04T10:30:00Z",
  "expires_at": "2026-02-04T14:30:00Z",
  "qr_code_data": "data:image/png;base64,...",
  "mobile_url": "http://..."
}
```

### Get Session Status
```
GET /api/session/{session_id}/status
### Capture Image
```
POST /api/capture/{session_id}
Body: {
  "image_data": "base64...",
  "format": "jpeg",
  "resolution": {"width": 1920, "height": 1080}
}
Response: {
  "page_id": "page_1738656000000",
  "thumbnail_url": "/api/capture/{session_id}/{page_id}/thumbnail",
  "original_url": "/api/capture/{session_id}/{page_id}/original"
}
```

### Get All Pages
```
GET /api/capture/{session_id}/pages
Response: {
  "session_id": "abc123",
  "page_count": 3,
  "pages": [...]
}
```

### Delete Page
```
DELETE /api/capture/{session_id}/{page_id}
```

### Streaming Statistics
```
GET /api/streaming/{session_id}/stats
Response: {
  "active": true,
  "frames_received": 450,
  "fps_received": 15.2,
  "avgLatency": 120
}
```
  "session_id": "abc123",
  "camera_connected": true,
  "page_count": 5,
  "last_activity": "2026-02-04T12:15:00Z"
}
```

### Update Camera Status
```
POST /api/session/{session_id}/camera
Body: { "connected": true }
```

More endpoints will be added in future phases.

## Contributing

This is a personal project focused on privacy and local-first operation. Contributions welcome! Please:

1. Respect the core constraints (no auth, no cloud, local-first)
2. Follow the existing code style
3. Test on actual devices (desktop + mobile)
4. Update documentation

## License

MIT License - See LICENSE file for details

## Acknowledgments

Inspired by CamScanner but built with privacy and self-hosting as first principles.

## Support

For issues, questions, or suggestions, please open an issue on the project repository.

---