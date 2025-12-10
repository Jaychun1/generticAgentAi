from typing import TypedDict, Annotated, List
import operator
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from tools.web_tools import web_search
from langchain_ollama import ChatOllama

LLM_MODEL = "qwen3"
BASE_URL = "http://localhost:11434"
llm = ChatOllama(model=LLM_MODEL, base_url=BASE_URL)

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]

def create_web_agent():
    """Handle web search queries."""
    system_prompt = """You are a web search assistant. Use the web_search tool to find current information.
    
    Guidelines:
    1. Search for relevant, up-to-date information
    2. Synthesize information from multiple sources
    3. Provide citations or sources when possible
    4. Be concise but comprehensive
    
    Use the web_search tool for any information you need."""
    
    agent = create_agent(llm, [web_search])
    
    def web_node(state: AgentState):
        system_msg = SystemMessage(system_prompt)
        messages = [system_msg] + state["messages"]
        result = agent.invoke({"messages": messages})
        return {"messages": result["messages"]}
    
    return web_node