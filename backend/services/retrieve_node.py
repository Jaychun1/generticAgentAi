from utils.helpers import get_latest_user_query


from typing import Dict, Any
from utils.helpers import get_latest_user_query

def route_after_retrieve(state: Dict[str, Any]) -> str:
    """Decide where to go after retrieval - FIXED to prevent infinite loop"""
    query = get_latest_user_query(state['messages'])
    retrieved_docs = state.get('retrieved_docs', '')
    
    print(f"[ROUTER] Deciding next step after retrieval - Docs: {len(retrieved_docs) if retrieved_docs else 0} chars")
    
    if retrieved_docs == "SKIPPED_FOR_SIMPLE_QUERY":
        print("[ROUTER] Simple query (skipped) -> generate")
        return 'generate'
    
    if not should_retrieve_documents(query):
        print("[ROUTER] Not a document query -> generate")
        return 'generate'
    
    if retrieved_docs and retrieved_docs.strip() != '':
        print("[ROUTER] Has documents -> grade_documents")
        return 'grade_documents'
    
    transform_count = state.get('transform_count', 0)
    
    if transform_count >= 2:  # Giới hạn chỉ transform tối đa 2 lần
        print(f"[ROUTER] Transform limit reached ({transform_count}) -> generate")
        return 'generate'
    
    print(f"[ROUTER] No documents (transform {transform_count + 1}/2) -> transform_query")
    return 'transform_query'

def should_retrieve_documents(query: str) -> bool:
    """Determine if we should retrieve documents for this query"""
    query_lower = query.lower().strip()
    
    # Simple greetings and casual questions - don't retrieve
    simple_phrases = [
        "hi", "hello", "hey", "hi there", "hello there",
        "how are you", "how are you doing", "what's up",
        "good morning", "good afternoon", "good evening",
        "thanks", "thank you", "bye", "goodbye",
        "who are you", "what can you do", "help", 
        "who created you", "what is your name"
    ]
    
    # Check for simple greetings or short casual phrases
    if query_lower in simple_phrases:
        return False
    
    # Check for very short queries (likely casual conversation)
    if len(query.split()) <= 2:
        # Nhưng nếu là câu hỏi ngắn về tài chính/SQL/web thì vẫn retrieve
        financial_keywords = ['revenue', 'profit', 'salary', 'employee', 'news']
        sql_keywords = ['employee', 'salary', 'table', 'query']
        web_keywords = ['news', 'latest', 'today']
        
        if not any(keyword in query_lower for keyword in 
                   financial_keywords + sql_keywords + web_keywords):
            return False
    
    # Default to True for most queries
    return True