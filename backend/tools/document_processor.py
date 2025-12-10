import os
from typing import Dict, Any, List
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils import embeddings, vector_store

class DocumentUploader:
    """Handle document uploads and processing."""
    
    def __init__(self):
        self.chroma_dir = "chroma_financial_db"
        self.collection_name = "financial_docs"
        self.embeddings = embeddings
        self.vector_store = vector_store
    
    def process_document(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process and index uploaded document."""
        # Determine loader based on file extension
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_ext == '.txt' or file_ext == '.md':
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_ext == '.csv':
            loader = CSVLoader(file_path)
        elif file_ext == '.docx':
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        documents = loader.load()
        
        if metadata:
            for doc in documents:
                doc.metadata.update({k: v for k, v in metadata.items() if v is not None})
                # Ensure required metadata fields
                doc.metadata.setdefault('company_name', 'unknown')
                doc.metadata.setdefault('doc_type', 'uploaded')
                doc.metadata.setdefault('source', Path(file_path).name)
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        self.vector_store.add_documents(splits)
        
        return {
            "file_name": Path(file_path).name,
            "chunks_created": len(splits),
            "total_pages": len(documents),
            "metadata": metadata
        }
    
    def list_uploaded_documents(self) -> List[Dict]:
        """List all uploaded documents."""
        # This would query the vector store for unique documents
        return []
    
    def query_document(self, document_path: str, query: str) -> Dict[str, Any]:
        """Query content from a document."""
        try:
            # Read document content
            content = self._read_document_content(document_path)
            
            # If vector store exists, search in it
            if hasattr(self, 'vector_store') and self.vector_store:
                # Search for relevant chunks
                results = self.vector_store.similarity_search(query, k=3)
                if results:
                    context = "\n".join([doc.page_content for doc in results])
                    answer = self._generate_answer(query, context)
                    return {
                        "answer": answer,
                        "sources": [{"content": doc.page_content[:200]} for doc in results]
                    }
            
            # Fallback: use entire content (limited length)
            max_length = 3000
            truncated_content = content[:max_length] + "..." if len(content) > max_length else content
            
            # Create prompt to answer based on content
            prompt = f"""Based on the following document content, answer this query: {query}
            
            Document Content:
            {truncated_content}
            
            Provide a clear and concise answer. If the content doesn't contain relevant information, say so."""
            
            # Use LLM to answer
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")
            response = llm.invoke(prompt)
            
            return {
                "answer": response.content,
                "sources": [{"content": truncated_content[:500]}]
            }
            
        except Exception as e:
            return {
                "answer": f"Error querying document: {str(e)}",
                "sources": []
            }
    
    def _read_document_content(self, file_path: str) -> str:
        """Read content from different file types."""
        import PyPDF2
        from docx import Document
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        elif file_ext == '.docx':
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
            
        elif file_ext == '.txt' or file_ext == '.md':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        elif file_ext == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_string()
            
        else:
            return f"Content from {file_ext} file (requires specific parsing)"
    
    def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM."""
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")
        prompt = f"""Based on the following context, answer this query: {query}
        
        Context:
        {context}
        
        Provide a clear and concise answer."""
        
        response = llm.invoke(prompt)
        return response.content