from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
import os

from .retrieve_node import route_after_retrieve
from .response_cache import get_quick_response
from tools.retrieval_tools import retrieve_docs
from models.schemas import (
    GradeDocuments, GradeHallucinations, 
    GradeAnswer, SearchQueries, RouterDecision
)

LLM_MODEL = "qwen3"
BASE_URL = "http://localhost:11434"
llm = ChatOllama(model=LLM_MODEL, base_url=BASE_URL, reasoning=True)

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    retrieved_docs: str
    rewritten_queries: List[str]
    transform_count: int  
    max_transforms: int  

# Reuse the self_rag implementation from original code
def create_self_rag():
    """Create self-RAG agent for financial documents với fix infinite loop"""
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node('retrieve', retrieve_node)
    builder.add_node('route_after_retrieve', lambda state: state)
    builder.add_node('grade_documents', grade_documents_node)
    builder.add_node('generate', generate_node)
    builder.add_node('transform_query', transform_query_node)

    # Define edges
    builder.add_edge(START, 'retrieve')
    builder.add_edge('retrieve', 'route_after_retrieve')
    builder.add_edge('transform_query', 'retrieve')

    # Conditional routing từ route_after_retrieve
    builder.add_conditional_edges(
        'route_after_retrieve',
        route_after_retrieve,  # Sử dụng function đã fix
        {
            'grade_documents': 'grade_documents',
            'generate': 'generate',
            'transform_query': 'transform_query'
        }
    )
    
    # Conditional edges từ grade_documents
    builder.add_conditional_edges(
        'grade_documents',
        should_generate,
        ['transform_query', 'generate']
    )
    
    # Conditional edges từ generate
    builder.add_conditional_edges(
        'generate',
        check_answer_quality,
        ['generate', END, 'transform_query']
    )

    return builder.compile()


class MainAgentState(TypedDict):
    messages: Annotated[List, operator.add]
    retrieved_docs: str
    rewritten_queries: List[str]
    next_node: str

def create_main_agent():
    """Create main routing agent"""
    from langgraph.graph import StateGraph, START, END
    
    builder = StateGraph(MainAgentState)
    
    # Define nodes
    builder.add_node("route", route_node)
    builder.add_node("financial_agent", financial_agent_node)
    builder.add_node("sql_agent", sql_agent_node)
    builder.add_node("web_agent", web_agent_node)
    
    # Define edges
    builder.add_edge(START, "route")
    
    builder.add_conditional_edges(
        "route",
        lambda state: state.get("next_node", "financial_agent"),
        {
            "financial_agent": "financial_agent",
            "sql_agent": "sql_agent",
            "web_agent": "web_agent"
        }
    )
    
    builder.add_edge("financial_agent", END)
    builder.add_edge("sql_agent", END)
    builder.add_edge("web_agent", END)
    
    return builder.compile()

def route_node(state: MainAgentState):
    """Route query to appropriate agent"""
    query = state["messages"][-1].content
    
    llm_structured = llm.with_structured_output(RouterDecision)
    decision = llm_structured.invoke(query)
    
    return {"next_node": decision.agent}

def route_query(query: str) -> str:
    """Route a query to appropriate agent (standalone function)"""
    llm_structured = llm.with_structured_output(RouterDecision)
    decision = llm_structured.invoke(query)
    return decision.agent

def financial_agent_node(state: MainAgentState):
    """Handle financial document queries"""
    self_rag = create_self_rag()
    self_rag_state = {
        "messages": state["messages"],
        "retrieved_docs": state.get("retrieved_docs", ""),
        "rewritten_queries": state.get("rewritten_queries", []),
        "transform_count": 0,  # Khởi tạo = 0
        "max_transforms": 3    # Giới hạn tối đa
    }
    
    result = self_rag.invoke(self_rag_state)    
    return {"messages": result["messages"]}

def sql_agent_node(state: MainAgentState):
    """Handle SQL database queries"""
    from .sql_service import create_sql_agent
    sql_agent = create_sql_agent()   
    return sql_agent(state)

def web_agent_node(state: MainAgentState):
    """Handle web search queries"""
    from .search_service import create_web_agent
    web_agent = create_web_agent()
    return web_agent(state)

# Copy all self-RAG helper functions from original code
def get_latest_user_query(messages: list):
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return messages[0].content if messages else ''

