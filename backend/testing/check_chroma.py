# File: check_chroma.py
import sys
sys.path.append('backend')

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

try:
    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    vector_store = Chroma(
        collection_name='financial_docs',
        embedding_function=embeddings,
        persist_directory='chroma_financial_db'
    )
    
    # Kiểm tra số lượng documents
    count = vector_store._collection.count()
    print(f"📊 Total documents in ChromaDB: {count}")
    
    # Thử search
    if count > 0:
        results = vector_store.similarity_search("amazon", k=2)
        print(f"🔍 Sample results (2):")
        for i, doc in enumerate(results):
            print(f"  {i+1}. Metadata: {doc.metadata}")
            print(f"     Content preview: {doc.page_content[:100]}...")
    else:
        print("⚠️ ChromaDB is empty! Need to upload documents.")
        
except Exception as e:
    print(f"Error: {e}")