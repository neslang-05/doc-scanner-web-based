"""
Video Streaming Routes
WebSocket-based video streaming from mobile camera to desktop preview.
"""

from flask import Blueprint, request, jsonify
from flask_sock import Sock
import base64
import time
import json


streaming_bp = Blueprint('streaming', __name__, url_prefix='/api/streaming')

# Store active streaming connections
active_streams = {}


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
        print(f"Stream connection established for session: {session_id}")
        
        # Register this connection
        if session_id not in active_streams:
            active_streams[session_id] = {
                'mobile': None,
                'desktop': [],
                'stats': {
                    'frames_received': 0,
                    'frames_sent': 0,
                    'start_time': time.time()
                }
            }
        
        try:
            # Determine if this is mobile (sender) or desktop (receiver)
            # First message should identify the client type
            first_msg = ws.receive()
            msg_data = json.loads(first_msg)
            
            client_type = msg_data.get('type')
            
            if client_type == 'mobile':
                # Mobile sender - receives frames and broadcasts to desktop viewers
                active_streams[session_id]['mobile'] = ws
                print(f"Mobile camera connected for session: {session_id}")
                
                # Handle incoming video frames from mobile
                while True:
                    try:
                        frame_data = ws.receive()
                        if frame_data:
                            active_streams[session_id]['stats']['frames_received'] += 1
                            
                            # Broadcast to all connected desktop viewers
                            desktop_clients = active_streams[session_id]['desktop']
                            for desktop_ws in desktop_clients[:]:  # Copy list to avoid modification issues
                                try:
                                    desktop_ws.send(frame_data)
                                    active_streams[session_id]['stats']['frames_sent'] += 1
                                except:
                                    # Remove disconnected desktop clients
                                    if desktop_ws in desktop_clients:
                                        desktop_clients.remove(desktop_ws)
                    except:
                        break
                        
            elif client_type == 'desktop':
                # Desktop receiver - receives frames from mobile
                active_streams[session_id]['desktop'].append(ws)
                print(f"Desktop viewer connected for session: {session_id}")
                
                # Keep connection alive and wait for frames
                # Frames are pushed from mobile handler
                while True:
                    try:
                        # Just keep the connection alive
                        # Actual frames are pushed from mobile handler
                        time.sleep(0.1)
                    except:
                        break
                        
        except Exception as e:
            print(f"Stream error for session {session_id}: {e}")
        finally:
            # Clean up on disconnect
            if session_id in active_streams:
                if active_streams[session_id]['mobile'] == ws:
                    active_streams[session_id]['mobile'] = None
                    print(f"Mobile camera disconnected for session: {session_id}")
                elif ws in active_streams[session_id]['desktop']:
                    active_streams[session_id]['desktop'].remove(ws)
                    print(f"Desktop viewer disconnected for session: {session_id}")
                
                # Clean up session if no more connections
                if not active_streams[session_id]['mobile'] and not active_streams[session_id]['desktop']:
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
        "desktop_viewers": len(active_streams[session_id]['desktop']),
        "frames_received": stats['frames_received'],
        "frames_sent": stats['frames_sent'],
        "elapsed_seconds": round(elapsed_time, 2),
        "fps_received": round(stats['frames_received'] / elapsed_time, 2) if elapsed_time > 0 else 0,
        "fps_sent": round(stats['frames_sent'] / elapsed_time, 2) if elapsed_time > 0 else 0
    }), 200
