"""
OCR Service
Handles optical character recognition using Tesseract.
"""

import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, List
import logging
import threading
import queue

logger = logging.getLogger(__name__)


class OCRService:
    """
    Service for performing OCR on document images.
    Supports asynchronous processing for non-blocking operation.
    """
    
    def __init__(self):
        """Initialize OCR service"""
        self.ocr_queue = queue.Queue()
        self.results = {}
        self.worker_thread = None
    
    def extract_text(self, image_path: Path, language: str = 'eng') -> Optional[str]:
        """
        Extract text from an image synchronously.
        
        Args:
            image_path: Path to image file
            language: Language code for OCR (default: 'eng')
            
        Returns:
            Extracted text or None if failed
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=language)
            
            return text.strip()
            
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not installed. Please install Tesseract OCR.")
            return None
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return None
    
    def extract_text_with_boxes(
        self, 
        image_path: Path, 
        language: str = 'eng'
    ) -> Optional[List[Dict]]:
        """
        Extract text with bounding box information.
        
        Args:
            image_path: Path to image file
            language: Language code for OCR
            
        Returns:
            List of dictionaries with text and box coordinates
        """
        try:
            image = Image.open(image_path)
            
            # Get OCR data with bounding boxes
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Process results
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:  # Only include confident results
                    results.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"OCR with boxes error: {e}")
            return None
    
    def extract_text_async(
        self, 
        job_id: str,
        image_path: Path, 
        language: str = 'eng',
        callback: callable = None
    ):
        """
        Extract text asynchronously.
        
        Args:
            job_id: Unique identifier for this job
            image_path: Path to image file
            language: Language code for OCR
            callback: Optional callback function called when complete
        """
        def worker():
            try:
                text = self.extract_text(image_path, language)
                self.results[job_id] = {
                    'status': 'completed',
                    'text': text,
                    'error': None
                }
                
                if callback:
                    callback(job_id, text)
                    
            except Exception as e:
                logger.error(f"Async OCR error: {e}")
                self.results[job_id] = {
                    'status': 'failed',
                    'text': None,
                    'error': str(e)
                }
        
        # Mark as in progress
        self.results[job_id] = {
            'status': 'in_progress',
            'text': None,
            'error': None
        }
        
        # Start worker thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def get_ocr_result(self, job_id: str) -> Optional[Dict]:
        """
        Get the result of an async OCR job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary with status, text, and error
        """
        return self.results.get(job_id)
    
    def batch_extract_text(
        self, 
        image_paths: List[Path], 
        language: str = 'eng'
    ) -> List[str]:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of image paths
            language: Language code for OCR
            
        Returns:
            List of extracted texts (in same order as input)
        """
        results = []
        
        for image_path in image_paths:
            text = self.extract_text(image_path, language)
            results.append(text or "")
        
        return results
    
    def is_tesseract_available(self) -> bool:
        """
        Check if Tesseract is installed and available.
        
        Returns:
            True if Tesseract is available
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available OCR languages.
        
        Returns:
            List of language codes
        """
        try:
            languages = pytesseract.get_languages()
            return languages
        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return ['eng']  # Default to English
