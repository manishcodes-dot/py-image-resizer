import os
from typing import List, Tuple
from PIL import Image

# Supported image formats
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def is_supported_image(filepath: str) -> bool:
    """Checks if file is a supported image extension."""
    _, ext = os.path.splitext(filepath.lower())
    return ext in SUPPORTED_EXTENSIONS

def scan_file_or_directory(path: str, recursive: bool = True) -> List[str]:
    """
    Scans a file or folder (optionally recursively) and returns a list of supported image paths.
    """
    found_files = []
    if os.path.isfile(path):
        if is_supported_image(path):
            found_files.append(os.path.abspath(path))
    elif os.path.isdir(path):
        if recursive:
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if is_supported_image(full_path):
                        found_files.append(os.path.abspath(full_path))
        else:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isfile(full_path) and is_supported_image(full_path):
                    found_files.append(os.path.abspath(full_path))
    return found_files

def format_size(bytes_size: int) -> str:
    """Formats file size into human-readable representation."""
    if bytes_size < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_image_info(filepath: str) -> Tuple[Tuple[int, int], str]:
    """
    Retrieves the width, height, and formatted resolution string of an image
    without loading it entirely into memory.
    """
    try:
        with Image.open(filepath) as img:
            w, h = img.size
            return (w, h), f"{w} x {h}"
    except Exception:
        return (0, 0), "Unknown"

def calculate_new_dimensions(
    orig_w: int, 
    orig_h: int, 
    resize_mode: str, 
    custom_w: int, 
    custom_h: int, 
    maintain_aspect: bool
) -> Tuple[int, int]:
    """
    Calculates new dimensions based on the resizing parameters.
    """
    if resize_mode == "original" or orig_w <= 0 or orig_h <= 0:
        return orig_w, orig_h
        
    target_w = orig_w
    target_h = orig_h
    
    if resize_mode == "1920":
        target_w = 1920
    elif resize_mode == "1080":
        target_w = 1080
    elif resize_mode == "720":
        target_w = 720
    elif resize_mode == "custom_w":
        target_w = custom_w
    elif resize_mode == "custom_h":
        target_h = custom_h
        
    # Apply aspect ratio adjustment
    if maintain_aspect:
        aspect = orig_w / orig_h
        if resize_mode in ("1920", "1080", "720", "custom_w"):
            # Width is fixed, calculate height
            target_h = int(target_w / aspect)
        elif resize_mode == "custom_h":
            # Height is fixed, calculate width
            target_w = int(target_h * aspect)
    else:
        # If not maintaining aspect ratio, custom mode should specify dimensions
        if resize_mode == "custom_w":
            target_h = orig_h  # Keep original height if only width is set
        elif resize_mode == "custom_h":
            target_w = orig_w  # Keep original width if only height is set
            
    return max(1, target_w), max(1, target_h)

def get_resource_path(relative_path: str) -> str:
    """Gets the absolute path to a resource, supporting development and PyInstaller environments."""
    import sys
    try:
        # PyInstaller extracts resources to sys._MEIPASS in frozen state
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
