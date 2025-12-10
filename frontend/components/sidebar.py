import streamlit as st
from config import Config

def show_sidebar(selected_page):
    """Display sidebar navigation + settings"""
    with st.sidebar:
        # Logo
        st.image("https://img.icons8.com/color/96/000000/chatbot.png", width=80)

        st.title("🤖 AgentAI")

        # --- Navigation ---
        st.subheader("📱 Navigation")
        
        if "page" not in st.session_state:
            st.session_state.page = "chat"

        col1, col2 = st.columns(2)

        # Row 1
        with col1:
            if st.button("💬 Chat", use_container_width=True,
                type="primary" if st.session_state.page == "chat" else "secondary"):
                st.session_state.page = "chat"
                st.rerun()

        with col2:
            if st.button("🗄️ SQL", use_container_width=True,
                type="primary" if st.session_state.page == "sql" else "secondary"):
                st.session_state.page = "sql"
                st.rerun()

        # Row 2
        col3, col4 = st.columns(2)

        with col3:
            if st.button("📁 Documents", use_container_width=True,
                type="primary" if st.session_state.page == "documents" else "secondary"):
                st.session_state.page = "documents"
                st.rerun()

        with col4:
            if st.button("⚙️ Settings", use_container_width=True,
                type="primary" if st.session_state.page == "settings" else "secondary"):
                st.session_state.page = "settings"
                st.rerun()

        st.markdown("---")

        # --- Agent Mode (only in Chat page) ---
        if st.session_state.page == "chat":
            st.subheader("🤖 Agent Mode")

            agent_options = {
                "auto": ("🤖 Auto", "Auto-route to best agent"),
                "financial": ("💰 Financial", "Financial document analysis"),
                "sql": ("🗄️ SQL", "Database queries"),
                "web": ("🌐 Web", "Web search"),
            }

            for agent_id, (icon_text, description) in agent_options.items():
                if st.button(
                    f"{icon_text}",
                    key=f"agent_{agent_id}",
                    use_container_width=True,
                    type="primary" if st.session_state.agent_mode == agent_id else "secondary"
                ):
                    st.session_state.agent_mode = agent_id
                    st.rerun()

            st.caption(f"**Selected:** {agent_options[st.session_state.agent_mode][1]}")

        st.markdown("---")

        # --- Session Controls ---
        st.subheader("💬 Session")

        if st.session_state.get('session_id'):
            short = st.session_state.session_id[:8] + "..."
            st.info(f"Session: `{short}`")

            if st.button("🆕 New Session", use_container_width=True):
                st.session_state.session_id = None
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.warning("No active session")

            if st.button("🆕 Start Session", use_container_width=True):
                import uuid
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

        st.markdown("---")

        # --- Backend Status ---
        st.subheader("📊 Status")

        # CHỈ sử dụng từ session_state, không gọi API trực tiếp
        backend_status = st.session_state.get('backend_status', False)
        
        if backend_status:
            st.success("Backend Connected")
        else:
            st.error("Backend Disconnected")

        # Quick stats
        if st.session_state.get('chat_history'):
            st.metric("Messages", len(st.session_state.chat_history))