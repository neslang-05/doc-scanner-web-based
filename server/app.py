"""
Flask Application Entry Point
Main server for the web-based document scanner.
"""

# Monkey patch for gevent compatibility
import os
if os.environ.get('GEVENT_MONKEY_PATCH', 'False').lower() == 'true':
    from gevent import monkey
    monkey.patch_all()

from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
import os
from pathlib import Path

# Import route blueprints
from routes.session import session_bp
from routes.capture import capture_bp
from routes.streaming import streaming_bp, init_streaming
from routes.processing import processing_bp
from routes.export import export_bp
import threading
import time
import logging
import sys


def setup_logging(app):
    """Configure structured logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Also set level for relevant services
    logging.getLogger('services').setLevel(logging.INFO)
    logging.getLogger('routes').setLevel(logging.INFO)


def start_cleanup_worker(app):
    """Start a background thread to clean up expired sessions."""
    def cleanup_loop():
        from services.session_manager import SessionManager
        session_manager = SessionManager()
        while True:
            try:
                count = session_manager.cleanup_expired_sessions()
                if count > 0:
                    app.logger.info(f"Cleaned up {count} expired sessions")
            except Exception as e:
                app.logger.error(f"Cleanup error: {e}")
            
            # Run cleanup every hour
            time.sleep(3600)

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__, 
                static_folder='../static',
                static_url_path='/static')
    
    # Configure Logging
    setup_logging(app)
    
    # Application Configuration
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_FILE_SIZE_MB', 16)) * 1024 * 1024
    app.config['SESSION_DURATION_HOURS'] = int(os.environ.get('SESSION_DURATION_HOURS', 4))
    app.config['MAX_PAGES_PER_SESSION'] = int(os.environ.get('MAX_PAGES_PER_SESSION', 100))
    
    # Configure CORS for local network access
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/ws/*": {"origins": "*"}
    })
    
    # Initialize WebSocket support
    init_streaming(app)
    
    # Register blueprints
    app.register_blueprint(session_bp)
    app.register_blueprint(capture_bp)
    app.register_blueprint(streaming_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(export_bp)
    
    # Start session cleanup background thread
    start_cleanup_worker(app)
    
    # Ensure sessions directory exists
    sessions_dir = Path('sessions')
    sessions_dir.mkdir(exist_ok=True)
    
    # Add .gitignore to sessions directory
    gitignore_path = sessions_dir / '.gitignore'
    if not gitignore_path.exists():
        with open(gitignore_path, 'w') as f:
            f.write('*\n!.gitignore\n')
    
    # Root route - Desktop scanning interface
    @app.route('/')
    def index():
        """Serve the desktop scanning interface."""
        return send_from_directory('../static/desktop', 'index.html')
    
    # Mobile camera route
    @app.route('/mobile/camera')
    def mobile_camera():
        """Serve the mobile camera interface."""
        return send_from_directory('../static/mobile', 'camera.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring."""
        return {'status': 'ok', 'service': 'web-scanner'}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'recoverable': True}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Global exception handler to prevent crashes."""
        app.logger.error(f'Unhandled exception: {error}')
        return {'error': 'Internal error', 'recoverable': True}, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Railway compatibility - use PORT env var
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Run on all interfaces to allow mobile device access
    # HTTPS is required for camera access on mobile
    # For development, use a self-signed cert or ngrok
    print("\n" + "="*60)
    print("Web-Based Document Scanner")
    print("="*60)
    print(f"\nServer starting on http://{host}:{port}")
    print(f"Access from desktop: http://localhost:{port}")
    print(f"Access from mobile: http://<your-local-ip>:{port}")
    print("\nNote: HTTPS is required for mobile camera access.")
    print("For development, consider using ngrok or mkcert.")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=False)
