from fastapi import APIRouter, Path, Query, Body, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.response import ApiResponse
from app.service.chat_service import chat_with_ai

from app.dependencies.auth import get_current_user

from app.schemas.user import CurrentUser
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from redis.asyncio import Redis
from app.dependencies.redis import get_redis_client
from app.llm.base import BaseLLMProvider
from app.dependencies.llm import get_llm_provider

router = APIRouter()

# response_model 用于告诉 FastAPI：这个接口最终返回的数据，必须符合 ChatResponse 这个 Pydantic 模型定义。
# 校验返回数据是否符合规定的字段和类型
# 将返回对象序列化为 JSON。
# 自动生成 Swagger / OpenAPI 文档中的响应结构

# current_user: CurrentUser = Depends(get_current_user) 注入的是“当前请求用户”的身份信息
# 它会从请求头读取:
# x-user-id: u_001
# x-username: alice
# 并生成
# CurrentUser(
#     user_id="u_001",
#     username="alice",
#     role=UserRole.USER,
#     is_active=True,
# )
# 然后把该对象传给接口中的 current_user 参数。如果请求头缺少x-user-id 或 x-username,依赖函数会抛出401,chat就不会执行,这就是它同时承担获取当前用户和简单认证校验的原因
@router.post("/chat",response_model=ApiResponse)
async def chat(
    request:ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db:AsyncSession = Depends(get_db_session),
    redis:Redis = Depends(get_redis_client),
    llm_provider:BaseLLMProvider = Depends(get_llm_provider)
) -> ApiResponse:
    res = await chat_with_ai(request,db,redis,llm_provider)

    # 在原有链路追踪 ID 后面追加当前用户 ID
    # 例如:
    # res.trace_id == "trace_a1b2c3d4"
    # current_user.user_id == "u_001"
    # 执行后 trace_a1b2c3d4*user*u_001
    # 这样在日志或接口响应中看到该 trace_id 时，可以知道这次 AI 调用属于哪个用户，方便排查问题

    res.trace_id = f"{res.trace_id}_user_{current_user.user_id}"
    return ApiResponse[ChatResponse](
        data = res
    )

# 接口 query+path+body 混合使用
# conversation_id: str = Path(...) 是 Path 参数
# debug: bool = Query(default=False, ...) 是 Query 参数
# request: ChatRequest 是 Body 参数

@router.post('/conversations/{conversation_id}/chat', response_model=ApiResponse[ChatResponse])
async def chat_in_conversation(
    request: ChatRequest, 
    conversation_id: str = Path(...,description="会话ID"),
    debug: bool = Query(default=False,description="是否开启调试模式")
) -> ApiResponse[ChatResponse]:
    res = await chat_with_ai(request)
    if debug:
        res.trace_id = res.trace_id or "debug_trace"
    res.session_id = conversation_id
    
    return ApiResponse[ChatResponse](
        data=res
    )

@router.post("/title")
async def title(message:str = Body(..., embed = True, min_length=1, description="消息内容")):
    return {
        "title":message[:20]
    }


@router.post("/chat/di-demo", response_model=ApiResponse[ChatResponse])
async def chat_di_demo(
       request:ChatRequest,
       current_user:CurrentUser = Depends(get_current_user),
       llm_provider:BaseLLMProvider = Depends(get_llm_provider) 
) -> ApiResponse[ChatResponse]:
    latest_message = request.messages[-1].content

    answer = await llm_provider.chat(
        message = f"用户{current_user.username} 问:{latest_message}"
    )
    result = ChatResponse(
        answer=answer,
        model=llm_provider.model,
        session_id=request.session_id
    )

    return ApiResponse[ChatResponse](
        data=result
    )