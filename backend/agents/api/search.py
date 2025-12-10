from fastapi import APIRouter, HTTPException
from models.schemas import SearchRequest, SearchResponse

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """Search web for information"""
    try:
        # Mock search results
        mock_results = [
            {
                "title": f"Kết quả 1 cho '{request.query}'",
                "snippet": "Đây là kết quả tìm kiếm mock...",
                "url": "https://example.com/result1",
                "source": "Mock Search"
            },
            {
                "title": f"Kết quả 2 cho '{request.query}'",
                "snippet": "Kết quả mock thứ hai...",
                "url": "https://example.com/result2",
                "source": "Mock Search"
            }
        ]
        
        return SearchResponse(
            results=mock_results[:request.num_results],
            query=request.query,
            total_results=len(mock_results),
            search_time=0.3
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))