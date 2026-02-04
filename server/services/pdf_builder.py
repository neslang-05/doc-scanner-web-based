"""
PDF Builder Service
Handles PDF assembly from processed document images with configurable DPI and compression.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from pathlib import Path
from typing import List, Optional, Dict, Any
import io
import logging

logger = logging.getLogger(__name__)


class PDFBuilder:
    """
    Service for creating PDF documents from scanned images.
    Supports variable DPI, compression, and page ordering.
    """
    
    def __init__(self):
        """Initialize PDF builder"""
        self.default_dpi = 300
        self.default_page_size = A4
    
    def build_pdf(
        self,
        image_paths: List[Path],
        output_path: Path,
        dpi: int = 300,
        compression: str = 'medium',
        page_size: tuple = None
    ) -> Dict[str, Any]:
        """
        Create a PDF from a list of images.
        
        Args:
            image_paths: List of paths to images in order
            output_path: Path where PDF should be saved
            dpi: Target DPI for images (150, 200, 300)
            compression: Compression level ('low', 'medium', 'high')
            page_size: Page size tuple (width, height) in points, None for auto
            
        Returns:
            Dictionary with success status and file info
        """
        try:
            if not image_paths:
                raise ValueError("No images provided")
            
            # Set compression quality
            quality_map = {
                'low': 95,
                'medium': 85,
                'high': 75
            }
            quality = quality_map.get(compression, 85)
            
            # Create PDF
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(str(output_path), pagesize=page_size or self.default_page_size)
            
            total_size = 0
            page_count = 0
            
            for img_path in image_paths:
                if not img_path.exists():
                    logger.warning(f"Image not found: {img_path}")
                    continue
                
                try:
                    # Open and process image
                    img = Image.open(img_path)
                    
                    # Convert to RGB if necessary
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Compress if needed
                    if quality < 95:
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='JPEG', quality=quality, optimize=True)
                        img_buffer.seek(0)
                        img = Image.open(img_buffer)
                    
                    # Calculate page size based on image aspect ratio
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                    
                    if page_size:
                        page_width, page_height = page_size
                    else:
                        # Use A4 by default
                        page_width, page_height = A4
                    
                    # Fit image to page while maintaining aspect ratio
                    if img_width / page_width > img_height / page_height:
                        # Image is wider
                        draw_width = page_width
                        draw_height = page_width / aspect_ratio
                    else:
                        # Image is taller
                        draw_height = page_height
                        draw_width = page_height * aspect_ratio
                    
                    # Center image on page
                    x = (page_width - draw_width) / 2
                    y = (page_height - draw_height) / 2
                    
                    # Set page size
                    c.setPageSize((page_width, page_height))
                    
                    # Draw image
                    c.drawImage(
                        ImageReader(img),
                        x, y,
                        width=draw_width,
                        height=draw_height,
                        preserveAspectRatio=True
                    )
                    
                    c.showPage()
                    page_count += 1
                    total_size += img_path.stat().st_size
                    
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {e}")
                    continue
            
            # Save PDF
            c.save()
            
            # Get file size
            file_size = output_path.stat().st_size
            
            return {
                "success": True,
                "output_path": str(output_path),
                "page_count": page_count,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "dpi": dpi,
                "compression": compression
            }
            
        except Exception as e:
            logger.error(f"PDF building error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def build_pdf_with_ocr(
        self,
        image_paths: List[Path],
        ocr_data: List[str],
        output_path: Path,
        dpi: int = 300,
        compression: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Create a searchable PDF with OCR text layer.
        
        Args:
            image_paths: List of paths to images
            ocr_data: List of OCR text for each page
            output_path: Output PDF path
            dpi: Target DPI
            compression: Compression level
            
        Returns:
            Dictionary with success status
        """
        try:
            # First create regular PDF
            result = self.build_pdf(image_paths, output_path, dpi, compression)
            
            if not result['success']:
                return result
            
            # TODO: Add OCR text layer using reportlab's text capabilities
            # This requires positioning OCR text beneath the image
            # For now, return the basic PDF
            
            result['ocr_enabled'] = False
            result['note'] = 'OCR text layer not yet implemented'
            
            return result
            
        except Exception as e:
            logger.error(f"PDF with OCR building error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> Dict[str, Any]:
        """
        Merge multiple PDF files into one.
        
        Args:
            pdf_paths: List of paths to PDF files
            output_path: Output merged PDF path
            
        Returns:
            Dictionary with success status
        """
        try:
            from PyPDF2 import PdfMerger
            
            merger = PdfMerger()
            
            for pdf_path in pdf_paths:
                if pdf_path.exists():
                    merger.append(str(pdf_path))
            
            merger.write(str(output_path))
            merger.close()
            
            file_size = output_path.stat().st_size
            
            return {
                "success": True,
                "output_path": str(output_path),
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "merged_count": len(pdf_paths)
            }
            
        except Exception as e:
            logger.error(f"PDF merging error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
