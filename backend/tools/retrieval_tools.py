import os
from langchain_core.tools import tool
from utils import extract_filters, generate_ranking_keywords, search_docs, rank_documents_by_keywords

@tool
def retrieve_docs(query:str, k=5):
    """
    Retrieve relevant financial documents from ChromaDB.
    Extracts filters from query and retrieves matching documents.

    Args:
        query: The search query (e.g., "What was Amazon's revenue in Q2 2025?")
        k: Number of documents to retrieve. generally prefer 5 docs

    Returns:
        Retrieved documents with metadata as formatted string
    """
    print(f"\n[TOOL] retrieve_docs called")
    print(f"[QUERY] {query}")

    filters = extract_filters(query)
    ranking_keywords = generate_ranking_keywords(query)
    
    # fetch more docs than needed for better re-ranking
    results = search_docs(query, filters, ranking_keywords, k=10*k)

    # rank retrieved docs
    docs = rank_documents_by_keywords(results, ranking_keywords, k=k)

    print(f"[RETRIEVED] {len(docs)} documents")

    # format extracted docs or chunks
    if len(docs)==0:
        return f"No documents found for the query: '{query}'. Try rephrasing query or use different filter."
    
    # final format
    # --- Document {i} ---
    retrieved_text = []
    for i, doc in enumerate(docs, 1):
        doc_text = [f"--- Document {i} ---"]

        # add all metadata
        for key, value in doc.metadata.items():
            doc_text.append(f"{key}: {value}")

        # add content
        doc_text.append(f"\nContent:\n{doc.page_content}")

        text = "\n".join(doc_text)
        retrieved_text.append(text)

    retrieved_text = "\n".join(retrieved_text)

    os.makedirs("debug_logs", exist_ok=True)
    with open("debug_logs/retrieved_reranked_docs.md", "w", encoding='utf-8') as f:
        f.write(retrieved_text)

    return retrieved_text