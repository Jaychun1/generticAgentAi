import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Backend API
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # API Endpoints
    CHAT_ENDPOINT = f"{BACKEND_URL}/api/v1/chat/"
    UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/v1/upload/"
    DOCUMENTS_ENDPOINT = f"{BACKEND_URL}/api/v1/upload/documents"
    HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
    SQL_ENDPOINT = f"{BACKEND_URL}/api/v1/sql/"  # Hypothetical endpoint
    
    # Application settings
    APP_NAME = "Multi-Agent AI System"
    APP_VERSION = "v2.0.0"
    PAGE_TITLE = "Multi-Agent AI"
    PAGE_ICON = ""
    PAGE_LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"
    
    # UI Settings
    MAX_CHAT_HISTORY = 50
    MAX_FILE_SIZE_MB = 10
    SUPPORTED_FILE_TYPES = ["pdf", "txt", "docx", "csv", "md"]
    
    # Agent settings
    AGENTS = {
        "auto": {"name": "Auto", "icon": "", "description": "Auto-route to best agent"},
        "financial": {"name": "Financial", "icon": "", "description": "Financial document analysis"},
        "sql": {"name": "SQL", "icon": "", "description": "Database queries"},
        "web": {"name": "Web", "icon": "", "description": "Web search"}
    }
    
    # Colors
    PRIMARY_COLOR = "#4F8BF9"
    SUCCESS_COLOR = "#00C851"
    WARNING_COLOR = "#FFBB33"
    ERROR_COLOR = "#FF4444"
    INFO_COLOR = "#33B5E5"
    
    # External URLs
    HELP_URL = "https://docs.agentai.com"
    BUG_REPORT_URL = "https://github.com/agentai/issues"
    ABOUT_TEXT = """
    Multi-Agent AI System v2.0
    A sophisticated AI system with specialized agents for different tasks.
    """
    
    # Timeout settings
    API_TIMEOUT = 30
    STREAM_TIMEOUT = 60
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        required_env_vars = []
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        return True
    

    AGENTS = {
        'auto': {
            'icon': '🤖',
            'name': 'Auto',
            'description': 'Automatically selects the best agent for your query'
        },
        'financial': {
            'icon': '💰',
            'name': 'Financial',
            'description': 'Specialized in financial data and analysis'
        },
        'sql': {
            'icon': '🗃️',
            'name': 'SQL Expert',
            'description': 'Handles database queries and SQL analysis'
        },
        'web': {
            'icon': '🌐',
            'name': 'Web Search',
            'description': 'Searches the web for current information'
        }
    }
    
    @classmethod
    def get_agent_info(cls, agent_type: str = 'auto'):
        """Safely get agent info with defaults"""
        agent = cls.AGENTS.get(agent_type, cls.AGENTS['auto'])
        return {
            'icon': agent.get('icon', '🤖'),
            'name': agent.get('name', 'Auto'),
            'description': agent.get('description', '')
        }