"""
Export Routes
API endpoints for PDF generation, OCR, and file downloads.
"""

from flask import Blueprint, request, jsonify, send_file
from server.services.session_manager import SessionManager
from server.services.image_storage import ImageStorage
from server.services.pdf_builder import PDFBuilder
from server.services.ocr_service import OCRService
from pathlib import Path
import secrets
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/api/export')
session_manager = SessionManager()
image_storage = ImageStorage()
pdf_builder = PDFBuilder()
ocr_service = OCRService()

# Store temporary download tokens
download_tokens = {}


@export_bp.route('/<session_id>/pdf', methods=['POST'])
def export_pdf(session_id):
    """
    Export captured pages as PDF.
    
    Request body:
    {
        "page_ids": ["page_1", "page_2"],  // Optional, if not provided uses all pages
        "dpi": 300,
        "compression": "medium",  // "low", "medium", "high"
        "include_ocr": false,
        "use_processed": true  // Use processed images if available
    }
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        data = request.get_json() or {}
        
        # Get page IDs
        page_ids = data.get('page_ids')
        if not page_ids:
            # Get all pages in order
            page_ids = image_storage.get_page_order(session_id)
            if not page_ids:
                # Fallback: get all pages from originals directory
                session_dir = Path('sessions') / session_id / 'originals'
                if session_dir.exists():
                    page_ids = [f.stem for f in session_dir.glob('*.jpg') 
                               if not f.stem.endswith('_metadata')]
                else:
                    return jsonify({"error": "No pages found"}), 404
        
        # Get processing preferences
        dpi = data.get('dpi', 300)
        compression = data.get('compression', 'medium')
        include_ocr = data.get('include_ocr', False)
        use_processed = data.get('use_processed', True)
        
        # Collect image paths
        session_path = Path('sessions') / session_id
        image_paths = []
        
        for page_id in page_ids:
            # Try processed first if requested
            if use_processed:
                processed_path = session_path / 'processed' / f'{page_id}.jpg'
                if processed_path.exists():
                    image_paths.append(processed_path)
                    continue
            
            # Fallback to original
            original_path = session_path / 'originals' / f'{page_id}.jpg'
            if original_path.exists():
                image_paths.append(original_path)
        
        if not image_paths:
            return jsonify({"error": "No valid images found"}), 404
        
        # Generate PDF filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f'document_{timestamp}.pdf'
        export_dir = session_path / 'exports'
        export_dir.mkdir(exist_ok=True)
        pdf_path = export_dir / pdf_filename
        
        # Build PDF
        if include_ocr and ocr_service.is_tesseract_available():
            # Extract OCR text
            ocr_texts = ocr_service.batch_extract_text(image_paths)
            result = pdf_builder.build_pdf_with_ocr(
                image_paths, ocr_texts, pdf_path, dpi, compression
            )
        else:
            result = pdf_builder.build_pdf(
                image_paths, pdf_path, dpi, compression
            )
        
        if not result['success']:
            return jsonify({"error": result.get('error', 'PDF generation failed')}), 500
        
        # Create temporary download token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        download_tokens[token] = {
            'file_path': str(pdf_path),
            'filename': pdf_filename,
            'expires_at': expires_at,
            'session_id': session_id
        }
        
        return jsonify({
            "success": True,
            "download_token": token,
            "download_url": f"/api/export/download/{token}",
            "filename": pdf_filename,
            "file_size_mb": result['file_size_mb'],
            "page_count": result['page_count'],
            "expires_at": expires_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({"error": str(e)}), 500


@export_bp.route('/download/<token>', methods=['GET'])
def download_file(token):
    """Download a file using a temporary token."""
    try:
        # Check if token exists
        if token not in download_tokens:
            return jsonify({"error": "Invalid or expired download link"}), 404
        
        token_data = download_tokens[token]
        
        # Check if expired
        if datetime.now() > token_data['expires_at']:
            del download_tokens[token]
            return jsonify({"error": "Download link has expired"}), 410
        
        file_path = Path(token_data['file_path'])
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=token_data['filename'],
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": str(e)}), 500


@export_bp.route('/<session_id>/ocr/<page_id>', methods=['POST'])
def extract_text_from_page(session_id, page_id):
    """
    Extract text from a specific page using OCR.
    
    Request body:
    {
        "language": "eng",  // Language code
        "async": false  // If true, returns job_id for status checking
    }
    """
    try:
        # Validate session
        if not session_manager.validate_session(session_id):
            return jsonify({"error": "Invalid or expired session"}), 404
        
        # Check if Tesseract is available
        if not ocr_service.is_tesseract_available():
            return jsonify({
                "error": "OCR not available. Please install Tesseract OCR."
            }), 503
        
        data = request.get_json() or {}
        language = data.get('language', 'eng')
        is_async = data.get('async', False)
        
        # Get image path (prefer processed)
        session_path = Path('sessions') / session_id
        image_path = session_path / 'processed' / f'{page_id}.jpg'
        
        if not image_path.exists():
            image_path = session_path / 'originals' / f'{page_id}.jpg'
        
        if not image_path.exists():
            return jsonify({"error": "Page not found"}), 404
        
        if is_async:
            # Asynchronous OCR
            job_id = f"{session_id}_{page_id}_{secrets.token_hex(8)}"
            ocr_service.extract_text_async(job_id, image_path, language)
            
            return jsonify({
                "success": True,
                "job_id": job_id,
                "status_url": f"/api/export/ocr/status/{job_id}"
            })
        else:
            # Synchronous OCR
            text = ocr_service.extract_text(image_path, language)
            
            if text is None:
                return jsonify({"error": "OCR extraction failed"}), 500
            
            return jsonify({
                "success": True,
                "page_id": page_id,
                "text": text,
                "language": language
            })
        
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        return jsonify({"error": str(e)}), 500


@export_bp.route('/ocr/status/<job_id>', methods=['GET'])
def get_ocr_status(job_id):
    """Get the status of an async OCR job."""
    try:
        result = ocr_service.get_ocr_result(job_id)
        
        if result is None:
            return jsonify({"error": "Job not found"}), 404
        
        return jsonify({
            "job_id": job_id,
            "status": result['status'],
            "text": result.get('text'),
            "error": result.get('error')
        })
        
    except Exception as e:
        logger.error(f"OCR status error: {e}")
        return jsonify({"error": str(e)}), 500


@export_bp.route('/<session_id>/share', methods=['POST'])
def create_share_link(session_id):
    """
    Create a temporary sharing link for a PDF.
    
    Request body:
    {
        "pdf_token": "existing_download_token",
        "expires_hours": 24
    }
    """
    try:
        data = request.get_json() or {}
        pdf_token = data.get('pdf_token')
        expires_hours = data.get('expires_hours', 24)
        
        if not pdf_token or pdf_token not in download_tokens:
            return jsonify({"error": "Invalid PDF token"}), 400
        
        # Create new share token with extended expiration
        share_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # Copy token data
        download_tokens[share_token] = {
            **download_tokens[pdf_token],
            'expires_at': expires_at,
            'is_share_link': True
        }
        
        return jsonify({
            "success": True,
            "share_token": share_token,
            "share_url": f"/api/export/download/{share_token}",
            "expires_at": expires_at.isoformat(),
            "expires_hours": expires_hours
        })
        
    except Exception as e:
        logger.error(f"Share link creation error: {e}")
        return jsonify({"error": str(e)}), 500


def cleanup_expired_tokens():
    """Remove expired download tokens."""
    now = datetime.now()
    expired = [token for token, data in download_tokens.items() 
               if data['expires_at'] < now]
    
    for token in expired:
        del download_tokens[token]
    
    logger.info(f"Cleaned up {len(expired)} expired download tokens")
