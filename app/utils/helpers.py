"""
Utility functions for the application.
"""

import os
import hashlib
from typing import BinaryIO, Tuple
from pathlib import Path

from app.config import settings


def save_uploaded_file(file_content: bytes, filename: str) -> Tuple[str, str]:
    """Save an uploaded file to the upload directory.

    Args:
        file_content: File content
        filename: Original filename

    Returns:
        Tuple of (file path, file hash)
    """
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Calculate file hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Create a unique filename
    file_ext = Path(filename).suffix
    unique_filename = f"{file_hash}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path, file_hash


def get_file_hash(file: BinaryIO) -> str:
    """Calculate the hash of a file.

    Args:
        file: File object

    Returns:
        File hash
    """
    # Save current position
    current_pos = file.tell()
    
    # Reset to beginning of file
    file.seek(0)
    
    # Calculate hash
    file_hash = hashlib.sha256(file.read()).hexdigest()
    
    # Restore position
    file.seek(current_pos)
    
    return file_hash
