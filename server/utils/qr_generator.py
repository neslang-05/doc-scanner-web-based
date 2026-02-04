"""
QR Code Generation Utility
Creates QR codes for mobile device pairing with sessions.
"""

import qrcode
from io import BytesIO
import base64
from typing import Tuple


def generate_pairing_qr(session_id: str, server_url: str) -> Tuple[bytes, str]:
    """
    Generate a QR code for mobile camera pairing.
    
    Args:
        session_id: Unique session identifier
        server_url: Base URL of the server (e.g., "http://192.168.1.100:5000")
        
    Returns:
        Tuple of (PNG image bytes, base64 data URI string)
    """
    # Construct mobile camera URL
    mobile_url = f"{server_url}/mobile/camera?session={session_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,  # Auto-adjust size
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to PNG bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()
    
    # Create base64 data URI
    base64_str = base64.b64encode(png_bytes).decode('utf-8')
    data_uri = f"data:image/png;base64,{base64_str}"
    
    return png_bytes, data_uri


def generate_qr_svg(session_id: str, server_url: str) -> str:
    """
    Generate a QR code as SVG for better scaling.
    
    Args:
        session_id: Unique session identifier
        server_url: Base URL of the server
        
    Returns:
        SVG string
    """
    import qrcode.image.svg
    
    mobile_url = f"{server_url}/mobile/camera?session={session_id}"
    
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(image_factory=factory)
    qr.add_data(mobile_url)
    qr.make(fit=True)
    
    img = qr.make_image()
    
    buffer = BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode('utf-8')
