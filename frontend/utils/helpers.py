import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

def format_error_message(error: Any) -> str:
    """Format error message for display"""
    if isinstance(error, dict):
        if 'error' in error:
            return str(error['error'])
        return json.dumps(error, indent=2)
    elif isinstance(error, str):
        return error
    else:
        return str(error)

def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = datetime.now().isoformat()
    random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"session_{random_str}"

def format_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp string"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime(format_str)
    except:
        return timestamp

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely load JSON"""
    try:
        return json.loads(text)
    except:
        return default

def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def extract_filename_from_path(path: str) -> str:
    """Extract filename from path"""
    return path.split('/')[-1] if '/' in path else path

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1)
        filename = name[:255-len(ext)-1] + '.' + ext
    
    return filename

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries, dict2 overwrites dict1"""
    result = dict1.copy()
    result.update(dict2)
    return result

def get_nested_value(data: Dict, keys: List[str], default: Any = None) -> Any:
    """Get nested value from dictionary"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

def format_markdown_for_display(markdown_text: str) -> str:
    """Format markdown text for safe display"""
    # Basic sanitization
    sanitized = markdown_text.replace('<script>', '').replace('</script>', '')
    return sanitized