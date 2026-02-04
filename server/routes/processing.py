"""
Processing Routes
API endpoints for image processing and enhancement.
"""

from flask import Blueprint, request, jsonify, send_file
from services.session_manager import SessionManager
from services.image_storage import ImageStorage
from services.image_processor import ImageProcessor
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

processing_bp = Blueprint('processing', __name__, url_prefix='/api/process')
session_manager = SessionManager()
image_storage = ImageStorage()
image_processor = ImageProcessor()


@processing_bp.route('/<session_id>/<page_id>', methods=['POST'])
def process_page(session_id, page_id):
    """
    Process a single page with specified parameters.
    
    Request body:
    {
        "detect_edges": true,
        "correct_perspective": true,
        "normalize_lighting": true,
        "enhance_mode": "grayscale",  // "color", "grayscale", or "bw"
        "enhance_image": true
    }
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        # Get processing parameters
        params = request.get_json() or {}
        
        # Get original image path
        session_dir = Path('sessions') / session_id
        original_path = session_dir / 'originals' / f'{page_id}.jpg'
        
        if not original_path.exists():
            return jsonify({"error": "Page not found"}), 404
        
        # Process image
        processed_image, metadata = image_processor.process_document(
            original_path, 
            params
        )
        
        # Save processed image
        processed_dir = session_dir / 'processed'
        processed_dir.mkdir(exist_ok=True)
        processed_path = processed_dir / f'{page_id}.jpg'
        
        cv2.imwrite(str(processed_path), processed_image)
        
        # Create thumbnail
        thumbnail = image_processor.create_thumbnail(processed_image)
        thumbnail_dir = session_dir / 'thumbnails'
        thumbnail_dir.mkdir(exist_ok=True)
        thumbnail_path = thumbnail_dir / f'{page_id}.jpg'
        cv2.imwrite(str(thumbnail_path), thumbnail)
        
        # Update metadata
        image_storage.update_page_metadata(session_id, page_id, {
            "processed": True,
            "processing_params": params,
            "processing_metadata": metadata
        })
        
        return jsonify({
            "success": True,
            "page_id": page_id,
            "processed_url": f"/api/process/{session_id}/{page_id}/preview",
            "metadata": metadata
        })
        
    except Exception as e:
        logger.error(f"Page processing error: {e}")
        return jsonify({"error": str(e)}), 500


@processing_bp.route('/<session_id>/<page_id>/preview', methods=['GET'])
def get_processed_preview(session_id, page_id):
    """Get processed image preview."""
    try:
        session_dir = Path('sessions') / session_id
        processed_path = session_dir / 'processed' / f'{page_id}.jpg'
        
        if processed_path.exists():
            return send_file(processed_path, mimetype='image/jpeg')
        else:
            # Fallback to original
            original_path = session_dir / 'originals' / f'{page_id}.jpg'
            if original_path.exists():
                return send_file(original_path, mimetype='image/jpeg')
            else:
                return jsonify({"error": "Image not found"}), 404
                
    except Exception as e:
        logger.error(f"Preview retrieval error: {e}")
        return jsonify({"error": str(e)}), 500


@processing_bp.route('/<session_id>/batch', methods=['POST'])
def batch_process(session_id):
    """
    Process multiple pages with the same parameters.
    
    Request body:
    {
        "page_ids": ["page_1", "page_2"],
        "processing_params": { ... }
    }
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        data = request.get_json()
        page_ids = data.get('page_ids', [])
        params = data.get('processing_params', {})
        
        results = []
        errors = []
        
        for page_id in page_ids:
            try:
                # Get original image path
                session_dir = Path('sessions') / session_id
                original_path = session_dir / 'originals' / f'{page_id}.jpg'
                
                if not original_path.exists():
                    errors.append({"page_id": page_id, "error": "Not found"})
                    continue
                
                # Process image
                processed_image, metadata = image_processor.process_document(
                    original_path, 
                    params
                )
                
                # Save processed image
                processed_dir = session_dir / 'processed'
                processed_dir.mkdir(exist_ok=True)
                processed_path = processed_dir / f'{page_id}.jpg'
                cv2.imwrite(str(processed_path), processed_image)
                
                # Create thumbnail
                thumbnail = image_processor.create_thumbnail(processed_image)
                thumbnail_dir = session_dir / 'thumbnails'
                thumbnail_dir.mkdir(exist_ok=True)
                thumbnail_path = thumbnail_dir / f'{page_id}.jpg'
                cv2.imwrite(str(thumbnail_path), thumbnail)
                
                # Update metadata
                image_storage.update_page_metadata(session_id, page_id, {
                    "processed": True,
                    "processing_params": params,
                    "processing_metadata": metadata
                })
                
                results.append({
                    "page_id": page_id,
                    "success": True,
                    "metadata": metadata
                })
                
            except Exception as e:
                logger.error(f"Batch processing error for {page_id}: {e}")
                errors.append({"page_id": page_id, "error": str(e)})
        
        return jsonify({
            "success": True,
            "processed_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors
        })
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({"error": str(e)}), 500


@processing_bp.route('/<session_id>/reorder', methods=['POST'])
def reorder_pages(session_id):
    """
    Reorder pages in a session.
    
    Request body:
    {
        "page_order": ["page_3", "page_1", "page_2"]
    }
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        data = request.get_json()
        page_order = data.get('page_order', [])
        
        # Update page order in metadata
        image_storage.update_page_order(session_id, page_order)
        
        return jsonify({
            "success": True,
            "page_order": page_order
        })
        
    except Exception as e:
        logger.error(f"Page reordering error: {e}")
        return jsonify({"error": str(e)}), 500
