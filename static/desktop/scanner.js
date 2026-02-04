/**
 * Desktop Scanner Controller
 * Manages the main scanning interface, session state, and user interactions.
 */

class DesktopScanner {
    constructor() {
        this.sessionId = null;
        this.cameraConnected = false;
        this.capturedPages = [];
        this.processingParams = {};
        this.ws = null;
        this.streamImg = null;
        this.latencyStats = { samples: [], avgLatency: 0 };
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkExistingSession();
    }
    
    /**
     * Cache DOM element references
     */
    initializeElements() {
        this.elements = {
            // Buttons
            newSessionBtn: document.getElementById('newSessionBtn'),
            captureBtn: document.getElementById('captureBtn'),
            processAllBtn: document.getElementById('processAllBtn'),
            exportPdfBtn: document.getElementById('exportPdfBtn'),
            
            // Displays
            sessionInfo: document.getElementById('sessionInfo'),
            cameraStatus: document.getElementById('cameraStatus'),
            pageCount: document.getElementById('pageCount'),
            qrCodeDisplay: document.getElementById('qrCodeDisplay'),
            qrCodeImage: document.getElementById('qrCodeImage'),
            mobileUrl: document.getElementById('mobileUrl'),
            livePreview: document.getElementById('livePreview'),
            previewPlaceholder: document.getElementById('previewPlaceholder'),
            previewVideo: document.getElementById('previewVideo'),
            pagesGallery: document.getElementById('pagesGallery'),
            
            // Options
            autoDetectEdges: document.getElementById('autoDetectEdges'),
            autoCaptureMode: document.getElementById('autoCaptureMode'),
            
            // Modal Elements
            processingModal: document.getElementById('processingModal'),
            enhanceMode: document.getElementById('enhanceMode'),
            correctPerspective: document.getElementById('correctPerspective'),
            normalizeLighting: document.getElementById('normalizeLighting'),
            applyProcessingBtn: document.getElementById('applyProcessing'),
            cancelProcessingBtn: document.getElementById('cancelProcessing'),
            modalClose: document.querySelector('.modal-close')
        };
    }
    
