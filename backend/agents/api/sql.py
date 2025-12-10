from fastapi import APIRouter, HTTPException
from models.schemas import SQLRequest, SQLResponse

router = APIRouter()

@router.post("/sql", response_model=SQLResponse)
async def sql_endpoint(request: SQLRequest):
    """Execute SQL query"""
    try:
        # Mock execution
        return SQLResponse(
            result=f"Đã thực thi truy vấn: {request.query}",
            sql_query=request.query,
            row_count=5
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))