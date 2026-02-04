"""
Image Storage Service
Handles storage, retrieval, and management of captured document images.
"""

import os
import base64
from pathlib import Path
from PIL import Image
import io
from typing import Dict, Optional
from datetime import datetime


class ImageStorage:
    """
    Manages file storage for original images, thumbnails, and processed images.
    Ensures non-destructive workflow by keeping originals separate.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the image storage service.
        
        Args:
            sessions_dir: Base directory for session storage
        """
        self.sessions_dir = Path(sessions_dir)
        self.thumbnail_size = (300, 400)  # Width x Height for thumbnails
        self.thumbnail_quality = 85
        
    def store_original(self, session_id: str, page_id: str, 
                      image_data_base64: str, image_format: str = 'jpeg',
                      metadata: Dict = None) -> Dict:
        """
        Store an original captured image.
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            image_data_base64: Base64 encoded image data
            image_format: Image format (jpeg, png)
            metadata: Optional metadata to store with image
            
        Returns:
            Dict with success status, original_path, and captured_at timestamp
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data_base64)
            
            # Validate image can be opened
            image = Image.open(io.BytesIO(image_bytes))
            
            # Construct file path
            session_path = self.sessions_dir / session_id / "originals"
            session_path.mkdir(parents=True, exist_ok=True)
            
            file_extension = 'jpg' if image_format == 'jpeg' else image_format
            original_path = session_path / f"{page_id}.{file_extension}"
            
            # Save image
            image.save(original_path, format='JPEG' if image_format == 'jpeg' else image_format.upper(),
                      quality=95, optimize=True)
            
            # Store metadata if provided
            if metadata:
                metadata_path = session_path / f"{page_id}_metadata.json"
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            captured_at = datetime.now().isoformat()
            
            return {
                "success": True,
                "original_path": str(original_path),
                "captured_at": captured_at,
                "width": image.width,
                "height": image.height
            }
            
        except Exception as e:
            print(f"Error storing original image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_thumbnail(self, session_id: str, page_id: str) -> Dict:
        """
        Generate a thumbnail from the original image.
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            
        Returns:
            Dict with success status and thumbnail_path
        """
        try:
            # Get original image path
            original_path = self.get_original_path(session_id, page_id)
            if not original_path or not Path(original_path).exists():
                return {"success": False, "error": "Original image not found"}
            
            # Load original image
            image = Image.open(original_path)
            
            # Create thumbnail
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_dir = self.sessions_dir / session_id / "processed"
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"{page_id}_thumb.jpg"
            image.save(thumbnail_path, format='JPEG', 
                      quality=self.thumbnail_quality, optimize=True)
            
            return {
                "success": True,
                "thumbnail_path": str(thumbnail_path)
            }
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_original_path(self, session_id: str, page_id: str) -> Optional[str]:
        """
        Get the file path of an original image.
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            
        Returns:
            File path string or None if not found
        """
        # Try different extensions
        for ext in ['jpg', 'jpeg', 'png']:
            path = self.sessions_dir / session_id / "originals" / f"{page_id}.{ext}"
            if path.exists():
                return str(path)
        return None
    
    def get_thumbnail_path(self, session_id: str, page_id: str) -> Optional[str]:
        """
        Get the file path of a thumbnail image.
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            
        Returns:
            File path string or None if not found
        """
        path = self.sessions_dir / session_id / "processed" / f"{page_id}_thumb.jpg"
        if path.exists():
            return str(path)
        return None
    
    def delete_page(self, session_id: str, page_id: str) -> bool:
        """
        Delete all files associated with a page (original, thumbnail, processed).
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            deleted_any = False
            
            # Delete original
            original_path = self.get_original_path(session_id, page_id)
            if original_path and Path(original_path).exists():
                Path(original_path).unlink()
                deleted_any = True
            
            # Delete thumbnail
            thumbnail_path = self.get_thumbnail_path(session_id, page_id)
            if thumbnail_path and Path(thumbnail_path).exists():
                Path(thumbnail_path).unlink()
                deleted_any = True
            
            # Delete metadata
            metadata_path = self.sessions_dir / session_id / "originals" / f"{page_id}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            return deleted_any
            
        except Exception as e:
            print(f"Error deleting page: {e}")
            return False
    
    def get_image_as_base64(self, file_path: str) -> Optional[str]:
        """
        Load an image file and convert to base64.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Base64 encoded string or None
        """
        try:
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
                return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return None
    
    def update_page_metadata(self, session_id: str, page_id: str, metadata: Dict) -> bool:
        """
        Update or add metadata for a page.
        
        Args:
            session_id: Session identifier
            page_id: Page identifier
            metadata: Metadata dictionary to merge/update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            metadata_path = self.sessions_dir / session_id / "originals" / f"{page_id}_metadata.json"
            
            # Load existing metadata if it exists
            existing_metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    existing_metadata = json.load(f)
            
            # Merge new metadata
            existing_metadata.update(metadata)
            existing_metadata['updated_at'] = datetime.now().isoformat()
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(existing_metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error updating page metadata: {e}")
            return False
    
    def update_page_order(self, session_id: str, page_order: list) -> bool:
        """
        Update the order of pages in a session.
        
        Args:
            session_id: Session identifier
            page_order: List of page IDs in desired order
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            order_path = self.sessions_dir / session_id / "page_order.json"
            
            with open(order_path, 'w') as f:
                json.dump({
                    "page_order": page_order,
                    "updated_at": datetime.now().isoformat()
                }, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error updating page order: {e}")
            return False
    
    def get_page_order(self, session_id: str) -> Optional[list]:
        """
        Get the order of pages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of page IDs in order, or None if not found
        """
        try:
            import json
            
            order_path = self.sessions_dir / session_id / "page_order.json"
            
            if order_path.exists():
                with open(order_path, 'r') as f:
                    data = json.load(f)
                    return data.get('page_order', [])
            
            return None
            
        except Exception as e:
            print(f"Error getting page order: {e}")
            return None
