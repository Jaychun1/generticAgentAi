from typing import TypedDict, Annotated, List
import operator
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from tools.sql_tools import ALL_SQL_TOOLS
from langchain_ollama import ChatOllama

LLM_MODEL = "qwen3"
BASE_URL = "http://localhost:11434"
llm = ChatOllama(model=LLM_MODEL, base_url=BASE_URL)

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]

def create_sql_agent():
    """Create SQL database agent."""
    system_prompt = """You are an SQL database expert. Use these tools to answer questions:
    
    Database Schema:
    [Schema will be provided by tools]
    
    Workflow:
    1. Use get_database_schema if you need table structure
    2. Use generate_sql_query to create SQL
    3. Use execute_sql_query to run the query
    4. Use fix_sql_error if there's an error
    
    Rules:
    - Only generate SELECT queries
    - Validate queries before executing
    - Format results clearly
    - Use markdown tables for tabular data"""
    
    agent = create_agent(llm, ALL_SQL_TOOLS, system_prompt=system_prompt)
    
    def sql_node(state: AgentState):
        system_msg = SystemMessage(system_prompt)
        messages = [system_msg] + state["messages"]
        result = agent.invoke({"messages": messages})
        return {"messages": result["messages"]}
    
    return sql_node