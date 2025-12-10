import uuid
from datetime import datetime
from typing import Dict, Any
import re

def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().isoformat()

def extract_company_name(query: str) -> str:
    """Extract company name from query"""
    query_lower = query.lower()
    
    companies = {
        'amazon': 'amazon',
        'apple': 'apple', 
        'google': 'google',
        'microsoft': 'microsoft',
        'tesla': 'tesla',
        'nvidia': 'nvidia',
        'meta': 'meta',
        'facebook': 'meta'
    }
    
    for name, company in companies.items():
        if name in query_lower:
            return company
    
    return None

def extract_year(query: str) -> int:
    """Extract year from query"""
    year_match = re.search(r'20\d{2}', query)
    if year_match:
        return int(year_match.group())
    return None

def format_file_size(bytes: int) -> str:
    """Format file size in human readable format"""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes / (1024 * 1024 * 1024):.1f} GB"
    
from langchain_core.messages import HumanMessage

def get_latest_user_query(messages: list):
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return messages[0].content if messages else ''
