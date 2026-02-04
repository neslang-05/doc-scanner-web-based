"""
Session Management Service
Handles session creation, validation, expiration, and state management.
"""

import os
import json
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List


class SessionManager:
    """
    Manages scanning sessions with automatic expiration and cleanup.
    Each session represents one scanning workflow from connection to export.
    """
    
    def __init__(self, sessions_dir: str = "sessions", session_duration_hours: int = 4):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Base directory for session storage
            session_duration_hours: Session lifetime before expiration
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.session_duration_hours = session_duration_hours
        
    def create_session(self) -> Dict:
        """
        Create a new scanning session with unique ID.
        
        Returns:
            Dict with session_id, created_at, expires_at
        """
        session_id = self._generate_session_id()
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=self.session_duration_hours)
        
        # Create session directory structure
        session_path = self.sessions_dir / session_id
        session_path.mkdir(exist_ok=True)
        (session_path / "originals").mkdir(exist_ok=True)
        (session_path / "processed").mkdir(exist_ok=True)
        (session_path / "exports").mkdir(exist_ok=True)
        
        # Initialize metadata
        metadata = {
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": created_at.isoformat(),
            "camera_connected": False,
            "pages": [],
            "page_count": 0
        }
        
        self._save_metadata(session_id, metadata)
        
        return {
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat()
        }
    
    def validate_session(self, session_id: str) -> bool:
        """
        Check if a session exists and is not expired.
        
        Args:
            session_id: Session identifier to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        if not self._is_valid_session_id(session_id):
            return False
            
        session_path = self.sessions_dir / session_id
        if not session_path.exists():
            return False
            
        metadata = self._load_metadata(session_id)
        if not metadata:
            return False
            
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if datetime.now() > expires_at:
            return False
            
        return True
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """
        Get current session status and statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with session status or None if invalid
        """
        if not self.validate_session(session_id):
            return None
            
        metadata = self._load_metadata(session_id)
        if not metadata:
            return None
            
        return {
            "session_id": session_id,
            "camera_connected": metadata.get("camera_connected", False),
            "page_count": metadata.get("page_count", 0),
            "last_activity": metadata.get("last_activity"),
            "expires_at": metadata.get("expires_at")
        }
    
    def update_camera_status(self, session_id: str, connected: bool) -> bool:
        """
        Update camera connection status for a session.
        
        Args:
            session_id: Session identifier
            connected: True if camera is connected
            
        Returns:
            True if updated successfully
        """
        if not self.validate_session(session_id):
            return False
            
        metadata = self._load_metadata(session_id)
        if not metadata:
            return False
            
        metadata["camera_connected"] = connected
        metadata["last_activity"] = datetime.now().isoformat()
        
        return self._save_metadata(session_id, metadata)
    
    def add_page(self, session_id: str, page_id: str, original_path: str) -> bool:
        """
        Add a captured page to the session.
        
        Args:
            session_id: Session identifier
            page_id: Unique page identifier
            original_path: Path to original image file
            
        Returns:
            True if page added successfully
        """
        if not self.validate_session(session_id):
            return False
            
        metadata = self._load_metadata(session_id)
        if not metadata:
            return False
            
        page_entry = {
            "page_id": page_id,
            "captured_at": datetime.now().isoformat(),
            "original_path": original_path,
            "processing_params": {}
        }
        
        metadata["pages"].append(page_entry)
        metadata["page_count"] = len(metadata["pages"])
        metadata["last_activity"] = datetime.now().isoformat()
        
        return self._save_metadata(session_id, metadata)
    
    def get_pages(self, session_id: str) -> List[Dict]:
        """
        Get all pages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of page metadata dictionaries
        """
        if not self.validate_session(session_id):
            return []
            
        metadata = self._load_metadata(session_id)
        if not metadata:
            return []
            
        return metadata.get("pages", [])
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions and their files.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned = 0
        current_time = datetime.now()
        
        for session_path in self.sessions_dir.iterdir():
            if not session_path.is_dir():
                continue
                
            session_id = session_path.name
            if not self._is_valid_session_id(session_id):
                continue
                
            metadata = self._load_metadata(session_id)
            if not metadata:
                continue
                
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if current_time > expires_at:
                try:
                    shutil.rmtree(session_path)
                    cleaned += 1
                except Exception as e:
                    print(f"Error cleaning session {session_id}: {e}")
                    
        return cleaned
    
    def delete_session(self, session_id: str) -> bool:
        """
        Manually delete a session and all its data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        if not self._is_valid_session_id(session_id):
            return False
            
        session_path = self.sessions_dir / session_id
        if not session_path.exists():
            return False
            
        try:
            shutil.rmtree(session_path)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        return uuid.uuid4().hex[:12]
    
    def _is_valid_session_id(self, session_id: str) -> bool:
        """Validate session ID format to prevent path traversal."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', session_id))
    
    def _get_metadata_path(self, session_id: str) -> Path:
        """Get path to session metadata file."""
        return self.sessions_dir / session_id / "metadata.json"
    
    def _load_metadata(self, session_id: str) -> Optional[Dict]:
        """Load session metadata from disk."""
        metadata_path = self._get_metadata_path(session_id)
        if not metadata_path.exists():
            return None
            
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata for {session_id}: {e}")
            return None
    
    def _save_metadata(self, session_id: str, metadata: Dict) -> bool:
        """Save session metadata to disk."""
        metadata_path = self._get_metadata_path(session_id)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metadata for {session_id}: {e}")
            return False
