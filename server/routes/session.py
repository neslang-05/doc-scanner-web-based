"""
Session Management Routes
API endpoints for session creation, validation, and status checking.
"""

from flask import Blueprint, jsonify, request
from services.session_manager import SessionManager
from utils.qr_generator import generate_pairing_qr


session_bp = Blueprint('session', __name__, url_prefix='/api/session')
session_manager = SessionManager()


@session_bp.route('/create', methods=['POST'])
def create_session():
    """
    Create a new scanning session.
    
    Returns:
        JSON with session_id, created_at, expires_at, qr_code_url
    """
    try:
        session_data = session_manager.create_session()
        
        # Get server URL for QR code
        server_url = request.host_url.rstrip('/')
        session_id = session_data['session_id']
        
        # Generate QR code
        _, qr_data_uri = generate_pairing_qr(session_id, server_url)
        
        response = {
            "session_id": session_id,
            "created_at": session_data['created_at'],
            "expires_at": session_data['expires_at'],
            "qr_code_data": qr_data_uri,
            "mobile_url": f"{server_url}/mobile/camera?session={session_id}"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@session_bp.route('/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """
    Get current status of a session.
    
    Args:
        session_id: Session identifier from URL path
        
    Returns:
        JSON with session status or error
    """
    try:
        status = session_manager.get_session_status(session_id)
        
        if not status:
            return jsonify({"error": "Session not found or expired"}), 404
            
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@session_bp.route('/<session_id>/validate', methods=['GET'])
def validate_session(session_id):
    """
    Validate if a session is active and not expired.
    
    Args:
        session_id: Session identifier from URL path
        
    Returns:
        JSON with valid: true/false
    """
    try:
        valid = session_manager.validate_session(session_id)
        return jsonify({"valid": valid}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@session_bp.route('/<session_id>/camera', methods=['POST'])
def update_camera_status(session_id):
    """
    Update camera connection status.
    
    Args:
        session_id: Session identifier from URL path
        
    Request body:
        {"connected": true/false}
        
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        connected = data.get('connected', False)
        
        success = session_manager.update_camera_status(session_id, connected)
        
        if not success:
            return jsonify({"error": "Failed to update camera status"}), 400
            
        return jsonify({"success": True}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@session_bp.route('/<session_id>/delete', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete a session and all its data.
    
    Args:
        session_id: Session identifier from URL path
        
    Returns:
        JSON with success status
    """
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            return jsonify({"error": "Failed to delete session"}), 400
            
        return jsonify({"success": True}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@session_bp.route('/cleanup', methods=['POST'])
def cleanup_sessions():
    """
    Manually trigger cleanup of expired sessions.
    Admin/maintenance endpoint.
    
    Returns:
        JSON with number of sessions cleaned
    """
    try:
        cleaned = session_manager.cleanup_expired_sessions()
        return jsonify({"cleaned_sessions": cleaned}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
