from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.langchain_agent_rag.schemas import AgentRAGRunResponse
from app.langchain_agent_rag.service import langchain_agent_rag_service
from app.schemas.response import ApiResponse
from app.schemas.user import CurrentUser


# 创建路由对象，供应用主路由注册。
router = APIRouter()


class AgentRAGChatRequest(BaseModel):
    """定义电商客服 Agent + RAG 接口的请求参数。"""

    # 用户的问题必填，长度至少为 1。
    question: str = Field(..., min_length=1, description="用户问题")

    # 模型供应商；请求中未提供时使用 deepseek。
    provider: str = Field(default="deepseek", description="模型供应商")

    # 模型名称；请求中未提供时使用 deepseek-chat。
    model: str = Field(default="deepseek-chat", description="模型名称")


# 注册 POST 接口，并声明响应的数据结构。
@router.post(
    "/langchain/agent-rag/ecommerce/chat",
    response_model=ApiResponse[AgentRAGRunResponse],
)
async def ecommerce_agent_rag_chat(
    request: AgentRAGChatRequest,
    # 通过依赖项验证当前用户身份。
    # 即使函数中暂时没有直接使用 current_user，该依赖仍会执行。
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[AgentRAGRunResponse]:
    """接收用户问题，调用 Agent + RAG 服务并返回结果。"""

    # 将请求参数传给服务层，异步等待 Agent 执行完成。
    result = await langchain_agent_rag_service.run_ecommerce_agent_rag(
        user_question=request.question,
        provider=request.provider,
        model_name=request.model,
    )

    # 使用统一 API 响应格式返回 Agent 的执行结果。
    return ApiResponse[AgentRAGRunResponse](
        data=result
    )