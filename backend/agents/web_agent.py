from typing import Dict, Any
from .base_agent import BaseAgent
from services.search_service import create_web_agent

class WebAgent(BaseAgent):
    """Web search agent"""
    
    def initialize(self):
        """Initialize the web agent"""
        self.agent = create_web_agent()
        return self
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """Invoke the web agent"""
        if not self.agent:
            self.initialize()
        
        state = {
            "messages": self.format_messages(query)
        }
        
        result = self.agent(state)
        
        return {
            "response": result["messages"][-1].content,
            "agent": "web",
            "metadata": {
                "query_type": "web_search",
                "sources": self._extract_sources(result["messages"][-1].content)
            }
        }
    
    def _extract_sources(self, response: str):
        """Extract sources from web search response"""
        import re
        urls = re.findall(r'https?://[^\s]+', response)
        return urls[:5]  