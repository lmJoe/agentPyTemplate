from fastapi import APIRouter
from app.schemas.rag import RAGQueryResponse,RAGQueryRequest
from app.schemas.response import ApiResponse
from app.service.rag_service import query_rag

router = APIRouter()

@router.post("/rag/query", response_model=ApiResponse[RAGQueryResponse])
async def rag_query(
  request:RAGQueryRequest,
) -> ApiResponse[RAGQueryResponse]:
  result = await query_rag(request)
  return ApiResponse[RAGQueryResponse](
    data=result
  )