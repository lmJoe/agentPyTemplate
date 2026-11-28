from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.langgraph_persistence.service import langgraph_persistence_service
from app.schemas.response import ApiResponse
from app.schemas.user import CurrentUser


# 创建 API 路由器，之后需要由 FastAPI 应用注册
router = APIRouter()


# 两个接口的用途
# - POST /langgraph/persistence/chat：接收用户问题和会话 ID，继续该会话的 LangGraph 流程，并返回回答、意图、订单信息及是否需要用户补充信息等字段。
# - GET /langgraph/persistence/state/{conversation_id}：根据会话 ID、租户 ID 和当前登录用户，读取该会话保存的状态。


class PersistenceChatRequest(BaseModel):
    # 用户本轮输入；不能为空
    question: str = Field(..., min_length=1)

    # 会话 ID；不能为空，用于定位已有的对话线程
    conversation_id: str = Field(..., min_length=1)

    # 租户 ID；请求未提供时使用默认值
    tenant_id: str = Field(default="tenant_001")


@router.post(
    "/langgraph/persistence/chat",
    response_model=ApiResponse[dict],
)
async def persistence_chat(
    request: PersistenceChatRequest,
    # 通过依赖项获取当前登录用户
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[dict]:
    # 将用户消息交给持久化服务，继续对应会话的流程。
    # user_id 来自已认证的用户信息，而不是请求体。
    result = langgraph_persistence_service.continue_flow(
        user_question=request.question,
        tenant_id=request.tenant_id,
        user_id=current_user.user_id,
        conversation_id=request.conversation_id,
    )

    # 将图执行结果整理成 API 响应数据
    return ApiResponse[dict](
        data={
            "answer": result["final_answer"],
            "intent": result["intent"],
            "order_id": result["order_id"],
            "order_status": result["order_status"],
            "need_user_input": result["need_user_input"],
            "waiting_for": result["waiting_for"],
            "logs": result["logs"],
        }
    )


@router.get(
    "/langgraph/persistence/state/{conversation_id}",
    response_model=ApiResponse[dict],
)
async def get_persistence_state(
    # 从 URL 路径中获取会话 ID
    conversation_id: str,

    # 从查询参数中读取租户 ID；未提供时使用默认值
    tenant_id: str = "tenant_001",

    # 获取当前登录用户
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[dict]:
    # 根据租户、当前用户和会话 ID 查询该会话状态
    result = langgraph_persistence_service.get_current_state(
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        conversation_id=conversation_id,
    )

    # 将查询结果包装成统一的 API 响应
    return ApiResponse[dict](
        data=result
    )