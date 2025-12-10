import time
import streamlit as st
from streamlit_option_menu import option_menu

from config import Config
from components.header import show_header
from components.sidebar import show_sidebar

# Import pages
from pages.chat_page import show_chat_page
from pages.sql_page import show_sql_page
from pages.documents_page import show_documents_page
from pages.settings_page import show_settings_page

from services.api_client import api_client

# Page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.PAGE_LAYOUT,
    initial_sidebar_state=Config.SIDEBAR_STATE,
    menu_items={
        'Get Help': Config.HELP_URL,
        'Report a bug': Config.BUG_REPORT_URL,
        'About': Config.ABOUT_TEXT
    }
)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'session_id': None,
        'current_session_id': None, 
        'chat_history': [],
        'chat_messages': [],
        'agent_mode': 'auto',
        'uploaded_documents': [],
        'query_input': '',
        'theme': 'light',
        'api_key': '',
        'user_preferences': {
            'auto_scroll': True,
            'show_agent_badge': True,
            'enable_notifications': False,
            'response_format': 'markdown'
        },
        'backend_status': False,  # Thêm mặc định
        'last_health_check': 0,   # Thêm mặc định
        'health_initialized': False  # Thêm flag để chỉ init 1 lần
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# CHỈ chạy health check khi cần - KHÔNG trong main flow
def initialize_health_check():
    """Initialize health check chỉ 1 lần khi app khởi động"""
    if not st.session_state.get('health_initialized'):
        try:
            # Cache health check result cho cả app
            st.session_state.backend_status = api_client.validate_backend_connection()
            st.session_state.last_health_check = time.time()
            st.session_state.health_initialized = True
        except:
            st.session_state.backend_status = False
            st.session_state.health_initialized = True

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Initialize health check chỉ 1 lần
    initialize_health_check()
    
    # Show header
    show_header()
    
    # Sidebar navigation
    with st.sidebar:
        # App logo and title
        st.title("Multi-Agent AI")
        
        # Navigation menu
        selected_page = option_menu(
            menu_title="Navigation",
            options=["Chat", "SQL Query", "Documents", "Settings"],
            icons=["chat", "database", "folder", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#4F8BF9"},
            }
        )
        
        # Show sidebar components based on selected page
        show_sidebar(selected_page)
    
    # Show selected page
    if selected_page == "Chat":
        show_chat_page()
    elif selected_page == "SQL Query":
        show_sql_page()
    elif selected_page == "Documents":
        show_documents_page()
    elif selected_page == "Settings":
        show_settings_page()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"{Config.APP_VERSION}")
    with col2:
        st.caption("support@agentai.com")
    with col3:
        if st.session_state.get('api_key'):
            st.caption("API Connected")
        else:
            st.caption("API Disconnected")

if __name__ == "__main__":
    main()