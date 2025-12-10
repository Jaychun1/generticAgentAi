from typing import Optional


def get_quick_response(query: str) -> Optional[str]:
    """Get quick response text for common queries"""
    query_lower = query.lower().strip()
    
    QUICK_RESPONSES = {
        "hi": "Hello! 👋 I'm your AI assistant. How can I help you today?",
        "hello": "Hi there! 😊 I'm ready to assist you with financial analysis, database queries, or web searches. What would you like to know?",
        "hey": "Hey! 👋 What can I do for you today?",
        "how are you": "I'm doing great, thanks for asking! Ready to help you with any questions you might have.",
        "what can you do": "I can help you with:\n\n• **Financial Analysis**: SEC filings, revenue reports, earnings data\n• **SQL Queries**: Employee database, salary information, HR data\n• **Web Search**: Latest news, current information, trends\n\nJust ask me anything!",
        "who are you": "I'm an AI assistant specializing in financial analysis, SQL database queries, and web searches. I can help you find and analyze information from various sources.",
        "thank you": "You're welcome! 😊 Let me know if you need anything else.",
        "thanks": "No problem! Happy to help. 👍",
        "bye": "Goodbye! 👋 Have a great day!",
        "goodbye": "See you later! 😊 Take care!"
    }
    
    # Exact matches
    if query_lower in QUICK_RESPONSES:
        return QUICK_RESPONSES[query_lower]
    
    # Partial matches
    for key, response in QUICK_RESPONSES.items():
        if key in query_lower:
            return response
    
    # Very short queries (1-2 words) that aren't specific
    if len(query_lower.split()) <= 2:
        # Check if it's not asking for specific information
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        if not any(query_lower.startswith(word) for word in question_words):
            return "Hi there! 👋 How can I assist you today?"
    
    return None