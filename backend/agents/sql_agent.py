from typing import Dict, Any
from .base_agent import BaseAgent
from services.sql_service import create_sql_agent

class SQLAgent(BaseAgent):
    """SQL database query agent"""
    
    def initialize(self):
        """Initialize the SQL agent"""
        self.agent = create_sql_agent()
        return self
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """Invoke the SQL agent"""
        if not self.agent:
            self.initialize()
        
        state = {
            "messages": self.format_messages(query)
        }
        
        result = self.agent(state)
        
        return {
            "response": result["messages"][-1].content,
            "agent": "sql",
            "metadata": {
                "query_type": "database",
                "has_results": "result" in result["messages"][-1].content.lower()
            }
        }