    /**
     * Attach event listeners to UI elements
     */
    attachEventListeners() {
        this.elements.newSessionBtn.addEventListener('click', () => this.createNewSession());
        this.elements.captureBtn.addEventListener('click', () => this.captureImage());
        this.elements.processAllBtn.addEventListener('click', () => this.showProcessingModal());
        this.elements.exportPdfBtn.addEventListener('click', () => this.exportPdf());
        
        // Modal Events
        this.elements.applyProcessingBtn.addEventListener('click', () => this.applyBatchProcessing());
        this.elements.cancelProcessingBtn.addEventListener('click', () => this.hideProcessingModal());
        this.elements.modalClose.addEventListener('click', () => this.hideProcessingModal());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.cameraConnected) {
                e.preventDefault();
                this.captureImage();
            }
        });
    }
    
    /**
     * Check if there's an existing session in localStorage
     */
    checkExistingSession() {
        const savedSessionId = localStorage.getItem('scanner_session_id');
        if (savedSessionId) {
            this.validateAndRestoreSession(savedSessionId);
        } else {
            this.showWelcomeState();
        }
    }
    
    /**
     * Show initial welcome state
     */
    showWelcomeState() {
        this.elements.previewPlaceholder.style.display = 'flex';
        this.elements.qrCodeDisplay.style.display = 'none';
        this.elements.livePreview.style.display = 'none';
    }
    
    /**
     * Create a new scanning session
     */
    async createNewSession() {
        try {
            this.showToast('Creating new session...', 'info');
            
            const response = await fetch('/api/session/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error('Failed to create session');
            }
            
            const data = await response.json();
            
            this.sessionId = data.session_id;
            localStorage.setItem('scanner_session_id', this.sessionId);
            
            this.updateSessionInfo(data);
            this.displayQRCode(data);
            this.startSessionPolling();
            
            this.showToast('Session created! Scan QR code to connect camera.', 'success');
            
        } catch (error) {
            console.error('Error creating session:', error);
            this.showToast('Failed to create session', 'error');
        }
    }
    
    /**
     * Validate and restore an existing session
     */
    async validateAndRestoreSession(sessionId) {
        try {
            const response = await fetch(`/api/session/${sessionId}/validate`);
            const data = await response.json();
            
            if (data.valid) {
                this.sessionId = sessionId;
                this.loadSessionStatus();
            } else {
                localStorage.removeItem('scanner_session_id');
                this.showWelcomeState();
            }
            
        } catch (error) {
            console.error('Error validating session:', error);
            localStorage.removeItem('scanner_session_id');
            this.showWelcomeState();
        }
    }
    
    /**
     * Load current session status
     */
    async loadSessionStatus() {
        try {
            const response = await fetch(`/api/session/${this.sessionId}/status`);
            if (!response.ok) {
                throw new Error('Session not found');
            }
            
            const status = await response.json();
            
            this.updateSessionInfo({
                session_id: status.session_id,
                expires_at: status.expires_at
            });
            
            this.updateCameraStatus(status.camera_connected);
            this.updatePageCount(status.page_count);
            
            // Load existing pages
            await this.loadCapturedPages();
            
            // Recreate QR code for this session
            const qrResponse = await fetch('/api/session/create', { method: 'POST' });
            // Note: This creates a new session, need to refactor to just get QR for existing session
            
            this.startSessionPolling();
            
        } catch (error) {
            console.error('Error loading session:', error);
            this.showWelcomeState();
        }
    }
    
    /**
     * Load captured pages from server
     */
    async loadCapturedPages() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/capture/${this.sessionId}/pages`);
            if (response.ok) {
                const data = await response.json();
                this.capturedPages = data.pages || [];
                this.updatePageCount(this.capturedPages.length);
                this.renderPageGallery();
            }
        } catch (error) {
            console.error('Error loading pages:', error);
        }
    }
    
    /**
     * Update session info display
     */
    updateSessionInfo(data) {
        const expiresAt = new Date(data.expires_at);
        this.elements.sessionInfo.textContent = 
            `Session: ${data.session_id.substring(0, 8)}... (expires ${expiresAt.toLocaleTimeString()})`;
    }
    
    /**
     * Display QR code for mobile pairing
     */
    displayQRCode(data) {
        this.elements.qrCodeImage.innerHTML = `<img src="${data.qr_code_data}" alt="QR Code">`;
        this.elements.mobileUrl.textContent = data.mobile_url;
        
        this.elements.previewPlaceholder.style.display = 'none';
        this.elements.qrCodeDisplay.style.display = 'flex';
        this.elements.livePreview.style.display = 'none';
    }
    
    /**
     * Update camera connection status
     */
    updateCameraStatus(connected) {
        this.cameraConnected = connected;
        
        if (connected) {
            this.elements.cameraStatus.textContent = 'Connected';
            this.elements.cameraStatus.className = 'status-badge status-connected';
            this.elements.qrCodeDisplay.style.display = 'none';
            this.elements.livePreview.style.display = 'block';
            this.elements.captureBtn.disabled = false;
            
            // Connect to video stream
            this.connectToVideoStream();
        } else {
            this.elements.cameraStatus.textContent = 'Disconnected';
            this.elements.cameraStatus.className = 'status-badge status-disconnected';
            this.elements.captureBtn.disabled = true;
            
            // Disconnect from video stream
            this.disconnectVideoStream();
        }
    }
    
    /**
     * Connect to WebSocket video stream from mobile
     */
    connectToVideoStream() {
        if (!this.sessionId) return;
        
        try {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/stream/${this.sessionId}`;
            
            this.ws = new WebSocket(wsUrl);
            
            // Create image element for displaying frames
            if (!this.streamImg) {
                this.streamImg = document.createElement('img');
                this.streamImg.style.width = '100%';
                this.streamImg.style.height = '100%';
                this.streamImg.style.objectFit = 'contain';
                this.elements.previewVideo.replaceWith(this.streamImg);
                this.elements.previewVideo = this.streamImg;
            }
            
            this.ws.onopen = () => {
                console.log('Desktop WebSocket connected');
                // Identify as desktop receiver
                this.ws.send(JSON.stringify({ type: 'desktop' }));
                this.showToast('Live preview connected', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'frame') {
                        // Update preview with new frame
                        this.streamImg.src = data.data;
                        
                        // Update latency if timestamp provided
                        if (data.timestamp) {
                            const latency = Date.now() - data.timestamp;
                            this.updateLatencyStats(latency);
                        }
                    }
                } catch (error) {
                    console.error('Frame processing error:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showToast('Stream connection error', 'error');
            };
            
            this.ws.onclose = () => {
                console.log('Desktop WebSocket closed');
                this.showToast('Live preview disconnected', 'warning');
            };
            
        } catch (error) {
            console.error('Failed to connect to video stream:', error);
            this.showToast('Failed to connect to video stream', 'error');
        }
    }
    
    /**
     * Disconnect from video stream
     */
    disconnectVideoStream() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    /**
     * Update latency statistics for monitoring
     */
    updateLatencyStats(latency) {
        this.latencyStats.samples.push(latency);
        
        // Keep only last 30 samples
        if (this.latencyStats.samples.length > 30) {
            this.latencyStats.samples.shift();
        }
        
        // Calculate average
        const sum = this.latencyStats.samples.reduce((a, b) => a + b, 0);
        this.latencyStats.avgLatency = Math.round(sum / this.latencyStats.samples.length);
        
        // Update UI (if latency display exists)
        // For now, just log if latency is high
        if (this.latencyStats.avgLatency > 500) {
            console.warn(`High latency: ${this.latencyStats.avgLatency}ms`);
        }
    }
    
    /**
     * Poll session status periodically
     */
    startSessionPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        this.pollingInterval = setInterval(async () => {
            if (!this.sessionId) return;
            
            try {
                const response = await fetch(`/api/session/${this.sessionId}/status`);
                if (!response.ok) throw new Error('Session expired');
                
                const status = await response.json();
                this.updateCameraStatus(status.camera_connected);
                this.updatePageCount(status.page_count);
                
            } catch (error) {
                console.error('Session polling error:', error);
                clearInterval(this.pollingInterval);
                this.showToast('Session expired', 'warning');
            }
        }, 2000);
    }
    
    /**
     * Capture an image from the camera
     */
    async captureImage() {
        if (!this.cameraConnected) return;
        
        try {
            // Get current frame from video preview
            const canvas = document.createElement('canvas');
            const img = this.streamImg || this.elements.previewVideo;
            
            // Set canvas size to match image
            canvas.width = img.naturalWidth || img.videoWidth || 1920;
            canvas.height = img.naturalHeight || img.videoHeight || 1080;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            // Convert to base64 JPEG
            const imageData = canvas.toDataURL('image/jpeg', 0.95).split(',')[1];
            
            // Send to server
            const response = await fetch(`/api/capture/${this.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_data: imageData,
                    format: 'jpeg',
                    resolution: {
                        width: canvas.width,
                        height: canvas.height
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error('Capture failed');
            }
            
            const result = await response.json();
            
            // Add to captured pages
            this.capturedPages.push(result);
            this.updatePageCount(this.capturedPages.length);
            this.renderPageGallery();
            
            this.showToast('Image captured!', 'success');
            
            // Visual feedback
            this.flashCaptureEffect();
            
        } catch (error) {
            console.error('Capture error:', error);
            this.showToast('Capture failed', 'error');
        }
    }
    
    /**
     * Visual feedback for capture
     */
    flashCaptureEffect() {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.background = 'white';
        overlay.style.opacity = '0.8';
        overlay.style.zIndex = '9999';
        overlay.style.pointerEvents = 'none';
        overlay.style.transition = 'opacity 0.3s';
        
        document.body.appendChild(overlay);
        
        setTimeout(() => {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        }, 100);
    }
    
    /**
     * View a captured page in full size
     */
    viewPage(pageId) {
        const page = this.capturedPages.find(p => p.page_id === pageId);
        if (page) {
            window.open(page.original_url, '_blank');
        }
    }
    
    /**
     * Delete a captured page
     */
    async deletePage(pageId) {
        if (!confirm('Delete this page?')) return;
        
        try {
            const response = await fetch(`/api/capture/${this.sessionId}/${pageId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.capturedPages = this.capturedPages.filter(p => p.page_id !== pageId);
                this.updatePageCount(this.capturedPages.length);
                this.renderPageGallery();
                this.showToast('Page deleted', 'success');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showToast('Failed to delete page', 'error');
        }
    }
    
    /**
     * Update page count display
     */
    updatePageCount(count) {
        this.elements.pageCount.textContent = count;
        
        const hasPages = count > 0;
        this.elements.processAllBtn.disabled = !hasPages;
        this.elements.exportPdfBtn.disabled = !hasPages;
    }
    
    /**
     * Render captured pages gallery
     */
    renderPageGallery() {
        if (this.capturedPages.length === 0) {
            this.elements.pagesGallery.innerHTML = `
                <div class="gallery-empty">
                    <p>No pages captured yet</p>
                    <p class="hint">Click the capture button or press Space to capture a page</p>
                </div>
            `;
            return;
        }
        
        const galleryHtml = this.capturedPages.map((page, index) => `
            <div class="page-thumbnail" data-page-id="${page.page_id}">
                <div class="thumbnail-image" onclick="window.scanner.viewPage('${page.page_id}')" style="background-image: url('${page.thumbnail_url}')">
                    <span class="page-number">${index + 1}</span>
                </div>
                <div class="thumbnail-actions">
                    <button class="btn-icon" title="Move Up" onclick="window.scanner.movePage('${page.page_id}', -1)" ${index === 0 ? 'disabled' : ''}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
                    </button>
                    <button class="btn-icon" title="Move Down" onclick="window.scanner.movePage('${page.page_id}', 1)" ${index === this.capturedPages.length - 1 ? 'disabled' : ''}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    </button>
                    <button class="btn-icon" title="Delete" onclick="window.scanner.deletePage('${page.page_id}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>
            </div>
        `).join('');
        
        this.elements.pagesGallery.innerHTML = galleryHtml;
    }

    /**
     * Move page in order
     */
    async movePage(pageId, direction) {
        const index = this.capturedPages.findIndex(p => p.page_id === pageId);
        if (index === -1) return;
        
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.capturedPages.length) return;
        
        // Swap
        const temp = this.capturedPages[index];
        this.capturedPages[index] = this.capturedPages[newIndex];
        this.capturedPages[newIndex] = temp;
        
        // Sync with server
        try {
            await fetch(`/api/process/${this.sessionId}/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_order: this.capturedPages.map(p => p.page_id)
                })
            });
            this.renderPageGallery();
        } catch (error) {
            console.error('Reorder sync error:', error);
        }
    }
    
    /**
     * Show processing options modal
     */
    showProcessingModal() {
        this.elements.processingModal.style.display = 'flex';
    }
    
    /**
     * Hide processing options modal
     */
    hideProcessingModal() {
        this.elements.processingModal.style.display = 'none';
    }
    
    /**
     * Apply processing to all captured pages
     */
    async applyBatchProcessing() {
        if (!this.sessionId || this.capturedPages.length === 0) return;
        
        const params = {
            enhance_mode: this.elements.enhanceMode.value,
            correct_perspective: this.elements.correctPerspective.checked,
            normalize_lighting: this.elements.normalizeLighting.checked
        };
        
        try {
            this.hideProcessingModal();
            this.showToast('Processing all pages...', 'info');
            
            const response = await fetch(`/api/process/${this.sessionId}/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_ids: this.capturedPages.map(p => p.page_id),
                    processing_params: params
                })
            });
            
            if (!response.ok) {
                throw new Error('Batch processing failed');
            }
            
            const result = await response.json();
            this.showToast(`Processed ${result.processed_count} pages successfully`, 'success');
            
            // Reload pages to show updated thumbnails
            await this.loadCapturedPages();
            
        } catch (error) {
            console.error('Processing error:', error);
            this.showToast('Failed to process pages', 'error');
        }
    }
    
    /**
     * Export captured pages as PDF
     */
    async exportPdf() {
        if (!this.sessionId || this.capturedPages.length === 0) return;
        
        try {
            this.showToast('Generating PDF...', 'info');
            
            const response = await fetch(`/api/export/${this.sessionId}/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_ids: this.capturedPages.map(p => p.page_id),
                    dpi: 300,
                    compression: 'medium',
                    include_ocr: false
                })
            });
            
            if (!response.ok) {
                throw new Error('PDF export failed');
            }
            
            const result = await response.json();
            
            if (result.download_url) {
                this.showToast('PDF ready! Download starting...', 'success');
                
                // Create a temporary link and click it
                const link = document.createElement('a');
                link.href = result.download_url;
                link.download = result.filename || 'scanned_document.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                throw new Error('No download URL returned');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Failed to export PDF', 'error');
        }
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('toast-show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('toast-show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize scanner when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.scanner = new DesktopScanner();
});
