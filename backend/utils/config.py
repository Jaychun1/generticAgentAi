import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    # ChromaDB
    CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "financial_docs")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/employees.db")
    
    # App
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "8000"))
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Upload
    UPLOAD_DIR = "uploads"
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".md"}

settings = Settings()