def retrieve_node(state):
    print("[RETRIEVE] fetching documents...")
    query = get_latest_user_query(state['messages'])
    
    # Kiểm tra transform count
    transform_count = state.get('transform_count', 0)
    print(f"[DEBUG] Transform count: {transform_count}")
    
    # Check if we should retrieve documents
    if not should_retrieve_documents(query):
        print(f"[RETRIEVE] Skipping retrieval for simple query: '{query}'")
        return {'retrieved_docs': "SKIPPED_FOR_SIMPLE_QUERY"}
    
    # Nếu đã transform quá nhiều mà vẫn không có docs, dừng lại
    if transform_count >= 3:
        print(f"[RETRIEVE] Transform limit reached ({transform_count}), returning empty")
        return {'retrieved_docs': ''}
    
    rewritten_queries = state.get('rewritten_queries', [])
    queries_to_search = rewritten_queries if rewritten_queries else [query]

    all_results = []
    for idx, search_query in enumerate(queries_to_search, 1):
        print(f"[RETRIEVE] Query {idx}: {search_query}")
        result = retrieve_docs.invoke({'query': search_query, 'k': 3})
        
        # Kiểm tra xem có kết quả thực sự không
        if result and result.strip():
            text = f"## Query {idx}: {search_query}\n\n### Retrieved Documents:\n{result}"
            all_results.append(text)
        else:
            print(f"[RETRIEVE] No results for query: {search_query}")
    
    if all_results:
        combined_result = "\n\n".join(all_results)
        print(f"[RETRIEVE] Found {len(all_results)} result sets")
    else:
        combined_result = ''
        print("[RETRIEVE] No documents found for any query")

    return {'retrieved_docs': combined_result}

def grade_documents_node(state):
    print("[GRADE] Evaluating document relevance")
    query = get_latest_user_query(state['messages'])
    retrieved_docs = state.get('retrieved_docs', '')
    
    # Nếu là simple query, không cần grade
    if not should_retrieve_documents(query):
        print("[GRADE] Simple query - skipping grading")
        return {'retrieved_docs': ''}
    
    if not retrieved_docs or retrieved_docs.strip() == '':
        print("[GRADE] No documents to grade")
        return {'retrieved_docs': ''}
    
    llm_structured = llm.with_structured_output(GradeDocuments)

    system_prompt = """You are a grader assessing relevance of retrieved documents to a user query.
                It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
                If the document contains keyword(s) or semantic meaning related to the user query, grade it as relevant.
                Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the query."""
    
    system_msg = SystemMessage(system_prompt)
    messages = [system_msg, HumanMessage(f"Retrieved Document: {retrieved_docs}\n\nUser query: {query}")]

    response = llm_structured.invoke(messages)
    print(f"[GRADE] Relevance: {response.binary_score}")

    if response.binary_score == 'yes':
        return {'retrieved_docs': retrieved_docs}
    else:
        return {'retrieved_docs': ''}

def generate_node(state):
    print("[GENERATE] Creating Answer")
    query = get_latest_user_query(state['messages'])
    documents = state.get('retrieved_docs', '')
    
    # Check for quick response first
    quick_response = get_quick_response(query)
    if quick_response:
        print("[GENERATE] Using quick response")
        return {'messages': [AIMessage(content=quick_response)]}
    
    # Check if we have documents
    has_documents = documents and documents.strip() != ''
    
    if not has_documents:
        # Simple response for casual conversation
        system_prompt = """You are a helpful AI assistant. Respond to the user in a friendly and helpful manner.
        
        Guidelines:
        - Be concise and friendly
        - If it's a greeting, respond appropriately
        - If it's a question about what you can do, explain your capabilities
        - Keep responses under 100 words for casual conversation"""
    else:
        # Detailed response for document-based queries
        system_prompt = """You are a financial document analyst providing detailed, accurate answers.

        OUTPUT FORMAT:
        Write a comprehensive answer (200-300 words) in MARKDOWN format:
        - Use ## headings for sections
        - Use **bold** for emphasis
        - Use bullet points or numbered lists
        - Include inline citations like [1], [2] where applicable

        GUIDELINES:
        - Base your answer ONLY on the provided documents
        - Be specific with numbers, dates, and metrics
        - If information is missing, acknowledge it
        - Use proper financial terminology

        CITATIONS:
        At the end, list references in this format:
        **References:**
        1. Company: x, Year: y, Quarter: z, Page: n"""
    
    if has_documents:
        query_prompt = f"Retrieved Document: {documents}\n\nUser query: {query}"
    else:
        query_prompt = f"User query: {query}"

    system_msg = SystemMessage(system_prompt)
    user_msg = HumanMessage(query_prompt)
    messages = [system_msg, user_msg]

    response = llm.invoke(messages)

    os.makedirs('debug_logs', exist_ok=True)
    with open('debug_logs/self_rag_answer.md', 'w', encoding='utf-8') as f:
        f.write(f"Query: {query}")
        f.write(response.content)

    return {'messages': [response]}

