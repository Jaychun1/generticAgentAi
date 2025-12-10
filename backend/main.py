from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agents.api.chat import router as chat_router
from agents.api.upload import router as upload_router
from services.chat_service import create_main_agent

app = FastAPI(
    title="Multi-Agent System API",
    description="API for Financial, SQL, and Web Search Agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(upload_router, prefix="/api/v1/upload", tags=["Upload"])

# Global agent instance
main_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize main agent on startup"""
    global main_agent
    main_agent = create_main_agent()

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Multi-Agent System API",
        "version": "1.0.0",
        "agents": ["financial", "sql", "web"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_initialized": main_agent is not None
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )