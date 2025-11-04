import os
import uuid
import time
import gc
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, subfolder=''):
    """Save uploaded file and return the path"""
    if not file or not allowed_file(file.filename):
        return None, "Invalid file type"
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Create subfolder if specified
    upload_path = Config.UPLOAD_FOLDER
    if subfolder:
        upload_path = os.path.join(upload_path, subfolder)
        os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    return file_path, None

def delete_file(file_path):
    """Delete a file from the filesystem with retry logic for locked files"""
    if not file_path or not os.path.exists(file_path):
        return False
    
    # Force garbage collection to release any file handles
    gc.collect()
    
    # Retry up to 5 times with increasing delays
    for attempt in range(5):
        try:
            time.sleep(0.1 * (attempt + 1))  # Increasing delay: 0.1s, 0.2s, 0.3s, etc.
            os.remove(file_path)
            return True
        except PermissionError:
            if attempt == 4:  # Last attempt
                print(f"Warning: Could not delete {file_path} after {attempt + 1} attempts. File may be in use.")
                return False
            continue
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    return False

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0