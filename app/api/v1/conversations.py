from fastapi import APIRouter, Path, Depends
from redis.asyncio import Redis
from app.schemas.conversation import (
  ConversationCreateRequest,
  ConversationMessagesResponse,
  ConversationResponse
)

from app.schemas.response import ApiResponse
from app.schemas.user import CurrentUser
from app.service.conversation_service import(
  create_conversation as create_conversation_service,
  get_conversation as get_conversation_service
)

from app.dependencies.database import get_db_session
from app.dependencies.redis import get_redis_client
from app.dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.pagination import PaginationParams

router = APIRouter()

# 创建新会话
@router.post(
    "/conversations",
    response_model=ApiResponse[ConversationResponse] # 声明接口返回的数据结构，用于校验和生成 Swagger 文档。
)
async def create_conversation(
  request: ConversationCreateRequest, 
  db:AsyncSession = Depends(get_db_session),
  current_user:CurrentUser = Depends(get_current_user)
) -> ApiResponse[ConversationResponse]:
  
  result = await create_conversation_service(db, request, current_user.user_id)
  return ApiResponse[ConversationResponse](data=result) # 把实际创建结果包装成统一响应格式再返回

# 根据会话 ID 查询会话
@router.get("/conversations/{conversation_id}",response_model=ApiResponse[ConversationMessagesResponse])
async def get_conversation(
  conversation_id: str = Path(...,description="会话ID"), # Path(...) 中的 ... 表示此参数必传；description 用于 Swagger 文档说明。
  db:AsyncSession = Depends(get_db_session),
  redis:Redis=Depends(get_redis_client)
) -> ApiResponse[ConversationMessagesResponse]:
  result = await get_conversation_service(db,conversation_id,redis) # 调用业务层/服务层函数，根据 ID 查找会话
  return ApiResponse[ConversationMessagesResponse](data=result)


@router.get('/conversations', response_model=ApiResponse[dict])
async def list_conversations(
      pagination:PaginationParams = Depends(PaginationParams)
) -> ApiResponse[dict]:
    return ApiResponse[dict](data={
      "page":pagination.page,
      "page_size":pagination.size,
      "offset":pagination.offset,
      "items":[]
    })
