"""
Replacement for the removed imghdr module for Python 3.13 compatibility.
"""
from os import PathLike

__all__ = ["what"]

def what(file, h=None):
    f = None
    try:
        if h is None:
            if isinstance(file, (str, PathLike)):
                f = open(file, 'rb')
                h = f.read(32)
            else:
                location = file.tell()
                h = file.read(32)
                file.seek(location)
                
        if not h or len(h) < 4:
            return None

        # PNG
        if h.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
            
        # JPEG
        if h.startswith(b'\xff\xd8'):
            return 'jpeg'
            
        # GIF
        if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
            return 'gif'
            
        # WEBP
        if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
            return 'webp'
            
        return None
        
    except Exception:
        return None
    finally:
        if f:
            f.close()
