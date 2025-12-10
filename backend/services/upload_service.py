import os
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from tools.document_processor import DocumentUploader as BaseUploader
from langchain_ollama import ChatOllama

class DocumentUploader(BaseUploader):
    """Extended document uploader with metadata management"""
    
    def __init__(self):
        super().__init__()
        self.metadata_dir = Path("document_metadata")
        self.metadata_dir.mkdir(exist_ok=True)
        self.llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")
    
    def save_metadata(self, doc_id: str, filename: str, result: Dict[str, Any]):
        """Save document metadata to file"""
        metadata = {
            "document_id": doc_id,
            "filename": filename,
            "upload_time": datetime.now().isoformat(),
            "chunks_created": result.get("chunks_created"),
            "metadata": result.get("metadata", {}),
            "processed": True
        }
        
        metadata_file = self.metadata_dir / f"{doc_id}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def list_uploaded_documents(self) -> List[Dict]:
        """List all uploaded documents with metadata"""
        documents = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                documents.append(metadata)
        
        return documents
    
    def query_document_by_id(self, document_id: str, query: str) -> Dict[str, Any]:
        """Query a document by its ID"""
        metadata_file = self.metadata_dir / f"{document_id}.json"
        
        if not metadata_file.exists():
            return {"error": "Document not found"}
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # For now, use a simple approach
        # In production, you'd want to search the vector store for this specific document
        return {
            "document_id": document_id,
            "query": query,
            "metadata": metadata,
            "answer": f"Query for document {metadata['filename']}: {query}"
        }