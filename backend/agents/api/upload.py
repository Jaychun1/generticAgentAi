from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
import tempfile
import os

from services.upload_service import DocumentUploader

router = APIRouter()
uploader = DocumentUploader()

class UploadResponse(BaseModel):
    status: str
    document_id: str
    file_name: str
    chunks_created: Optional[int]
    metadata: Optional[Dict[str, Any]]

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = None
) -> UploadResponse:
    """Upload and process a document"""
    try:
        # Parse metadata
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Save file temporarily
        temp_file = None
        try:
            # Create temp file with proper extension
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_file = tmp.name
            
            # Process document
            result = uploader.process_document(temp_file, metadata_dict)
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Save metadata
            uploader.save_metadata(doc_id, file.filename, result)
            
            return UploadResponse(
                status="success",
                document_id=doc_id,
                file_name=file.filename,
                chunks_created=result.get("chunks_created"),
                metadata=result.get("metadata")
            )
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@router.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = uploader.list_uploaded_documents()
        return {
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.post("/query")
async def query_document(document_id: str, query: str):
    """Query a specific document"""
    try:
        result = uploader.query_document_by_id(document_id, query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")