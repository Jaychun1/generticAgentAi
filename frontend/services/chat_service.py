import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import traceback

from config import Config
from .api_client import api_client

def _now_iso():
    return datetime.now().isoformat()

class ChatService:
    """Service for handling chat operations"""

    def __init__(self):
        self.api_client = api_client
        self._init_chat_state()

    def _init_chat_state(self):
        """Initialize chat-related session state"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []

        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}

        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = str(uuid.uuid4())

        # optional debug log
        if 'chat_debug' not in st.session_state:
            st.session_state.chat_debug = []

    # -------------------------
    # Core send flow (robust)
    # -------------------------
    def send_message(self, message: str, agent_type: str = None) -> Dict[str, Any]:
        """
        Send message and get response.

        Important behavior:
        - Immediately append user message + assistant placeholder to session history so that
          UI reruns or auto-scroll won't lose the "thinking" state.
        - Then call API; when API returns, update the assistant placeholder in-place.
        - Return a result dict with keys: response, agent_used, timestamp, metadata or error.
        """
        session_id = st.session_state.current_session_id
        user_ts = _now_iso()
        placeholder_id = str(uuid.uuid4())

        # 1) Append user message and assistant placeholder immediately
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": user_ts,
            "agent": None
        }

        assistant_placeholder = {
            "role": "assistant",
            "content": "Thinking...",
            "timestamp": user_ts,
            "agent": "pending",
            "metadata": {"status": "pending"},
            "placeholder_id": placeholder_id
        }

        st.session_state.chat_messages.extend([user_msg, assistant_placeholder])
        self._trim_history()

        # Debug
        st.session_state.chat_debug.append(f"[{_now_iso()}] queued message id={placeholder_id}")

        # 2) Call API (safely)
        result = {}
        try:
            if agent_type and agent_type != "auto":
                api_result = self.api_client.chat_direct(
                    agent_type=agent_type,
                    message=message,
                    session_id=session_id
                )
            else:
                api_result = self.api_client.chat(
                    message=message,
                    session_id=session_id,
                    agent_type=agent_type
                )

            # Expect api_result to be a dict. Guard against bad format.
            if not isinstance(api_result, dict):
                api_result = {"error": "Invalid response format from api_client", "raw": str(api_result)}

            if "error" in api_result:
                # Update placeholder with error
                err_msg = api_result.get("error", "Unknown error")
                self._update_assistant_placeholder(placeholder_id,
                                                   content=f"Error: {err_msg}",
                                                   agent_used=api_result.get("agent_used", "auto"),
                                                   metadata={"error": err_msg})
                result = {"error": err_msg}
            else:
                # Successful response: update assistant placeholder with actual response
                resp_text = api_result.get("response", "")
                agent_used = api_result.get("agent_used", agent_type or "auto")
                ts = api_result.get("timestamp", _now_iso())
                metadata = api_result.get("metadata", {})

                self._update_assistant_placeholder(placeholder_id,
                                                   content=resp_text,
                                                   agent_used=agent_used,
                                                   timestamp=ts,
                                                   metadata=metadata)

                result = {
                    "response": resp_text,
                    "agent_used": agent_used,
                    "timestamp": ts,
                    "metadata": metadata
                }

        except Exception as e:
            tb = traceback.format_exc()
            err_msg = f"Exception calling api_client: {str(e)}"
            # Update assistant placeholder with error info
            self._update_assistant_placeholder(placeholder_id,
                                               content=f"Service error: {str(e)}",
                                               agent_used=agent_type or "auto",
                                               metadata={"error": err_msg, "trace": tb})
            # return an error dict
            result = {"error": err_msg, "trace": tb}

        # Return final result (no raising) — UI will display whatever in history
        return result

    # -------------------------
    # Helpers to update history
    # -------------------------
    def _update_assistant_placeholder(self, placeholder_id: str, content: str,
                                      agent_used: Optional[str] = None,
                                      timestamp: Optional[str] = None,
                                      metadata: Optional[Dict[str, Any]] = None):
        """
        Find the assistant message with placeholder_id and update it in place.
        If not found, append a new assistant message.
        """
        if timestamp is None:
            timestamp = _now_iso()
        if metadata is None:
            metadata = {}

        found = False
        for i, msg in enumerate(st.session_state.chat_messages):
            if msg.get("role") == "assistant" and msg.get("placeholder_id") == placeholder_id:
                # Update fields (keep placeholder_id)
                st.session_state.chat_messages[i].update({
                    "content": content,
                    "timestamp": timestamp,
                    "agent": agent_used or st.session_state.chat_messages[i].get("agent", "auto"),
                    "metadata": metadata
                })
                # remove placeholder_id (no longer a placeholder)
                st.session_state.chat_messages[i].pop("placeholder_id", None)
                found = True
                break

        if not found:
            # fallback: append assistant message
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "timestamp": timestamp,
                "agent": agent_used or "auto",
                "metadata": metadata
            }
            st.session_state.chat_messages.append(assistant_msg)

        self._trim_history()

    def _trim_history(self):
        """Keep chat history within configured limit (pairs)."""
        max_pairs = max(1, getattr(Config, "MAX_CHAT_HISTORY", 50))
        max_msgs = max_pairs * 2
        if len(st.session_state.chat_messages) > max_msgs:
            st.session_state.chat_messages = st.session_state.chat_messages[-max_msgs:]

    # Legacy/compat helper (kept for backward compat)
    def _save_message(self, user_message: str, response: Dict[str, Any]):
        """
        Backwards-compatible method — not used by new send flow but kept if other
        parts of app still call it.
        """
        timestamp = datetime.now().isoformat()

        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": timestamp,
            "agent": None
        }

        assistant_msg = {
            "role": "assistant",
            "content": response.get("response", ""),
            "timestamp": response.get("timestamp", timestamp),
            "agent": response.get("agent_used", "auto"),
            "metadata": response.get("metadata", {})
        }

        st.session_state.chat_messages.extend([user_msg, assistant_msg])
        self._trim_history()

    # -------------------------
    # Other utilities
    # -------------------------
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get formatted chat history"""
        return st.session_state.chat_messages

    def clear_chat_history(self):
        """Clear current chat history"""
        st.session_state.chat_messages = []
        st.session_state.current_session_id = str(uuid.uuid4())

    def export_chat_history(self, format: str = "json") -> str:
        """Export chat history in specified format"""
        history = self.get_chat_history()

        if format == "json":
            return json.dumps(history, indent=2, ensure_ascii=False)
        elif format == "txt":
            lines = []
            for msg in history:
                agent_info = f" ({msg['agent']})" if msg.get('agent') else ""
                lines.append(f"[{msg['timestamp']}] {msg['role'].upper()}{agent_info}: {msg['content']}")
            return "\n\n".join(lines)
        elif format == "md":
            lines = ["# Chat History\n"]
            for msg in history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                agent_info = f" ({msg['agent']})" if msg.get('agent') else ""
                lines.append(f"## {role}{agent_info}\n")
                lines.append(f"*{msg['timestamp']}*\n")
                lines.append(f"{msg['content']}\n")
            return "\n".join(lines)

        return ""

    def get_agent_info(self, agent_type: str) -> Dict[str, str]:
        """Get information about an agent"""
        return Config.AGENTS.get(agent_type, Config.AGENTS.get("auto", {"icon": "🤖", "name": "Auto"}))

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active chat sessions"""
        # This would query backend for sessions
        # For now, return current session
        return [{
            "id": st.session_state.current_session_id,
            "created": datetime.now().isoformat(),
            "message_count": len(st.session_state.chat_messages) // 2
        }]

    def switch_session(self, session_id: str):
        """Switch to different chat session"""
        # This would load session from backend
        # For now, just update current session ID and clear messages for the session
        st.session_state.current_session_id = session_id
        st.session_state.chat_messages = []

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to suggest best agent"""
        query_lower = query.lower()

        financial_keywords = ['financial', 'simple','llm']
        # sql_keywords = ['employee', 'salary', 'department', 'database', 'query', 'table', 'select']
        # web_keywords = ['latest', 'news', 'current', 'today', 'update', 'search']

        scores = {
            "financial": sum(1 for kw in financial_keywords if kw in query_lower),
            # "sql": sum(1 for kw in sql_keywords if kw in query_lower),
            # "web": sum(1 for kw in web_keywords if kw in query_lower)
        }

        best_agent = max(scores, key=scores.get)
        confidence = scores[best_agent] / max(len(query.split()), 1)

        return {
            "suggested_agent": best_agent if confidence > 0.2 else "auto",
            "confidence": confidence,
            "scores": scores
        }

# singleton
chat_service = ChatService()
