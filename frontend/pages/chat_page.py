import streamlit as st
import time
from datetime import datetime
import markdown

from config import Config
from services.chat_service import chat_service

def show_chat_page():
    """Display chat interface page"""
    
    # Agent info banner
    current_agent = st.session_state.get('agent_mode', 'auto')
    
    try:
        agent_info = Config.AGENTS[current_agent]
    except KeyError:
        agent_info = Config.AGENTS.get('auto', {'icon': '🤖', 'name': 'Auto', 'description': ''})
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"## {agent_info.get('icon', '🤖')}")
        with col2:
            st.markdown(f"### {agent_info.get('name', 'Auto')} Mode")
            st.caption(agent_info.get('description', ''))
        with col3:
            if st.button("🔄 Switch"):
                st.session_state.agent_mode = 'auto'
                st.rerun()
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        messages = chat_service.get_chat_history()
        
        for i, msg in enumerate(messages):
            try:
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.markdown(msg['content'])
                        
                        # Show timestamp
                        if msg.get('timestamp'):
                            try:
                                dt = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                                st.caption(dt.strftime("%H:%M"))
                            except:
                                st.caption(msg['timestamp'][:16])
                
                else:  # assistant
                    agent_type = msg.get('agent', 'auto')
                    # SỬA: Đảm bảo agent_icon luôn có giá trị
                    agent_data = Config.AGENTS.get(agent_type, {})
                    agent_icon = agent_data.get('icon', '🤖')
                    
                    with st.chat_message("assistant", avatar=agent_icon):
                        # Format markdown if enabled
                        if st.session_state.user_preferences.get('response_format') == 'markdown':
                            st.markdown(msg['content'])
                        else:
                            st.write(msg['content'])
                        
                        # Show agent badge if enabled
                        if st.session_state.user_preferences.get('show_agent_badge'):
                            agent_name = agent_data.get('name', 'Auto')
                            st.caption(f"via {agent_icon} {agent_name}")
                        
                        # Show timestamp
                        if msg.get('timestamp'):
                            try:
                                dt = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                                st.caption(dt.strftime("%H:%M"))
                            except:
                                st.caption(msg['timestamp'][:16])
                        
                        # Show metadata if available
                        if msg.get('metadata'):
                            with st.expander("📊 Details"):
                                st.json(msg['metadata'])
            except Exception as e:
                st.error(f"Error displaying message: {str(e)}")
                continue
    
    # Chat input
    input_col1, input_col2 = st.columns([4, 1])
    
    with input_col1:
        user_input = st.chat_input(
            "Type your message here...",
            key="chat_input"
        )
    
    with input_col2:
        if st.button("🎤 Voice", use_container_width=True):
            st.info("Voice input coming soon!")
    
    # Handle user input
    if user_input:
        # Add user message to display immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
        
        # Get response
        agent_type = None if current_agent == 'auto' else current_agent
        
        with chat_container:
            with st.chat_message("assistant", avatar=agent_info['icon']):
                message_placeholder = st.empty()
                status_placeholder = st.empty()
                
                status_placeholder.info(f"Thinking with {agent_info['name']}...")
                
                # Get response
                response = chat_service.send_message(user_input, agent_type)
                
                if "error" in response:
                    message_placeholder.error(f"Error: {response['error']}")
                else:
                    status_placeholder.empty()
                    message_placeholder.markdown(response.get("response", ""))
                    
                    # Show agent badge
                    if st.session_state.user_preferences.get('show_agent_badge'):
                        response_agent = response.get("agent_used", current_agent)
                        agent_name = Config.AGENTS.get(response_agent, {}).get('name', 'Auto')
                        agent_icon = Config.AGENTS.get(response_agent, {}).get('icon', '🤖')
                        st.caption(f"via {agent_icon} {agent_name}")
        
        # Auto-scroll if enabled
        if st.session_state.user_preferences.get('auto_scroll'):
            st.rerun()
    
    # Quick query suggestions
    st.markdown("---")
    st.subheader("💡 Quick Queries")
    
    quick_queries = {
        "Financial": [
            "What was Amazon's revenue in Q4 2023?",
            "Show me Apple's net income for 2022",
            "Compare Google and Microsoft profit margins"
        ],
        "SQL": [
            "Who are the top 5 highest paid employees?",
            "How many employees are in the engineering department?",
            "What's the average salary by department?"
        ],
        "Web": [
            "Latest AI news from today",
            "Current stock market trends",
            "What's happening in tech this week?"
        ]
    }
    
    for category, queries in quick_queries.items():
        with st.expander(f"{category} Examples"):
            for query in queries:
                if st.button(query, key=f"quick_{category}_{query[:10]}"):
                    st.session_state.quick_query = query
                    st.rerun()
    
    # Handle quick query
    if 'quick_query' in st.session_state:
        user_input = st.session_state.pop('quick_query')
        st.chat_input(user_input, key="quick_query_input")

def chat_with_polling(self, message: str, session_id: str = None, agent_type: str = None, poll_interval: int = 2):
    """Sử dụng polling để tránh timeout"""
    import time
    
    # 1. Gửi request bắt đầu xử lý
    start_response = self.session.post(
        f"{Config.CHAT_ENDPOINT}start",
        json={
            "message": message,
            "session_id": session_id,
            "agent_type": agent_type
        },
        timeout=10  # Timeout ngắn cho request khởi tạo
    )
    
    task_id = start_response.json().get("task_id")
    
    # 2. Poll cho đến khi hoàn thành
    max_polls = 300  # Tối đa 10 phút (300 * 2s)
    for i in range(max_polls):
        time.sleep(poll_interval)
        
        status_response = self.session.get(
            f"{Config.CHAT_ENDPOINT}tasks/{task_id}",
            timeout=5
        )
        
        status = status_response.json()
        
        if status.get("status") == "completed":
            return status.get("result")
        elif status.get("status") == "failed":
            return {"error": status.get("error")}
        # else: continue polling
    
    return {"error": "Timeout after polling"}