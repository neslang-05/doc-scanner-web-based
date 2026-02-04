"""
Application Logs Routes
Provides endpoints for viewing server logs and streaming statistics.
"""

from flask import Blueprint, jsonify, request
from collections import deque
from datetime import datetime
import threading
import json

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

# Store recent logs in memory (circular buffer)
MAX_LOGS = 500
log_buffer = deque(maxlen=MAX_LOGS)
log_lock = threading.Lock()


def add_log(level, source, message, details=None):
    """
    Add a log entry to the buffer.
    
    Args:
        level: Log level (INFO, WARNING, ERROR, DEBUG)
        source: Source component (streaming, capture, session, etc.)
        message: Log message
        details: Optional additional details dict
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'source': source,
        'message': message,
        'details': details or {}
    }
    
    with log_lock:
        log_buffer.append(entry)


def get_recent_logs(count=100, level=None, source=None):
    """
    Get recent log entries with optional filtering.
    
    Args:
        count: Maximum number of logs to return
        level: Filter by log level
        source: Filter by source component
        
    Returns:
        List of log entries (newest first)
    """
    with log_lock:
        logs = list(log_buffer)
    
    # Filter by level
    if level:
        logs = [l for l in logs if l['level'] == level.upper()]
    
    # Filter by source
    if source:
        logs = [l for l in logs if l['source'] == source.lower()]
    
    # Return newest first, limited to count
    return list(reversed(logs))[:count]


@logs_bp.route('/', methods=['GET'])
def get_logs():
    """
    Get recent application logs.
    
    Query params:
        count: Number of logs to return (default 100, max 500)
        level: Filter by level (INFO, WARNING, ERROR, DEBUG)
        source: Filter by source component
        
    Returns:
        JSON array of log entries
    """
    count = min(int(request.args.get('count', 100)), MAX_LOGS)
    level = request.args.get('level')
    source = request.args.get('source')
    
    logs = get_recent_logs(count, level, source)
    
    return jsonify({
        'logs': logs,
        'total_in_buffer': len(log_buffer),
        'filters': {
            'count': count,
            'level': level,
            'source': source
        }
    }), 200


@logs_bp.route('/clear', methods=['POST'])
def clear_logs():
    """Clear all logs from the buffer."""
    with log_lock:
        log_buffer.clear()
    
    add_log('INFO', 'logs', 'Log buffer cleared')
    
    return jsonify({'message': 'Logs cleared'}), 200


@logs_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get application statistics including streaming stats.
    """
    from server.routes.streaming import active_streams, streams_lock
    from server.services.session_manager import SessionManager
    
    session_manager = SessionManager()
    
    # Get streaming stats
    streaming_stats = []
    with streams_lock:
        for session_id, stream_data in active_streams.items():
            stats = stream_data['stats']
            elapsed = (datetime.now().timestamp() - stats['start_time'])
            streaming_stats.append({
                'session_id': session_id[:8] + '...',
                'mobile_connected': stream_data['mobile'] is not None,
                'desktop_viewers': len(stream_data['desktop_queues']),
                'frames_received': stats['frames_received'],
                'frames_sent': stats['frames_sent'],
                'fps_in': round(stats['frames_received'] / elapsed, 1) if elapsed > 0 else 0,
                'fps_out': round(stats['frames_sent'] / elapsed, 1) if elapsed > 0 else 0,
                'elapsed_seconds': round(elapsed, 1)
            })
    
    # Count logs by level
    log_counts = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
    with log_lock:
        for log in log_buffer:
            if log['level'] in log_counts:
                log_counts[log['level']] += 1
    
    return jsonify({
        'streaming': {
            'active_sessions': len(streaming_stats),
            'sessions': streaming_stats
        },
        'logs': {
            'total': len(log_buffer),
            'by_level': log_counts
        },
        'server_time': datetime.now().isoformat()
    }), 200
