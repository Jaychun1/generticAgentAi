import streamlit as st
import json
import requests
from config import Config
from services.api_client import api_client


def show_settings_page():
    """Display application settings page"""
    
    st.header("⚙️ Settings")
    
    # CHỈ gọi health check 1 lần duy nhất khi mở trang
    if 'health_initialized' not in st.session_state:
        st.session_state.health_initialized = True
        
        # Initialize health status
        try:
            st.session_state.backend_ok = api_client.validate_backend_connection()
            st.session_state.backend_health = api_client.health_check() if st.session_state.backend_ok else None
        except:
            st.session_state.backend_ok = False
            st.session_state.backend_health = None
        
        # Initialize Ollama status
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=3)
            st.session_state.ollama_status = response.status_code == 200
        except:
            st.session_state.ollama_status = False
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 General", "🤖 Agents", "🔌 API", "ℹ️ About"])
    
    with tab1:
        # General settings
        st.subheader("General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # UI Settings
            st.markdown("### 🎨 UI Settings")
            
            theme = st.selectbox(
                "Theme",
                ["Light", "Dark", "System"],
                index=["Light", "Dark", "System"].index(st.session_state.get('theme', 'Light'))
            )
            st.session_state.theme = theme
            
            auto_scroll = st.checkbox(
                "Auto-scroll chat",
                value=st.session_state.user_preferences.get('auto_scroll', True),
                help="Automatically scroll to latest message"
            )
            
            show_agent_badge = st.checkbox(
                "Show agent badge",
                value=st.session_state.user_preferences.get('show_agent_badge', True),
                help="Display which agent responded to each message"
            )
        
        with col2:
            # Chat Settings
            st.markdown("### 💬 Chat Settings")
            
            max_history = st.slider(
                "Max chat history",
                min_value=10,
                max_value=200,
                value=Config.MAX_CHAT_HISTORY,
                step=10,
                help="Maximum number of messages to keep in chat history"
            )
            
            response_format = st.selectbox(
                "Response format",
                ["markdown", "plain text"],
                index=0 if st.session_state.user_preferences.get('response_format') == 'markdown' else 1
            )
            
            enable_notifications = st.checkbox(
                "Enable notifications",
                value=st.session_state.user_preferences.get('enable_notifications', False)
            )
        
        # Update preferences
        st.session_state.user_preferences.update({
            'auto_scroll': auto_scroll,
            'show_agent_badge': show_agent_badge,
            'response_format': response_format,
            'enable_notifications': enable_notifications
        })
        
        if st.button("💾 Save General Settings"):
            st.success("Settings saved!")
    
    with tab2:
        # Agent settings
        st.subheader("Agent Configuration")
        
        for agent_id, agent_info in Config.AGENTS.items():
            with st.expander(f"{agent_info['icon']} {agent_info['name']}", expanded=agent_id == 'auto'):
                st.markdown(f"**Description**: {agent_info['description']}")
                
                # Agent-specific settings
                if agent_id == 'financial':
                    retrieval_k = st.slider(
                        "Documents to retrieve",
                        min_value=1,
                        max_value=10,
                        value=3,
                        key=f"{agent_id}_retrieval_k"
                    )
                    
                    enable_self_rag = st.checkbox(
                        "Enable Self-RAG",
                        value=True,
                        key=f"{agent_id}_self_rag"
                    )
                
                elif agent_id == 'sql':
                    max_rows = st.slider(
                        "Max rows to return",
                        min_value=10,
                        max_value=1000,
                        value=100,
                        step=10,
                        key=f"{agent_id}_max_rows"
                    )
                
                elif agent_id == 'web':
                    search_results = st.slider(
                        "Search results",
                        min_value=5,
                        max_value=20,
                        value=10,
                        key=f"{agent_id}_search_results"
                    )
                    
                    search_region = st.selectbox(
                        "Search region",
                        ["us-en", "uk-en", "au-en", "global"],
                        key=f"{agent_id}_search_region"
                    )
        
        if st.button("💾 Save Agent Settings"):
            st.success("Agent settings saved!")
    
    with tab3:
        # API settings
        st.subheader("API Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔌 Backend Connection")
            
            backend_url = st.text_input(
                "Backend URL",
                value=Config.BACKEND_URL,
                help="URL of the backend API server"
            )
            
            api_timeout = st.number_input(
                "API Timeout (seconds)",
                min_value=5,
                max_value=120,
                value=Config.API_TIMEOUT,
                step=5
            )
            
            # Test connection với button rõ ràng
            if st.button("🔗 Test Connection", key="test_connection"):
                with st.spinner("Testing connection..."):
                    temp_client = api_client.__class__(base_url=backend_url)
                    if temp_client.validate_backend_connection():
                        st.success("✅ Connection successful!")
                        # Cập nhật session_state
                        st.session_state.backend_ok = True
                        st.session_state.backend_health = temp_client.health_check()
                    else:
                        st.error("❌ Connection failed")
                        st.session_state.backend_ok = False
                        st.session_state.backend_health = None
        
        with col2:
            st.markdown("### 🔑 API Keys")
            
            # Ollama API key (if needed)
            ollama_api_key = st.text_input(
                "Ollama API Key",
                type="password",
                help="Optional: API key for Ollama cloud"
            )
            
            # Other API keys can be added here
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Optional: For OpenAI models"
            )
        
        # API status - HIỂN THỊ từ session_state, không gọi lại
        st.markdown("### 📊 API Status")
        
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            if st.session_state.backend_ok:
                st.success("Backend: ✅ Online")
            else:
                st.error("Backend: ❌ Offline")
        
        with status_col2:
            if st.session_state.ollama_status:
                st.success("Ollama: ✅ Online")
            else:
                st.warning("Ollama: ⚠️ Offline")
        
        with status_col3:
            st.info("Database: Unknown")
        
        # Refresh button nếu cần
        if st.button("🔄 Refresh All Status", key="refresh_all"):
            with st.spinner("Refreshing status..."):
                try:
                    st.session_state.backend_ok = api_client.validate_backend_connection()
                    if st.session_state.backend_ok:
                        st.session_state.backend_health = api_client.health_check()
                except:
                    st.session_state.backend_ok = False
                
                try:
                    response = requests.get("http://localhost:11434/api/version", timeout=3)
                    st.session_state.ollama_status = response.status_code == 200
                except:
                    st.session_state.ollama_status = False
            
            st.success("Status refreshed!")
            st.rerun()
    
    with tab4:
        # About page - CHỈ hiển thị từ session_state
        st.subheader("About Multi-Agent AI System")
        
        col1, col2 = st.columns([1, 2])
        
        with col2:
            st.markdown(f"""
            ### {Config.APP_NAME}
            **Version**: {Config.APP_VERSION}
            
            A sophisticated multi-agent AI system with specialized agents for:
            - 📊 Financial document analysis
            - 🗄️ SQL database querying
            - 🌐 Web search and information retrieval
            
            **Key Features:**
            ✅ Auto-routing to appropriate agents
            ✅ Document upload and vector search
            ✅ Real-time web search
            ✅ SQL query generation and execution
            ✅ Chat history and session management
            """)
        
        st.markdown("---")
        
        # System information
        st.subheader("System Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown("**Backend Information**")
            st.text(f"URL: {Config.BACKEND_URL}")
            
            # Sử dụng session_state để hiển thị
            health_status = "Healthy" if st.session_state.backend_ok else "Unhealthy"
            st.text(f"Health: {health_status}")
            
            # Chỉ hiển thị chi tiết health khi có dữ liệu
            if st.session_state.backend_health and "error" not in st.session_state.backend_health:
                with st.expander("Health Details"):
                    st.json(st.session_state.backend_health)
        
        with info_col2:
            st.markdown("**Frontend Information**")
            
            # Get session info
            session_info = {
                "Current Session": st.session_state.get('current_session_id', 'None'),
                "Chat Messages": len(st.session_state.get('chat_messages', [])),
                "Uploaded Documents": len(st.session_state.get('uploaded_documents', [])),
                "Theme": st.session_state.get('theme', 'Light')
            }
            
            st.json(session_info)
        
        # Export/Import settings
        st.markdown("---")
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export settings
            st.markdown("#### Export Settings")
            
            export_format = st.selectbox(
                "Format",
                ["json", "yaml"],
                key="export_format"
            )
            
            if st.button("📤 Export All Settings"):
                settings_data = {
                    "user_preferences": st.session_state.user_preferences,
                    "theme": st.session_state.theme,
                    "agent_mode": st.session_state.agent_mode
                }
                
                if export_format == "json":
                    export_content = json.dumps(settings_data, indent=2)
                    mime_type = "application/json"
                    file_ext = "json"
                else:
                    import yaml
                    export_content = yaml.dump(settings_data)
                    mime_type = "text/yaml"
                    file_ext = "yaml"
                
                st.download_button(
                    label="📥 Download Settings",
                    data=export_content,
                    file_name=f"agentai_settings.{file_ext}",
                    mime=mime_type
                )
        
        with col2:
            # Import settings
            st.markdown("#### Import Settings")
            
            uploaded_settings = st.file_uploader(
                "Choose settings file",
                type=["json", "yaml", "yml"],
                key="settings_uploader"
            )
            
            if uploaded_settings and st.button("📥 Import Settings"):
                try:
                    content = uploaded_settings.read().decode()
                    
                    if uploaded_settings.name.endswith('.json'):
                        settings = json.loads(content)
                    else:
                        import yaml
                        settings = yaml.safe_load(content)
                    
                    # Apply settings
                    for key, value in settings.items():
                        if key in st.session_state:
                            st.session_state[key] = value
                    
                    st.success("✅ Settings imported successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to import settings: {str(e)}")
        
        # Reset to defaults
        st.markdown("---")
        st.warning("⚠️ Danger Zone")
        
        if st.button("🔄 Reset to Defaults", type="secondary"):
            st.session_state.clear()
            st.success("✅ All settings reset to defaults!")
            st.rerun()