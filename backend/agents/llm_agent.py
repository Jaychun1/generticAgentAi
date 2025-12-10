# /opt/generticAgentAi/backend/agents/llm_agent.py
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)

def get_llm_agent(model_name: str = "qwen3"):
    """
    Create a direct LLM agent using Ollama
    For general questions not requiring specialized agents
    """
    
    # Initialize Ollama LLM
    llm = OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434",
        temperature=0.7,
        num_predict=1000,
        top_k=40,
        top_p=0.95
    )
    
    # Create a prompt template
    system_prompt = """You are a helpful AI assistant. 
    Provide clear, accurate, and concise answers to the user's questions.
    If you don't know something, say so honestly.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    # Create chain
    chain = prompt | llm
    
    class LLMAgent:
        def __init__(self, chain, model_name):
            self.chain = chain
            self.model_name = model_name
            
        def invoke(self, input_text: str):
            """Invoke the LLM with the input text"""
            try:
                logger.info(f"LLM Agent ({self.model_name}) processing: {input_text[:100]}...")
                
                # Get response from LLM
                response = self.chain.invoke({"input": input_text})
                
                return {
                    "response": response,
                    "metadata": {
                        "model": self.model_name,
                        "agent_type": "llm",
                        "tokens_used": len(str(response).split())
                    }
                }
                
            except Exception as e:
                logger.error(f"LLM Agent error: {e}")
                return {
                    "response": f"Sorry, I encountered an error: {str(e)}",
                    "metadata": {"error": True, "agent_type": "llm"}
                }
    
    return LLMAgent(chain, model_name)