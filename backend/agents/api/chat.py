from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import json

router = APIRouter()

# Initialize agents lazily
financial_agent_instance = None
sql_agent_instance = None  
web_agent_instance = None

def get_financial_agent():
    """Get or create financial agent instance"""
    global financial_agent_instance
    if financial_agent_instance is None:
        from agents.financial_agent import FinancialAgent
        financial_agent_instance = FinancialAgent().initialize()
    return financial_agent_instance

def get_sql_agent():
    """Get or create SQL agent instance"""
    global sql_agent_instance
    if sql_agent_instance is None:
        from agents.sql_agent import SQLAgent
        sql_agent_instance = SQLAgent().initialize()
    return sql_agent_instance

def get_web_agent():
    """Get or create web agent instance"""
    global web_agent_instance
    if web_agent_instance is None:
        from agents.web_agent import WebAgent
        web_agent_instance = WebAgent().initialize()
    return web_agent_instance

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID")
    agent_type: Optional[str] = Field(None, description="Force specific agent")
    stream: Optional[bool] = Field(False, description="Stream response")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    agent_used: str = Field(..., description="Which agent was used")
    timestamp: str = Field(..., description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")

# Session storage (in production, use Redis or database)
sessions = {}

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Chat with the multi-agent system"""
    try:
        # Route query or use specified agent
        if request.agent_type:
            agent_name = request.agent_type.lower()
        else:
            from services.chat_service import route_query
            agent_name = route_query(request.message)
        
        # Select agent
        if agent_name == "financial":
            agent = get_financial_agent()
        elif agent_name == "sql":
            agent = get_sql_agent()
        elif agent_name == "web":
            agent = get_web_agent()
        else:
            # Default to financial
            agent = get_financial_agent()
            agent_name = "financial"
        
        # Create or get session
        if not request.session_id or request.session_id not in sessions:
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "history": [],
                "created_at": datetime.now().isoformat(),
                "agent_counts": {"financial": 0, "sql": 0, "web": 0}
            }
        else:
            session_id = request.session_id
        
        # Invoke agent
        result = agent.invoke(request.message)
        
        # Update session
        sessions[session_id]["history"].append({
            "query": request.message,
            "response": result["response"],
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        })
        sessions[session_id]["agent_counts"][agent_name] += 1
        
        # Log interaction in background
        background_tasks.add_task(log_interaction, session_id, request.message, result)
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            agent_used=agent_name,
            timestamp=datetime.now().isoformat(),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.post("/direct/{agent_type}")
async def direct_chat(agent_type: str, request: ChatRequest):
    """Chat directly with a specific agent"""
    if agent_type not in ["financial", "sql", "web"]:
        raise HTTPException(status_code=400, detail="Invalid agent type")
    
    request.agent_type = agent_type
    return await chat(request, BackgroundTasks())

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session history"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": sessions[session_id]["history"],
        "agent_counts": sessions[session_id]["agent_counts"],
        "created_at": sessions[session_id]["created_at"]
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

def log_interaction(session_id: str, query: str, result: Dict[str, Any]):
    """Log interaction to file (background task)"""
    import os
    os.makedirs("logs", exist_ok=True)
    
    log_entry = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "agent": result.get("agent"),
        "response_length": len(result.get("response", ""))
    }
    
    log_file = f"logs/chat_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")