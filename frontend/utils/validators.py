import re
from typing import Optional, Tuple
from config import Config

class Validators:
    """Collection of validation functions"""
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: Optional[list] = None) -> Tuple[bool, str]:
        """Validate file type"""
        if allowed_types is None:
            allowed_types = Config.SUPPORTED_FILE_TYPES
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if not file_ext:
            return False, "File has no extension"
        
        if file_ext not in allowed_types:
            return False, f"File type .{file_ext} not allowed. Allowed: {', '.join(allowed_types)}"
        
        return True, ""
    
    @staticmethod
    def validate_file_size(file_size_bytes: int, max_size_mb: Optional[int] = None) -> Tuple[bool, str]:
        """Validate file size"""
        if max_size_mb is None:
            max_size_mb = Config.MAX_FILE_SIZE_MB
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size_bytes > max_size_bytes:
            file_size_mb = file_size_bytes / (1024 * 1024)
            return False, f"File size {file_size_mb:.1f}MB exceeds maximum {max_size_mb}MB"
        
        return True, ""
    
    @staticmethod
    def validate_sql_query(query: str) -> Tuple[bool, str]:
        """Validate SQL query for safety"""
        # Convert to uppercase for checking
        query_upper = query.upper().strip()
        
        # Check for dangerous keywords
        dangerous_keywords = [
            'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'INSERT', 
            'UPDATE', 'CREATE', 'EXEC', 'EXECUTE', 'GRANT',
            'REVOKE', 'MERGE', 'LOCK'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Dangerous SQL keyword '{keyword}' detected"
        
        # Check if it starts with SELECT (basic safety)
        if not query_upper.startswith('SELECT'):
            # Check if it's natural language
            sql_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
            if not any(keyword in query_upper for keyword in sql_keywords):
                return True, "Assuming natural language query"
        
        return True, "Query validated"
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL format"""
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if re.match(pattern, url):
            return True, ""
        return False, "Invalid URL format"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, ""
        return False, "Invalid email format"
    
    @staticmethod
    def validate_metadata(metadata: dict) -> Tuple[bool, str]:
        """Validate document metadata"""
        required_fields = ['company_name', 'doc_type']
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                return False, f"Missing required field: {field}"
        
        # Validate doc_type
        valid_doc_types = ['10-k', '10-q', '8-k', 'other', 'annual report', 'quarterly report']
        if metadata['doc_type'] not in valid_doc_types:
            return False, f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}"
        
        # Validate fiscal year if present
        if 'fiscal_year' in metadata:
            try:
                year = int(metadata['fiscal_year'])
                if year < 2000 or year > 2030:
                    return False, "Fiscal year must be between 2000 and 2030"
            except ValueError:
                return False, "Fiscal year must be a number"
        
        return True, ""