def transform_query_node(state):
    """Transform query node với tracking transform count"""
    query = get_latest_user_query(state['messages'])
    rewritten_queries = state.get('rewritten_queries', [])
    
    # Lấy và tăng transform count
    transform_count = state.get('transform_count', 0)
    transform_count += 1
    
    print(f"[TRANSFORM] Transform attempt {transform_count}/3 for query: {query[:50]}...")
    
    # Nếu đã transform quá nhiều, trả về empty
    if transform_count > 3:
        print(f"[TRANSFORM] Max transforms reached ({transform_count}), returning empty")
        return {
            "rewritten_queries": [],
            "transform_count": transform_count
        }
    
    llm_structured = llm.with_structured_output(SearchQueries)

    system_prompt = """You are a query re-writer that decomposes complex queries into focused search queries optimized for vectorstore retrieval.

                GUIDELINES:
                - Generate 1-3 VERY SPECIFIC queries
                - Each query should target ONE specific aspect
                - Include specific financial terms if applicable
                - Make queries concise but clear
                - AVOID generating queries that have been tried before

                IMPORTANT: If the query seems too vague or cannot be improved, return an empty list [].
                
                EXAMPLES:
                - "tell me about revenue" → ["Amazon quarterly revenue 2023", "Microsoft annual revenue growth"]
                - "company financials" → ["Apple financial statements 2023", "Google balance sheet Q4 2023"]
                - "hi" → []  # Empty for greetings
                - "something in document" → []  # Too vague"""
    
    query_context = f"Original Query: {query}"
    if rewritten_queries:
        query_context = query_context + f"\n\nAlready tried queries (DO NOT REPEAT):\n"
        for idx, q in enumerate(rewritten_queries, 1):
            query_context = query_context + f"{idx}. {q}\n"
    
    system_msg = SystemMessage(system_prompt)
    user_msg = HumanMessage(query_context)
    messages = [system_msg, user_msg]
    
    try:
        response = llm_structured.invoke(messages)
        new_queries = response.search_queries
        
        # Lọc bỏ queries trùng
        all_queries = rewritten_queries + new_queries
        unique_queries = []
        seen = set()
        for q in all_queries:
            if q not in seen and q.strip():
                seen.add(q)
                unique_queries.append(q)
        
        print(f"[TRANSFORM] Generated {len(new_queries)} queries, total unique: {len(unique_queries)}")
        
        return {
            "rewritten_queries": unique_queries,
            "transform_count": transform_count
        }
        
    except Exception as e:
        print(f"[TRANSFORM] Error: {e}")
        return {
            "rewritten_queries": rewritten_queries,
            "transform_count": transform_count
        }
    
def should_generate(state):
    print("[ROUTER] Assess graded documents")
    query = get_latest_user_query(state['messages'])
    retrieved_docs = state.get('retrieved_docs', '')
    transform_count = state.get('transform_count', 0)
    
    # Kiểm tra xem có skip retrieval không
    if retrieved_docs == "SKIPPED_FOR_SIMPLE_QUERY":
        print('[ROUTER] Simple query - generating answer directly')
        return 'generate'
    
    # Kiểm tra transform limit
    if transform_count >= 3:
        print(f"[ROUTER] Transform limit reached ({transform_count}) - generating anyway")
        return 'generate'
    
    if not retrieved_docs or retrieved_docs.strip() == '':
        print(f"[ROUTER] No relevant documents - transforming query (attempt {transform_count + 1})")
        return 'transform_query'
    else:
        print('[ROUTER] Have relevant documents - generating answer')
        return 'generate'

