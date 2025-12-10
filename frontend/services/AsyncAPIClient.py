import asyncio
import aiohttp
import concurrent.futures
from functools import partial

from .api_client import APIClient, api_client
from config import Config

class AsyncAPIClient:
    """Async client cho performance tốt hơn"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.BACKEND_URL
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 phút
        
    async def chat_async(self, message: str, session_id: str = None, agent_type: str = None):
        """Async chat request"""
        url = f"{Config.CHAT_ENDPOINT}"
        payload = {
            "message": message,
            "session_id": session_id,
            "agent_type": agent_type
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": str(e)}
    
    def chat_with_progress(self, message: str, session_id: str = None, agent_type: str = None):
        """Chat với progress tracking"""
        import threading
        
        result = {}
        event = threading.Event()
        
        def chat_thread():
            try:
                response = api_client.chat(message, session_id, agent_type)
                result.update(response)
            except Exception as e:
                result["error"] = str(e)
            finally:
                event.set()
        
        # Start thread
        thread = threading.Thread(target=chat_thread)
        thread.daemon = True
        thread.start()
        
        return event, result

from functools import lru_cache
import hashlib

class CachedAPIClient(APIClient):
    """APIClient với caching"""
    
    @lru_cache(maxsize=100)
    def _chat_cache_key(self, message: str, agent_type: str = None) -> str:
        """Tạo cache key từ message và agent type"""
        key = f"{message}:{agent_type}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def chat(self, message: str, session_id: str = None, agent_type: str = None, use_cache: bool = True):
        """Chat với caching"""
        if use_cache and not session_id:  # Không cache nếu có session
            cache_key = self._chat_cache_key(message, agent_type)
            if hasattr(self, '_chat_cache') and cache_key in self._chat_cache:
                return self._chat_cache[cache_key]
        
        # Gọi API bình thường
        result = super().chat(message, session_id, agent_type)
        
        # Cache kết quả
        if use_cache and not session_id:
            if not hasattr(self, '_chat_cache'):
                self._chat_cache = {}
            self._chat_cache[cache_key] = result
        
        return result