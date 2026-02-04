"""
Test Script for Web Document Scanner
Validates core functionality and dependencies.
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.9 or higher."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        ('flask', 'Flask'),
        ('flask_cors', 'flask-cors'),
        ('flask_sock', 'flask-sock'),
        ('qrcode', 'qrcode'),
        ('PIL', 'Pillow'),
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
    ]
    
    all_installed = True
    
    for module_name, package_name in required_packages:
        try:
            importlib.import_module(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} (not installed)")
            all_installed = False
    
    return all_installed


def check_directory_structure():
    """Check if required directories exist."""
    required_dirs = [
        'server/routes',
        'server/services',
        'server/utils',
        'static/desktop',
        'static/mobile',
        'sessions'
    ]
    
    all_exist = True
    base_path = Path('.')
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ (missing)")
            all_exist = False
    
    return all_exist


def check_critical_files():
    """Check if critical files exist."""
    critical_files = [
        'server/app.py',
        'server/routes/session.py',
        'server/routes/streaming.py',
        'server/routes/capture.py',
        'server/services/session_manager.py',
        'server/services/image_storage.py',
        'static/desktop/index.html',
        'static/desktop/scanner.js',
        'static/mobile/camera.html',
        'static/mobile/camera.js',
        'requirements.txt'
    ]
    
    all_exist = True
    
    for file_path in critical_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False
    
    return all_exist


def test_session_manager():
    """Test basic session manager functionality."""
    try:
        from server.services.session_manager import SessionManager
        
        manager = SessionManager()
        session = manager.create_session()
        
        if 'session_id' in session:
            print(f"✓ Session Manager (created session: {session['session_id'][:8]}...)")
            
            # Clean up test session
            manager.delete_session(session['session_id'])
            return True
        else:
            print("✗ Session Manager (failed to create session)")
            return False
            
    except Exception as e:
        print(f"✗ Session Manager ({str(e)})")
        return False


def test_image_storage():
    """Test image storage functionality."""
    try:
        from server.services.image_storage import ImageStorage
        
        storage = ImageStorage()
        print("✓ Image Storage")
        return True
        
    except Exception as e:
        print(f"✗ Image Storage ({str(e)})")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Web Document Scanner - System Check")
    print("=" * 60)
    print()
    
    print("1. Checking Python Version...")
    python_ok = check_python_version()
    print()
    
    print("2. Checking Dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("3. Checking Directory Structure...")
    dirs_ok = check_directory_structure()
    print()
    
    print("4. Checking Critical Files...")
    files_ok = check_critical_files()
    print()
    
    print("5. Testing Core Services...")
    session_ok = test_session_manager()
    storage_ok = test_image_storage()
    print()
    
    print("=" * 60)
    if all([python_ok, deps_ok, dirs_ok, files_ok, session_ok, storage_ok]):
        print("✓ All checks passed! System is ready.")
        print()
        print("To start the server, run:")
        print("  python server/app.py")
    else:
        print("✗ Some checks failed. Please review errors above.")
        print()
        print("To install dependencies, run:")
        print("  pip install -r requirements.txt")
    print("=" * 60)


if __name__ == '__main__':
    main()
