"""
Image Capture Routes
API endpoints for capturing and managing scanned document images.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from services.session_manager import SessionManager
from services.image_storage import ImageStorage
import time
import base64
import io
from pathlib import Path


capture_bp = Blueprint('capture', __name__, url_prefix='/api/capture')
session_manager = SessionManager()
image_storage = ImageStorage()


@capture_bp.route('/<session_id>', methods=['POST'])
def capture_image(session_id):
    """
    Capture a high-resolution image from the mobile camera.
    
    Args:
        session_id: Session identifier
        
    Request body:
        {
            "image_data": "base64 encoded image",
            "format": "jpeg" | "png",
            "resolution": {"width": 1920, "height": 1080}
        }
        
    Returns:
        JSON with page_id and thumbnail URL
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        # Check page count limit
        status = session_manager.get_session_status(session_id)
        if status and status.get('page_count', 0) >= current_app.config['MAX_PAGES_PER_SESSION']:
            return jsonify({"error": f"Maximum page limit reached ({current_app.config['MAX_PAGES_PER_SESSION']})"}), 400
        
        # Get image data from request
        data = request.get_json()
        image_data_base64 = data.get('image_data')
        image_format = data.get('format', 'jpeg')
        resolution = data.get('resolution', {})
        
        if not image_data_base64:
            return jsonify({"error": "No image data provided"}), 400
        
        # Generate page ID
        page_id = f"page_{int(time.time() * 1000)}"
        
        # Store original image
        result = image_storage.store_original(
            session_id=session_id,
            page_id=page_id,
            image_data_base64=image_data_base64,
            image_format=image_format,
            metadata={
                "resolution": resolution,
                "captured_at": time.time()
            }
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 500
        
        # Add page to session
        session_manager.add_page(
            session_id=session_id,
            page_id=page_id,
            original_path=result['original_path']
        )
        
        # Generate thumbnail
        thumbnail_result = image_storage.generate_thumbnail(
            session_id=session_id,
            page_id=page_id
        )
        
        return jsonify({
            "success": True,
            "page_id": page_id,
            "thumbnail_url": f"/api/capture/{session_id}/{page_id}/thumbnail",
            "original_url": f"/api/capture/{session_id}/{page_id}/original",
            "captured_at": result['captured_at']
        }), 200
        
    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify({"error": str(e)}), 500


@capture_bp.route('/<session_id>/<page_id>/original', methods=['GET'])
def get_original_image(session_id, page_id):
    """
    Retrieve the original captured image.
    
    Args:
        session_id: Session identifier
        page_id: Page identifier
        
    Returns:
        Image file
    """
    try:
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        image_path = image_storage.get_original_path(session_id, page_id)
        
        if not image_path or not Path(image_path).exists():
            return jsonify({"error": "Image not found"}), 404
        
        return send_file(image_path, mimetype='image/jpeg')
        
    except Exception as e:
        print(f"Error retrieving original: {e}")
        return jsonify({"error": str(e)}), 500


@capture_bp.route('/<session_id>/<page_id>/thumbnail', methods=['GET'])
def get_thumbnail(session_id, page_id):
    """
    Retrieve the thumbnail of a captured image.
    
    Args:
        session_id: Session identifier
        page_id: Page identifier
        
    Returns:
        Thumbnail image file
    """
    try:
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        thumbnail_path = image_storage.get_thumbnail_path(session_id, page_id)
        
        if not thumbnail_path or not Path(thumbnail_path).exists():
            # Try to generate thumbnail if it doesn't exist
            image_storage.generate_thumbnail(session_id, page_id)
            thumbnail_path = image_storage.get_thumbnail_path(session_id, page_id)
        
        if not thumbnail_path or not Path(thumbnail_path).exists():
            return jsonify({"error": "Thumbnail not found"}), 404
        
        return send_file(thumbnail_path, mimetype='image/jpeg')
        
    except Exception as e:
        print(f"Error retrieving thumbnail: {e}")
        return jsonify({"error": str(e)}), 500


@capture_bp.route('/<session_id>/pages', methods=['GET'])
def get_all_pages(session_id):
    """
    Get list of all captured pages in a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        JSON array of page information
    """
    try:
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        pages = session_manager.get_pages(session_id)
        
        # Enrich with URLs
        for page in pages:
            page_id = page['page_id']
            page['thumbnail_url'] = f"/api/capture/{session_id}/{page_id}/thumbnail"
            page['original_url'] = f"/api/capture/{session_id}/{page_id}/original"
        
        return jsonify({
            "session_id": session_id,
            "page_count": len(pages),
            "pages": pages
        }), 200
        
    except Exception as e:
        print(f"Error retrieving pages: {e}")
        return jsonify({"error": str(e)}), 500


@capture_bp.route('/<session_id>/<page_id>', methods=['DELETE'])
def delete_page(session_id, page_id):
    """
    Delete a captured page.
    
    Args:
        session_id: Session identifier
        page_id: Page identifier
        
    Returns:
        JSON with success status
    """
    try:
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        # Delete image files
        success = image_storage.delete_page(session_id, page_id)
        
        if not success:
            return jsonify({"error": "Failed to delete page"}), 500
        
        # Remove from session metadata (would need to add this method to session_manager)
        # For now, just return success
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error deleting page: {e}")
        return jsonify({"error": str(e)}), 500
