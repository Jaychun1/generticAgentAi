from urllib.parse import urljoin
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
from functools import wraps

from config import Config
from utils.helpers import format_error_message

class APIClient:
    """HTTP client for backend API communication"""

    _health_check_cache = {}
    _CACHE_TIMEOUT = 600 

    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.BACKEND_URL
        self.session = requests.Session()
        
        # Thêm adapter với timeout và retry
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=2,  # Chỉ retry 2 lần
            backoff_factor=0.5,  # Đợi 0.5, 1 giây
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"MultiAgentAI/{Config.APP_VERSION}",
            "X-Request-Timeout": str(Config.API_TIMEOUT)
        })
    
    @staticmethod
    def _handle_request(func):
        """Decorator to handle API requests with error handling"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.ConnectionError:
                return {"error": "Cannot connect to backend server"}
            except requests.exceptions.Timeout:
                return {"error": "Request timeout"}
            except requests.exceptions.HTTPError as e:
                return {"error": f"HTTP Error: {e.response.status_code}"}
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
        return wrapper

    @_handle_request
    def chat(self, message: str, session_id: str = None, agent_type: str = None, timeout: int = None) -> Dict[str, Any]:
        """Send chat message với timeout tuỳ chỉnh"""
        url = f"{Config.CHAT_ENDPOINT}"
        payload = {
            "message": message,
            "session_id": session_id,
            "agent_type": agent_type
        }
        return self.session.post(
            url, 
            json=payload, 
            timeout=timeout or Config.API_TIMEOUT,
            # Thêm stream=False để không chờ toàn bộ
            stream=False
        )
     
    @_handle_request
    def chat_direct(self, agent_type: str, message: str, session_id: str = None) -> Dict[str, Any]:
        """Chat directly with specific agent"""
        url = f"{Config.CHAT_ENDPOINT}direct/{agent_type}"
        payload = {
            "message": message,
            "session_id": session_id
        }
        return self.session.post(url, json=payload, timeout=Config.API_TIMEOUT)
    
    @_handle_request
    def upload_document(self, file_bytes: bytes, filename: str, metadata: Dict = None) -> Dict[str, Any]:
        """Upload document"""
        url = f"{Config.UPLOAD_ENDPOINT}"
        
        files = {
            'file': (filename, file_bytes)
        }
        
        data = {}
        if metadata:
            data['metadata'] = json.dumps(metadata)
        
        # Use separate session for file upload
        upload_session = requests.Session()
        response = upload_session.post(url, files=files, data=data, timeout=Config.API_TIMEOUT)
        return response
    
    @_handle_request
    def list_documents(self) -> Dict[str, Any]:
        """List uploaded documents"""
        url = f"{Config.DOCUMENTS_ENDPOINT}"
        return self.session.get(url, timeout=Config.API_TIMEOUT)
    
    @_handle_request
    def query_document(self, document_id: str, query: str) -> Dict[str, Any]:
        """Query specific document"""
        url = f"{Config.UPLOAD_ENDPOINT}query"
        payload = {
            "document_id": document_id,
            "query": query
        }
        return self.session.post(url, json=payload, timeout=Config.API_TIMEOUT)
    
    @_handle_request
    def sql_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Execute SQL query"""
        url = f"{Config.SQL_ENDPOINT}"
        payload = {
            "query": query,
            "session_id": session_id
        }
        return self.session.post(url, json=payload, timeout=Config.API_TIMEOUT)
    
    @_handle_request
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        url = f"{Config.CHAT_ENDPOINT}sessions/{session_id}"
        return self.session.get(url, timeout=Config.API_TIMEOUT)
    
    @_handle_request
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete session"""
        url = f"{Config.CHAT_ENDPOINT}sessions/{session_id}"
        return self.session.delete(url, timeout=Config.API_TIMEOUT)
    
    def stream_chat(self, message: str, session_id: str = None, agent_type: str = None):
        """Stream chat response (if backend supports streaming)"""
        # This is a placeholder for streaming implementation
        url = f"{Config.CHAT_ENDPOINT}stream/"
        payload = {
            "message": message,
            "session_id": session_id,
            "agent_type": agent_type,
            "stream": True
        }
        
        try:
            with self.session.post(url, json=payload, stream=True, timeout=Config.STREAM_TIMEOUT) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield json.loads(line)
        except Exception as e:
            yield {"error": str(e)}
    
    def health_check(self, force: bool = False) -> Dict[str, Any]:
        """Check backend health with cache"""
        cache_key = self.base_url
        
        # Kiểm tra cache nếu không force
        if not force and cache_key in self._health_check_cache:
            cached_time, cached_result = self._health_check_cache[cache_key]
            if time.time() - cached_time < self._CACHE_TIMEOUT:
                return cached_result
        
        # Gọi API thực tế
        result = self._perform_health_check()
        
        # Cache kết quả
        self._health_check_cache[cache_key] = (time.time(), result)
        return result
    
    @_handle_request
    def _perform_health_check(self) -> Dict[str, Any]:
        """Actual health check API call"""
        url = urljoin(self.base_url, Config.HEALTH_ENDPOINT)
        return self.session.get(url, timeout=5)
    
    def clear_health_check_cache(self):
        """Clear health check cache"""
        self._health_check_cache.clear()
    
    def validate_backend_connection(self, force: bool = False) -> bool:
        """Validate connection to backend with cache"""
        try:
            result = self.health_check(force=force)
            return not result.get("error") and result.get("status") == "healthy"
        except:
            return False

    def chat_with_progress_callback(self, message: str, callback=None, **kwargs):
        """Chat với callback progress"""
        
        def wrapped_request():
            response = self.session.post(
                f"{Config.CHAT_ENDPOINT}",
                json={"message": message, **kwargs},
                timeout=Config.API_TIMEOUT,
                stream=True  # Enable streaming
            )
            
            # Process stream
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    try:
                        progress = json.loads(chunk.decode())
                        if callback:
                            callback(progress)
                    except:
                        pass
            
            return response.json()
        
        import threading
        thread = threading.Thread(target=wrapped_request)
        thread.start()
        return thread

api_client = APIClient()