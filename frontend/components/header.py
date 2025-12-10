import streamlit as st
from config import Config

def show_header():
    """Display application header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title(Config.PAGE_TITLE)
        st.markdown(Config.ABOUT_TEXT)
    
    with col3:
        # Status indicator - CHỈ sử dụng từ session_state
        backend_status = st.session_state.get('backend_status', False)
        
        if backend_status:
            st.success("Online")
        else:
            st.error("Offline")
        
        # Quick stats
        if st.session_state.get('chat_messages'):
            msg_count = len(st.session_state.chat_messages)
            st.caption(f"{msg_count // 2} messages")
    
    st.markdown("---")