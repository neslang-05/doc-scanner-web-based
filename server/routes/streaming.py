"""
Video Streaming Routes
WebSocket-based video streaming from mobile camera to desktop preview.
Uses a shared queue system for reliable frame delivery.
"""

from flask import Blueprint, request, jsonify
from flask_sock import Sock
import base64
import time
import json
import queue
import threading

# Import logging helper
try:
    from server.routes.logs import add_log
except ImportError:
    def add_log(level, source, message, details=None):
        print(f"[{level}] {source}: {message}")


streaming_bp = Blueprint('streaming', __name__, url_prefix='/api/streaming')

# Store active streaming connections with frame queues for each desktop client
active_streams = {}
# Lock for thread-safe access to active_streams
streams_lock = threading.Lock()


def init_streaming(app):
    """
    Initialize WebSocket support for the Flask app.
    
    Args:
        app: Flask application instance
    """
    global sock
    sock = Sock(app)
    
    @sock.route('/ws/stream/<session_id>')
    def stream_handler(ws, session_id):
        """
        WebSocket handler for video streaming.
        
        Args:
            ws: WebSocket connection
            session_id: Session identifier
        """
        add_log('INFO', 'streaming', f'WebSocket connection attempt', {'session_id': session_id[:12]})
        
        # Register this connection
        with streams_lock:
            if session_id not in active_streams:
                active_streams[session_id] = {
                    'mobile': None,
                    'desktop_queues': {},  # Changed: dict of client_id -> queue
                    'stats': {
                        'frames_received': 0,
                        'frames_sent': 0,
                        'start_time': time.time()
                    }
                }
        
        client_id = id(ws)  # Unique identifier for this connection
        frame_queue = None
        client_type = None
        
        try:
            # Determine if this is mobile (sender) or desktop (receiver)
            # First message should identify the client type
            first_msg = ws.receive()
            msg_data = json.loads(first_msg)
            
            client_type = msg_data.get('type')
            add_log('INFO', 'streaming', f'Client identified as {client_type}', {'session_id': session_id[:12], 'client_id': client_id})
            
            if client_type == 'mobile':
                # Mobile sender - receives frames and broadcasts to desktop viewers
                with streams_lock:
                    active_streams[session_id]['mobile'] = ws
                add_log('INFO', 'streaming', 'Mobile camera connected', {'session_id': session_id[:12]})
                
                # Handle incoming video frames from mobile
                while True:
                    try:
                        frame_data = ws.receive()
                        if frame_data:
                            with streams_lock:
                                active_streams[session_id]['stats']['frames_received'] += 1
                                
                                # Put frame in all desktop client queues
                                for q in active_streams[session_id]['desktop_queues'].values():
                                    try:
                                        # Non-blocking put, drop old frames if queue is full
                                        if q.full():
                                            try:
                                                q.get_nowait()
                                            except queue.Empty:
                                                pass
                                        q.put_nowait(frame_data)
                                    except queue.Full:
                                        pass  # Skip this frame for this client
                    except Exception as e:
                        add_log('ERROR', 'streaming', f'Mobile receive error: {str(e)}', {'session_id': session_id[:12]})
                        break
                        
            elif client_type == 'desktop':
                # Desktop receiver - receives frames via queue
                frame_queue = queue.Queue(maxsize=5)  # Buffer up to 5 frames
                
                with streams_lock:
                    active_streams[session_id]['desktop_queues'][client_id] = frame_queue
                add_log('INFO', 'streaming', 'Desktop viewer connected', {'session_id': session_id[:12], 'client_id': client_id})
                
                # Send frames from queue to this desktop client
                while True:
                    try:
                        # Wait for frame with timeout to allow checking connection
                        frame_data = frame_queue.get(timeout=1.0)
                        ws.send(frame_data)
                        with streams_lock:
                            active_streams[session_id]['stats']['frames_sent'] += 1
                    except queue.Empty:
                        # No frame available, send heartbeat to check connection
                        try:
                            ws.send(json.dumps({'type': 'heartbeat'}))
                        except Exception as hb_error:
                            add_log('WARNING', 'streaming', f'Heartbeat failed, closing connection: {str(hb_error)}', {'session_id': session_id[:12]})
                            break
                    except Exception as e:
                        add_log('ERROR', 'streaming', f'Desktop send error: {str(e)}', {'session_id': session_id[:12]})
                        break
                        
        except Exception as e:
            add_log('ERROR', 'streaming', f'Stream error: {str(e)}', {'session_id': session_id[:12]})
        finally:
            # Clean up on disconnect
            with streams_lock:
                if session_id in active_streams:
                    if client_type == 'mobile' and active_streams[session_id]['mobile'] == ws:
                        active_streams[session_id]['mobile'] = None
                        add_log('INFO', 'streaming', 'Mobile camera disconnected', {'session_id': session_id[:12]})
                    elif client_type == 'desktop' and client_id in active_streams[session_id]['desktop_queues']:
                        del active_streams[session_id]['desktop_queues'][client_id]
                        add_log('INFO', 'streaming', 'Desktop viewer disconnected', {'session_id': session_id[:12]})
                    
                    # Clean up session if no more connections
                    if (session_id in active_streams and 
                        not active_streams[session_id]['mobile'] and 
                        not active_streams[session_id]['desktop_queues']):
                        del active_streams[session_id]


@streaming_bp.route('/<session_id>/stats', methods=['GET'])
def get_streaming_stats(session_id):
    """
    Get streaming statistics for performance monitoring.
    
    Args:
        session_id: Session identifier
        
    Returns:
        JSON with streaming statistics
    """
    with streams_lock:
        if session_id not in active_streams:
            return jsonify({
                "active": False,
                "message": "No active stream"
            }), 404
        
        stats = active_streams[session_id]['stats']
        elapsed_time = time.time() - stats['start_time']
        
        return jsonify({
            "active": True,
            "mobile_connected": active_streams[session_id]['mobile'] is not None,
            "desktop_viewers": len(active_streams[session_id]['desktop_queues']),
            "frames_received": stats['frames_received'],
            "frames_sent": stats['frames_sent'],
            "elapsed_seconds": round(elapsed_time, 2),
            "fps_received": round(stats['frames_received'] / elapsed_time, 2) if elapsed_time > 0 else 0,
            "fps_sent": round(stats['frames_sent'] / elapsed_time, 2) if elapsed_time > 0 else 0
        }), 200
