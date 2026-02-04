"""
Image Processing Service
Handles document edge detection, perspective correction, and image enhancement.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Service for processing scanned document images.
    All processing is non-destructive - originals are preserved.
    """
    
    def __init__(self):
        """Initialize image processor"""
        pass
    
    def detect_document_edges(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Find document boundaries using contour detection.
        Returns the largest quadrilateral contour (4 corners).
        
        Args:
            image: Input image as numpy array
            
        Returns:
            4x2 array of corner coordinates, or None if no document detected
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edged = cv2.Canny(blurred, 75, 200)
            
            # Find contours
            contours, _ = cv2.findContours(
                edged.copy(), 
                cv2.RETR_LIST, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Sort by area (largest first)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            
            # Find the largest quadrilateral
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                
                if len(approx) == 4:
                    return approx.reshape(4, 2)
            
            # Fallback: return image bounds
            h, w = image.shape[:2]
            return np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Edge detection error: {e}")
            return None
    
    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Order points in clockwise order: top-left, top-right, bottom-right, bottom-left.
        
        Args:
            pts: 4x2 array of corner coordinates
            
        Returns:
            Ordered 4x2 array
        """
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Sum: top-left has smallest, bottom-right has largest
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Diff: top-right has smallest, bottom-left has largest
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def correct_perspective(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """
        Apply perspective transform to flatten document.
        
        Args:
            image: Input image
            corners: 4 corner coordinates
            
        Returns:
            Warped image with corrected perspective
        """
        try:
            # Order corners
            rect = self.order_points(corners)
            (tl, tr, br, bl) = rect
            
            # Compute target dimensions
            width_a = np.linalg.norm(br - bl)
            width_b = np.linalg.norm(tr - tl)
            max_width = int(max(width_a, width_b))
            
            height_a = np.linalg.norm(tr - br)
            height_b = np.linalg.norm(tl - bl)
            max_height = int(max(height_a, height_b))
            
            # Define destination points
            dst = np.array([
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1]
            ], dtype=np.float32)
            
            # Apply perspective transform
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, M, (max_width, max_height))
            
            return warped
            
        except Exception as e:
            logger.error(f"Perspective correction error: {e}")
            return image
    
    def normalize_lighting(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize lighting across the image using CLAHE.
        
        Args:
            image: Input image
            
        Returns:
            Image with normalized lighting
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Lighting normalization error: {e}")
            return image
    
    def apply_color_filter(self, image: np.ndarray, mode: str) -> np.ndarray:
        """
        Apply color filter to image.
        
        Args:
            image: Input image
            mode: Filter mode - 'color', 'grayscale', or 'bw' (black & white)
            
        Returns:
            Filtered image
        """
        try:
            if mode == 'grayscale':
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            elif mode == 'bw':
                # Convert to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Apply adaptive thresholding for better B&W conversion
                bw = cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11, 2
                )
                
                return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
            
            else:  # 'color' or default
                return image
                
        except Exception as e:
            logger.error(f"Color filter error: {e}")
            return image
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        General image enhancement (sharpness, contrast).
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        try:
            # Increase sharpness
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            sharpened = cv2.filter2D(image, -1, kernel)
            
            # Slight contrast enhancement
            alpha = 1.1  # Contrast control
            beta = 10    # Brightness control
            enhanced = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return image
    
    def process_document(
        self, 
        image_path: Path,
        params: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a document image with specified parameters.
        
        Args:
            image_path: Path to original image
            params: Processing parameters dictionary
                - detect_edges: bool
                - correct_perspective: bool
                - normalize_lighting: bool
                - enhance_mode: 'color', 'grayscale', or 'bw'
                - enhance_image: bool
                
        Returns:
            Tuple of (processed_image, metadata)
        """
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            metadata = {
                "original_size": image.shape[:2],
                "steps_applied": []
            }
            
            # Edge detection and perspective correction
            if params.get('detect_edges', False):
                corners = self.detect_document_edges(image)
                
                if corners is not None and params.get('correct_perspective', False):
                    image = self.correct_perspective(image, corners)
                    metadata["steps_applied"].append("perspective_correction")
                    metadata["corners"] = corners.tolist()
                else:
                    metadata["steps_applied"].append("edge_detection_failed")
            
            # Lighting normalization
            if params.get('normalize_lighting', False):
                image = self.normalize_lighting(image)
                metadata["steps_applied"].append("lighting_normalization")
            
            # Color filter
            enhance_mode = params.get('enhance_mode', 'color')
            if enhance_mode != 'color':
                image = self.apply_color_filter(image, enhance_mode)
                metadata["steps_applied"].append(f"color_filter_{enhance_mode}")
            
            # General enhancement
            if params.get('enhance_image', False):
                image = self.enhance_image(image)
                metadata["steps_applied"].append("image_enhancement")
            
            metadata["final_size"] = image.shape[:2]
            
            return image, metadata
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            # Return original if processing fails
            image = cv2.imread(str(image_path))
            return image, {"error": str(e)}
    
    def create_thumbnail(self, image: np.ndarray, max_size: int = 300) -> np.ndarray:
        """
        Create thumbnail of image.
        
        Args:
            image: Input image
            max_size: Maximum dimension (width or height)
            
        Returns:
            Thumbnail image
        """
        try:
            h, w = image.shape[:2]
            
            if max(h, w) <= max_size:
                return image
            
            # Calculate scaling factor
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize
            thumbnail = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return thumbnail
            
        except Exception as e:
            logger.error(f"Thumbnail creation error: {e}")
            return image
