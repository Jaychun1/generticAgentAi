import streamlit as st
import pandas as pd
from datetime import datetime
import json

from config import Config
from services.api_client import api_client


def show_documents_page():
    """Display documents management page"""
    
    st.header("📁 Document Management")
    st.markdown("Upload, manage, and query financial documents")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📚 Library", "🔍 Query"])
    
    with tab1:
        # Document upload interface
        st.subheader("Upload Documents")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose files",
                type=Config.SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                help=f"Supported formats: {', '.join(Config.SUPPORTED_FILE_TYPES)}"
            )
        
        with col2:
            # Upload settings
            st.markdown("### Upload Settings")
            
            chunk_size = st.slider(
                "Chunk Size (characters)",
                min_value=500,
                max_value=2000,
                value=1000,
                step=100,
                help="Smaller chunks for detailed analysis, larger for context"
            )
            
            chunk_overlap = st.slider(
                "Chunk Overlap",
                min_value=50,
                max_value=500,
                value=200,
                step=50,
                help="Overlap between chunks for better context"
            )
        
        # Metadata form
        st.markdown("### Document Metadata")
        
        with st.form("metadata_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                company = st.text_input("Company Name", placeholder="e.g., amazon")
                doc_type = st.selectbox(
                    "Document Type",
                    ["10-k", "10-q", "8-k", "other", "annual report", "quarterly report"]
                )
            
            with col2:
                fiscal_year = st.number_input(
                    "Fiscal Year",
                    min_value=2000,
                    max_value=2030,
                    value=datetime.now().year
                )
                quarter = st.selectbox(
                    "Quarter",
                    ["Q1", "Q2", "Q3", "Q4", "Annual"]
                )
            
            with col3:
                source = st.text_input("Source", placeholder="e.g., SEC Edgar")
                language = st.selectbox("Language", ["English", "Vietnamese", "Other"])
            
            tags = st.multiselect(
                "Tags",
                ["financial", "earnings", "risk", "governance", "sustainability", "technology"],
                default=["financial"]
            )
            
            additional_notes = st.text_area("Additional Notes", height=100)
            
            submit_button = st.form_submit_button("🚀 Upload Documents")
        
        # Handle upload
        if submit_button and uploaded_files:
            total_files = len(uploaded_files)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            error_files = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {i+1}/{total_files}: {uploaded_file.name}")
                
                try:
                    # Prepare metadata
                    metadata = {
                        "company_name": company.lower() if company else "unknown",
                        "doc_type": doc_type,
                        "fiscal_year": fiscal_year,
                        "fiscal_quarter": quarter if quarter != "Annual" else None,
                        "source": source,
                        "language": language,
                        "tags": tags,
                        "notes": additional_notes,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                    
                    # Upload file
                    result = api_client.upload_document(
                        uploaded_file.getvalue(),
                        uploaded_file.name,
                        metadata
                    )
                    
                    if "error" in result:
                        error_files.append((uploaded_file.name, result["error"]))
                    else:
                        success_count += 1
                        
                        # Add to session state
                        if 'uploaded_documents' not in st.session_state:
                            st.session_state.uploaded_documents = []
                        
                        st.session_state.uploaded_documents.append({
                            "filename": uploaded_file.name,
                            "document_id": result.get("document_id"),
                            "metadata": metadata,
                            "upload_time": datetime.now().isoformat()
                        })
                
                except Exception as e:
                    error_files.append((uploaded_file.name, str(e)))
                
                # Update progress
                progress_bar.progress((i + 1) / total_files)
            
            # Show results
            status_text.empty()
            
            if success_count > 0:
                st.success(f"Successfully uploaded {success_count}/{total_files} files")
            
            if error_files:
                st.error(f"Failed to upload {len(error_files)} files")
                with st.expander("Error Details"):
                    for filename, error in error_files:
                        st.write(f"**{filename}**: {error}")
    
    with tab2:
        # Document library
        st.subheader("Document Library")
        
        # Refresh button
        if st.button("🔄 Refresh Library"):
            st.rerun()
        
        # Get documents from API
        with st.spinner("Loading documents..."):
            result = api_client.list_documents()
            
            if "error" in result:
                st.error(f"Failed to load documents: {result['error']}")
            else:
                documents = result.get("documents", [])
                
                if documents:
                    st.info(f"📚 Found {len(documents)} documents")
                    
                    # Display as table
                    df_data = []
                    for doc in documents:
                        df_data.append({
                            "ID": doc.get("document_id", "")[:8] + "...",
                            "Filename": doc.get("filename", ""),
                            "Company": doc.get("metadata", {}).get("company_name", ""),
                            "Type": doc.get("metadata", {}).get("doc_type", ""),
                            "Year": doc.get("metadata", {}).get("fiscal_year", ""),
                            "Chunks": doc.get("chunks_created", 0),
                            "Uploaded": doc.get("upload_time", "")[:10]
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Document actions
                        st.subheader("Document Actions")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            selected_doc = st.selectbox(
                                "Select Document",
                                [doc["filename"] for doc in documents]
                            )
                        
                        with col2:
                            action = st.selectbox(
                                "Action",
                                ["Query", "Delete", "View Metadata", "Download Info"]
                            )
                        
                        with col3:
                            if st.button("Execute Action"):
                                if action == "Query":
                                    st.session_state.selected_doc_for_query = selected_doc
                                    st.rerun()
                                elif action == "Delete":
                                    st.warning(f"Delete {selected_doc}? This action cannot be undone.")
                                elif action == "View Metadata":
                                    doc_metadata = next((d for d in documents if d["filename"] == selected_doc), {})
                                    st.json(doc_metadata.get("metadata", {}))
                                elif action == "Download Info":
                                    doc_info = next((d for d in documents if d["filename"] == selected_doc), {})
                                    st.download_button(
                                        "📥 Download",
                                        json.dumps(doc_info, indent=2),
                                        f"{selected_doc}_info.json",
                                        "application/json"
                                    )
                else:
                    st.info("No documents found. Upload some documents to get started.")
    
    with tab3:
        # Document query interface
        st.subheader("Query Documents")
        
        # Get documents for selection
        result = api_client.list_documents()
        documents = result.get("documents", []) if "error" not in result else []
        
        if documents:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Document selection
                selected_docs = st.multiselect(
                    "Select Documents to Query",
                    [doc["filename"] for doc in documents],
                    default=[st.session_state.get('selected_doc_for_query')] if st.session_state.get('selected_doc_for_query') else None
                )
                
                # Query input
                query = st.text_area(
                    "Enter your question about the selected documents:",
                    height=100,
                    placeholder="Example: 'What were the main risks mentioned in these documents?'",
                    help="Ask specific questions about the document content"
                )
            
            with col2:
                # Query settings
                st.markdown("### Query Settings")
                
                max_results = st.slider(
                    "Max Results",
                    min_value=1,
                    max_value=10,
                    value=3
                )
                
                similarity_threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="Higher values return more relevant but fewer results"
                )
            
            if st.button("🔍 Query Documents", type="primary") and selected_docs and query:
                # For each selected document, query it
                for doc_name in selected_docs:
                    doc = next((d for d in documents if d["filename"] == doc_name), {})
                    doc_id = doc.get("document_id")
                    
                    if doc_id:
                        with st.expander(f"📄 {doc_name}", expanded=len(selected_docs) == 1):
                            with st.spinner(f"Querying {doc_name}..."):
                                result = api_client.query_document(doc_id, query)
                                
                                if "error" in result:
                                    st.error(f"Error: {result['error']}")
                                else:
                                    st.markdown("### Answer")
                                    st.write(result.get("answer", "No answer found"))
                                    
                                    if result.get("sources"):
                                        st.markdown("### 📌 Sources")
                                        for i, source in enumerate(result.get("sources", []), 1):
                                            with st.expander(f"Source {i}"):
                                                st.text(source.get("content", "")[:500] + "...")
        else:
            st.info("No documents available. Please upload documents first.")

def show_document_stats():
    """Show document statistics"""
    pass