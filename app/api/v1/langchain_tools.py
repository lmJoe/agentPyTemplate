from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.langchain_tools.registry import langchain_tool_registry
from app.langchain_tools.service import langchain_tool_calling_service
from app.schemas.response import ApiResponse
from app.schemas.user import CurrentUser


router = APIRouter()

# 请求数据模型
# 定义聊天接口的请求格式：
# - question：必填，至少一个字符。
# - provider：可选，默认 "deepseek"。
# - model：可选，默认 "deepseek-chat"。
# FastAPI 会用这个 Pydantic 模型解析并校验请求体。
class LangChainToolChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")
    provider: str = Field(default="deepseek", description="模型供应商")
    model: str = Field(default="deepseek-chat", description="模型名称")


# 获取所有注册的工具信息
# 这个接口从 langchain_tool_registry 获取已注册工具，把每个工具整理成包含名称、用途说明和参数信息的字典，再放入 ApiResponse 返回。
@router.get(
    "/langchain/tools",
    response_model=ApiResponse[list[dict]],
)
async def list_langchain_tools(
    # 表示请求需要经过 get_current_user 依赖，通常用于验证登录用户；成功后，当前用户信息会传给 current_user。这段代码本身没有使用 current_user 的值。
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[list[dict]]:
    tools = langchain_tool_registry.list()

    return ApiResponse[list[dict]](
        data=[
            {
                "name": item.name,
                "description": item.description,
                "args": item.args,
            }
            for item in tools
        ]
    )

# 跨境电商客服助手服务接口
# 请求体示例
# {
#   "question": "帮我查一下订单 10001 到哪了？",
#   "provider": "deepseek",
#   "model": "deepseek-chat"
# }
@router.post(
    "/langchain/tools/chat",
    response_model=ApiResponse[dict],
)
async def langchain_tool_chat(
    request: LangChainToolChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[dict]:
    # 接口把请求参数传给 service：service 负责调用模型、按需执行工具并生成回答。路由再把结果包装成 ApiResponse[dict] 返回。
    result = await langchain_tool_calling_service.run_ecommerce_customer_service(
        user_question=request.question,
        provider=request.provider,
        model_name=request.model,
    )

    return ApiResponse[dict](
        data=result
    )