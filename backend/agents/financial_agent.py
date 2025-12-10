# File: backend/agents/financial_agent.py
import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional
import functools

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

# Constants
LLM_MODEL = "qwen3"
BASE_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 30

# Pydantic models for structured outputs
class AgentResponse(BaseModel):
    response: str
    agent: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

class SimpleQueryDetector(BaseModel):
    """Detect if query is simple/conversational"""
    is_simple: bool
    reason: str
    suggested_response: Optional[str] = None

def timeout(seconds=TIMEOUT_SECONDS):
    """Timeout decorator using asyncio"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    return future.result(timeout=seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            except Exception as e:
                raise e
        return wrapper
    return decorator

class FinancialAgent:
    """Financial document analysis agent with minimal and full RAG modes"""
    
    def __init__(self, model: str = LLM_MODEL, base_url: str = BASE_URL, use_minimal: bool = True):
        self.llm = ChatOllama(model=model, base_url=base_url, temperature=0.1)
        self.use_minimal = use_minimal
        self.rag_agent = None
        self.llm_structured = self.llm.with_structured_output(SimpleQueryDetector)
        
        # Simple responses cache
        self.simple_responses = {
            "hi": "Hello! 👋 I'm your financial AI assistant. How can I help with financial analysis today?",
            "hello": "Hi there! 😊 I specialize in analyzing financial documents. What would you like to know?",
            "how are you": "I'm doing great! Ready to dive into some financial analysis. What can I help you with?",
            "bye": "Goodbye! 👋 Feel free to come back if you have any financial questions.",
            "thank you": "You're welcome! 😊 Let me know if you need anything else.",
            "what can you do": "I can help with: 📊 Financial document analysis, 💰 Revenue/profit queries, 📈 Quarterly/annual reports, 🗂️ Document search and retrieval.",
            "help": "I'm here to analyze financial documents! You can ask me about: revenue, profits, financial reports, or upload documents for analysis."
        }
    
    def initialize(self):
        """Initialize the full RAG agent if needed"""
        if not self.use_minimal:
            from services.chat_service import create_self_rag
            self.rag_agent = create_self_rag()
        return self
    
    def _is_simple_query(self, query: str) -> tuple[bool, Optional[str]]:
        """Check if query is simple/conversational"""
        query_lower = query.lower().strip()
        
        # Direct match for simple phrases
        for key, response in self.simple_responses.items():
            if key in query_lower and query_lower.split()[0] == key:
                return True, response
        
        # Check with LLM for ambiguous cases
        try:
            detector = self.llm_structured.invoke(
                f"Query: '{query}'\n\n"
                "Is this a simple greeting/conversational query or a serious financial query? "
                "Simple queries: greetings, thanks, casual conversation, vague questions. "
                "Financial queries: specific questions about revenue, profit, documents, analysis."
            )
            
            if detector.is_simple:
                # Use LLM-suggested response or default
                return True, detector.suggested_response or "I'm here to help with financial analysis! Could you please be more specific about what financial information you're looking for?"
        except:
            pass
        
        # Check for vague queries
        vague_patterns = [
            "tell me something",
            "what's in your",
            "show me your",
            "your document",
            "any document",
            "something about",
            "anything interesting"
        ]
        
        if any(pattern in query_lower for pattern in vague_patterns):
            return True, "I'd love to help! Could you please specify what financial information you're looking for? For example: 'What's the revenue for Q4?' or 'Show me profit margins for last year'."
        
        # Check length
        if len(query.split()) <= 2 and not any(word in query_lower for word in 
                                              ['revenue', 'profit', 'financial', 'document', 'report']):
            return True, f"I'm here for financial analysis! Did you have a specific financial question about '{query}'?"
        
        return False, None
    
    def _get_minimal_response(self, query: str) -> Dict[str, Any]:
        """Get response from minimal mode (no RAG)"""
        is_simple, simple_response = self._is_simple_query(query)
        
        if is_simple and simple_response:
            return {
                "response": simple_response,
                "agent": "financial",
                "metadata": {
                    "simple_response": True,
                    "query_type": "conversational",
                    "mode": "minimal"
                }
            }
        
        # For financial queries in minimal mode
        system_prompt = """You are a financial analyst AI assistant. 
        You help users understand financial concepts and answer questions about financial documents.
        
        Guidelines:
        1. If user asks about specific documents, explain that they need to upload documents first
        2. Be helpful but honest about what you can do
        3. Suggest concrete next steps
        4. Keep responses clear and concise
        
        Current limitations:
        - You cannot access specific documents until they are uploaded
        - You can explain financial concepts in general terms"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return {
                "response": response.content,
                "agent": "financial",
                "metadata": {
                    "simple_response": False,
                    "query_type": "financial",
                    "mode": "minimal",
                    "llm_used": True
                }
            }
        except Exception as e:
            return {
                "response": "I'm having trouble processing your request. Please try again or use a simpler query.",
                "agent": "financial",
                "error": str(e),
                "metadata": {"error": True}
            }
    
    @timeout(TIMEOUT_SECONDS)
    def _get_rag_response(self, query: str) -> Dict[str, Any]:
        """Get response from full RAG mode"""
        if not self.rag_agent:
            self.initialize()
        
        # Check if simple query first
        is_simple, simple_response = self._is_simple_query(query)
        if is_simple and simple_response:
            return {
                "response": simple_response,
                "agent": "financial",
                "metadata": {
                    "simple_response": True,
                    "query_type": "conversational",
                    "mode": "rag",
                    "rag_bypassed": True
                }
            }
        
        # Prepare state for RAG agent
        from services.chat_service import AgentState
        from langgraph.graph import StateGraph
        
        # Initialize with transform count to prevent infinite loops
        state = {
            "messages": [HumanMessage(content=query)],
            "retrieved_docs": "",
            "rewritten_queries": [],
            "transform_count": 0,
            "max_transforms": 3
        }
        
        try:
            result = self.rag_agent.invoke(state)
            
            # Extract response from messages
            if result.get("messages") and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_content = "I couldn't generate a response. Please try again."
            
            return {
                "response": response_content,
                "agent": "financial",
                "retrieved_docs": result.get("retrieved_docs", ""),
                "metadata": {
                    "simple_response": False,
                    "query_type": "financial",
                    "mode": "rag",
                    "has_documents": bool(result.get("retrieved_docs")),
                    "queries_generated": len(result.get("rewritten_queries", [])),
                    "transform_count": result.get("transform_count", 0)
                }
            }
            
        except Exception as e:
            # Fallback to minimal mode on RAG error
            print(f"[RAG Error] {e}")
            return self._get_minimal_response(query)
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """Main invoke method with automatic fallback"""
        try:
            if self.use_minimal:
                return self._get_minimal_response(query)
            else:
                return self._get_rag_response(query)
                
        except TimeoutError as e:
            # Fallback to minimal mode on timeout
            print(f"[Timeout] Switching to minimal mode: {e}")
            return {
                "response": "The analysis is taking too long. Here's a quick answer instead:\n\n" + 
                           self._get_minimal_response(query)["response"],
                "agent": "financial",
                "error": str(e),
                "metadata": {
                    "timeout": True,
                    "fallback_to_minimal": True
                }
            }
        except Exception as e:
            return {
                "response": f"An error occurred: {str(e)[:100]}...",
                "agent": "financial",
                "error": str(e),
                "metadata": {"error": True}
            }
    
    def format_messages(self, query: str) -> List:
        """Format messages for the agent"""
        return [HumanMessage(content=query)]
    
    def switch_mode(self, use_minimal: bool) -> None:
        """Switch between minimal and RAG mode"""
        self.use_minimal = use_minimal
        if not use_minimal and not self.rag_agent:
            self.initialize()


# For backward compatibility
class MinimalFinancialAgent(FinancialAgent):
    """Alias for minimal mode"""
    def __init__(self, **kwargs):
        kwargs['use_minimal'] = True
        super().__init__(**kwargs)


# Test the agent
if __name__ == "__main__":
    # Test minimal mode
    print("=== Testing Minimal Mode ===")
    minimal_agent = FinancialAgent(use_minimal=True)
    print("Simple query:", minimal_agent.invoke("hi"))
    print("Financial query:", minimal_agent.invoke("What is revenue?"))
    
    # Test RAG mode (requires services)
    print("\n=== Testing RAG Mode ===")
    try:
        rag_agent = FinancialAgent(use_minimal=False)
        print("Simple query in RAG:", rag_agent.invoke("hello"))
        print("Document query:", rag_agent.invoke("tell me about revenue"))
    except Exception as e:
        print(f"RAG mode test failed: {e}")
        print("Falling back to minimal mode...")
        rag_agent.switch_mode(True)
        print("Fallback response:", rag_agent.invoke("tell me about revenue"))