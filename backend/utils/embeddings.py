class MockEmbeddings:
    """Mock embeddings for demo purposes"""
    
    def embed_documents(self, texts):
        """Mock embedding function"""
        return [[0.1] * 384] * len(texts)  
    
    def embed_query(self, text):
        """Mock query embedding"""
        return [0.1] * 384

def get_embeddings():
    """Get embeddings instance (mock for now)"""
    return MockEmbeddings()