/**
 * Mobile Camera Stream
 * Minimal interface for streaming camera to desktop
 * Phone acts purely as a camera sensor - no capture buttons or controls
 */

class MobileCameraStream {
    constructor() {
        this.sessionId = null;
        this.stream = null;
        this.ws = null;
        this.statusCheckInterval = null;
        this.frameInterval = null;
        this.canvas = null;
        this.context = null;
        
        this.elements = {
            video: document.getElementById('cameraVideo'),
            statusText: document.getElementById('statusText'),
            statusIndicator: document.getElementById('statusIndicator'),
            errorMessage: document.getElementById('errorMessage'),
            errorText: document.getElementById('errorText')
        };
        
        this.initialize();
    }
    
    /**
     * Initialize camera stream
     */
    async initialize() {
        try {
            // Get session ID from URL
            this.sessionId = this.getSessionIdFromUrl();
            
            if (!this.sessionId) {
                this.showError('Invalid session. Please scan the QR code again.');
                return;
            }
            
            // Validate session with server
            const valid = await this.validateSession();
            if (!valid) {
                this.showError('Session expired or invalid. Please create a new session on desktop.');
                return;
            }
            
            // Request camera permission and start streaming
            await this.startCameraStream();
            
            // Notify server that camera is connected
            await this.notifyServerConnected();
            
            // Start streaming video to server (WebSocket or WebRTC)
            this.startVideoStreaming();
            
            // Keep session alive
            this.startKeepAlive();
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError(`Failed to start camera: ${error.message}`);
        }
    }
    
    /**
     * Extract session ID from URL query parameters
     */
    getSessionIdFromUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get('session');
    }
    
    /**
     * Validate session with server
     */
    async validateSession() {
        try {
            const response = await fetch(`/api/session/${this.sessionId}/validate`);
            const data = await response.json();
            return data.valid;
        } catch (error) {
            console.error('Session validation error:', error);
            return false;
        }
    }
    
    /**
     * Start camera stream using MediaStream API
     */
    async startCameraStream() {
        this.updateStatus('Requesting camera access...');
        
        try {
            // Request rear camera with high resolution
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment', // Rear camera
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                },
                audio: false
            });
            
            // Attach stream to video element
            this.elements.video.srcObject = this.stream;
            
            this.updateStatus('Camera connected', true);
            
            // Prevent screen from sleeping
            this.preventScreenSleep();
            
        } catch (error) {
            console.error('Camera access error:', error);
            
            if (error.name === 'NotAllowedError') {
                throw new Error('Camera permission denied. Please allow camera access and reload.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No camera found on this device.');
            } else if (error.name === 'NotReadableError') {
                throw new Error('Camera is already in use by another application.');
            } else {
                throw new Error('Failed to access camera. Please ensure you are using HTTPS.');
            }
        }
    }
    
    /**
     * Notify server that camera is connected
     */
    async notifyServerConnected() {
        try {
            await fetch(`/api/session/${this.sessionId}/camera`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connected: true })
            });
        } catch (error) {
            console.error('Failed to notify server:', error);
        }
    }
    
    /**
     * Start streaming video to server
     * Captures frames from video element and sends via WebSocket
     */
    startVideoStreaming() {
        // Create canvas for frame capture
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        
        // Get video dimensions
        const video = this.elements.video;
        
        // Wait for video to have dimensions
        video.addEventListener('loadedmetadata', () => {
            this.canvas.width = video.videoWidth;
            this.canvas.height = video.videoHeight;
            
            // Connect WebSocket
            this.connectWebSocket();
        });
    }
    
    /**
     * Connect to WebSocket server for streaming
     */
    connectWebSocket() {
        try {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/stream/${this.sessionId}`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateStatus('Streaming video...', true);
                
                // Identify as mobile sender
                this.ws.send(JSON.stringify({ type: 'mobile' }));
                
                // Start sending frames
                this.startFrameCapture();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('Failed to connect to streaming server');
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.stopFrameCapture();
                this.updateStatus('Disconnected', false);
            };
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.showError('Failed to start video streaming');
        }
    }
    
    /**
     * Start capturing and sending video frames
     */
    startFrameCapture() {
        // Capture at 15 FPS (lower than camera for bandwidth optimization)
        const fps = 15;
        const interval = 1000 / fps;
        
        this.frameInterval = setInterval(() => {
            this.captureAndSendFrame();
        }, interval);
    }
    
    /**
     * Stop capturing frames
     */
    stopFrameCapture() {
        if (this.frameInterval) {
            clearInterval(this.frameInterval);
            this.frameInterval = null;
        }
    }
    
    /**
     * Capture a frame from video and send via WebSocket
     */
    captureAndSendFrame() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }
        
        try {
            const video = this.elements.video;
            
            // Draw current video frame to canvas
            this.context.drawImage(video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Convert to JPEG with compression (quality 0.7 for bandwidth optimization)
            this.canvas.toBlob((blob) => {
                if (blob && this.ws && this.ws.readyState === WebSocket.OPEN) {
                    // Convert blob to base64 and send
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const base64data = reader.result;
                        this.ws.send(JSON.stringify({
                            type: 'frame',
                            data: base64data,
                            timestamp: Date.now()
                        }));
                    };
                    reader.readAsDataURL(blob);
                }
            }, 'image/jpeg', 0.7);
            
        } catch (error) {
            console.error('Frame capture error:', error);
        }
    }
    
    /**
     * Send periodic keep-alive to maintain session
     */
    startKeepAlive() {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/session/${this.sessionId}/status`);
                if (!response.ok) {
                    throw new Error('Session expired');
                }
            } catch (error) {
                console.error('Session check failed:', error);
                this.showError('Session expired. Please scan a new QR code.');
                this.cleanup();
            }
        }, 5000); // Check every 5 seconds
    }
    
    /**
     * Prevent screen from sleeping while streaming
     */
    preventScreenSleep() {
        // Use Wake Lock API if available
        if ('wakeLock' in navigator) {
            navigator.wakeLock.request('screen').then(wakeLock => {
                console.log('Screen wake lock activated');
                this.wakeLock = wakeLock;
            }).catch(err => {
                console.warn('Wake lock failed:', err);
            });
        }
    }
    
    /**
     * Update status display
     */
    updateStatus(message, connected = false) {
        this.elements.statusText.textContent = message;
        
        if (connected) {
            this.elements.statusIndicator.className = 'indicator indicator-active';
        } else {
            this.elements.statusIndicator.className = 'indicator indicator-inactive';
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.elements.errorText.textContent = message;
        this.elements.errorMessage.classList.remove('hidden');
        this.updateStatus('Error', false);
    }
    
    /**
     * Cleanup resources on disconnect
     */
    cleanup() {
        // Stop camera stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        // Clear intervals
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        
        // Release wake lock
        if (this.wakeLock) {
            this.wakeLock.release();
        }
        
        // Close WebSocket
        if (this.ws) {
            this.ws.close();
        }
        
        // Notify server of disconnection
        if (this.sessionId) {
            fetch(`/api/session/${this.sessionId}/camera`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connected: false })
            }).catch(err => console.error('Failed to notify disconnect:', err));
        }
    }
}

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden - camera may pause');
    } else {
        console.log('Page visible - camera resumed');
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.cameraStream) {
        window.cameraStream.cleanup();
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cameraStream = new MobileCameraStream();
});