def check_answer_quality(state: AgentState):
    """Check answer quality node - với transform limit"""
    try:
        print("[ROUTER] Check answer quality - START")
        
        query = get_latest_user_query(state['messages'])
        documents = state.get('retrieved_docs', '')
        transform_count = state.get('transform_count', 0)
        
        # Debug info
        print(f"[DEBUG] Query: '{query}'")
        print(f"[DEBUG] Transform count: {transform_count}")
        
        # Nếu không có messages, kết thúc
        if not state.get('messages') or len(state['messages']) == 0:
            print("[ROUTER] No messages, ending")
            return END
        
        # Kiểm tra transform limit
        if transform_count >= 3:
            print(f"[ROUTER] Max transforms reached ({transform_count}), ending")
            return END
        
        # Xử lý simple query đã skip retrieval
        if documents == "SKIPPED_FOR_SIMPLE_QUERY":
            print("[ROUTER] Simple query (skip retrieval), auto-ending")
            return END
        
        # Nếu documents rỗng và query đơn giản
        if (not documents or documents.strip() == '') and not should_retrieve_documents(query):
            print("[ROUTER] Simple query without docs, auto-ending")
            return END
        
        # Nếu không có documents sau nhiều lần transform
        if (not documents or documents.strip() == '') and transform_count > 0:
            print(f"[ROUTER] No docs after {transform_count} transforms, ending")
            return END
        
        # Lấy generation từ message cuối cùng
        last_message = state['messages'][-1]
        if hasattr(last_message, 'content'):
            generation = last_message.content
        else:
            generation = str(last_message)
        
        # Nếu là casual conversation, auto-end
        simple_keywords = ["hi", "hello", "hey", "thanks", "bye", "ok", "yes", "no"]
        if any(keyword in query.lower() for keyword in simple_keywords):
            print("[ROUTER] Simple conversation detected, auto-ending")
            return END
        
        # Nếu answer quá ngắn hoặc là apology, có thể cần transform lại
        if len(generation) < 50 and "sorry" in generation.lower():
            print("[ROUTER] Short apology answer, transforming query")
            return "transform_query"
        
        # Default: answer is good
        print('[ROUTER] Answer seems acceptable, ending')
        return END
        
    except Exception as e:
        print(f"[ROUTER] Error in check_answer_quality: {str(e)}")
        import traceback
        traceback.print_exc()
        return END

def should_retrieve_documents(query: str) -> bool:
    """Determine if we should retrieve documents for this query - IMPROVED"""
    query_lower = query.lower().strip()
    
    # Simple greetings and casual questions - don't retrieve
    simple_phrases = [
        "hi", "hello", "hey", "hi there", "hello there",
        "how are you", "how are you doing", "what's up",
        "good morning", "good afternoon", "good evening",
        "thanks", "thank you", "bye", "goodbye",
        "who are you", "what can you do", "help", 
        "who created you", "what is your name",
        "ok", "okay", "yes", "no", "maybe"
    ]
    
    # Very vague queries about documents
    vague_doc_phrases = [
        "tell me something in your document",
        "what's in your document",
        "show me your document",
        "document content",
        "what documents do you have",
        "your documents"
    ]
    
    # Check for simple greetings
    if query_lower in simple_phrases:
        return False
    
    # Check for vague document queries
    if any(phrase in query_lower for phrase in vague_doc_phrases):
        return False  # Không retrieve vì quá vague
    
    # Check for very short vague queries
    if len(query.split()) <= 3:
        vague_words = ['document', 'something', 'anything', 'tell', 'show', 'what']
        if any(word in query_lower for word in vague_words):
            return False
    
    # Keywords that indicate document retrieval is needed
    financial_keywords = ['revenue', 'profit', 'earnings', 'financial', 'sec', 'filing', 
                         'quarter', 'annual', 'report', 'balance', 'cash flow', 'income',
                         'statement', 'ebitda', 'margin', 'growth']
    
    sql_keywords = ['employee', 'salary', 'department', 'database', 'query', 'table', 
                   'select', 'employees', 'hr', 'human resources', 'sql', 'query']
    
    specific_keywords = financial_keywords + sql_keywords
    
    # Nếu có từ khóa cụ thể, retrieve
    if any(keyword in query_lower for keyword in specific_keywords):
        return True
    
    # Câu hỏi bắt đầu bằng what/how về số liệu cụ thể
    if query_lower.startswith(('what is', 'how much', 'how many', 'what are')):
        number_words = ['revenue', 'profit', 'salary', 'employees', 'cost', 'price']
        if any(word in query_lower for word in number_words):
            return True
    
    # Default: don't retrieve để tránh loop
    return False