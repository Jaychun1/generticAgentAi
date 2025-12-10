from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, model: str = "qwen3", base_url: str = "http://localhost:11434"):
        self.llm = ChatOllama(model=model, base_url=base_url)
        self.agent = None
        
    @abstractmethod
    def initialize(self):
        """Initialize the agent"""
        pass
    
    @abstractmethod
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """Invoke the agent with a query"""
        pass
    
    def format_messages(self, query: str):
        """Format messages for the agent"""
        return [HumanMessage(content=query)]