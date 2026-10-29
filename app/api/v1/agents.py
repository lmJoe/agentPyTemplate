from fastapi import APIRouter,Depends
from pydantic import BaseModel, Field

from app.schemas.response import ApiResponse
# 引入 agent的上下文的类get_agent_context
from app.dependencies.agent_context import AgentContext, get_agent_context

router = APIRouter()

# 定义了一个“运行 Agent”的 FastAPI 接口。它接收用户问题和 Agent ID，并通过依赖注入取得当前用户、追踪 ID、调试开关，最后返回模拟的 Agent 回答



class AgentRunRequest(BaseModel):
    question: str = Field(...,min_length=1,description="用户问题")
    agent_id: str = Field(default="agent_chat", description="Agent ID")


class AgentRunResponse(BaseModel):
    answer: str = Field(...,description="Agent 回答")
    trace_id: str = Field(...,description="链路追踪ID")
    debug: bool = Field(default=False, description="是否开启调试模式")

# context: AgentContext = Depends(get_agent_context)
# 自动执行前面定义的 get_agent_context()
# 得到
# context.current_user  # 当前用户
# context.trace_id      # 本次请求追踪 ID
# context.debug         # ?debug=true/false

# 因此 ,完整的请求就是
# POST /agents/run?debug=true
# x-user-id: u_001
# x-username: alice
# Content-Type: application/json

# {
#   "question": "什么是 AI Agent？"
# }

@router.post("/agents/run", response_model=ApiResponse[AgentRunResponse])
async def run_agents(
    request:AgentRunRequest,
    context:AgentContext = Depends(get_agent_context)
) -> ApiResponse[AgentRunResponse]:
    answer = (
        f"用户 {context.current_user.username} 调用了 {request.agent_id}"
        f"问题是:{request.question}"
    )
    return ApiResponse[AgentRunResponse](
        data=AgentRunResponse(
            answer=answer,
            trace_id=context.trace_id,
            debug=context.debug
        )
    )

# 调用run_agents的链路
# POST /api/v1/agents/run?debug=true
# 请求头：
#   x-user-id: u_001
#   x-username: alice
# 请求体：
#   {
#     "question": "什么是 AI Agent？",
#     "agent_id": "agent_chat"
#   }
#     │
#     ▼
# FastAPI 匹配路由
# @router.post("/agents/run")
#     │
#     ▼
# 解析并校验 Body
# AgentRunRequest
#   ├─ question：必填，长度至少 1
#   └─ agent_id：未传时默认 agent_chat
#     │
#     ▼
# 解析 run_agents 的依赖
# Depends(get_agent_context)
#     │
#     ▼
# 执行 get_agent_context()
#   ├─ Depends(get_current_user)
#   │    ├─ 从请求头读取 x-user-id
#   │    ├─ 从请求头读取 x-username
#   │    ├─ 构造 CurrentUser
#   │    └─ 缺少用户信息则返回 401
#   │
#   ├─ 从 Query 读取 debug=true
#   └─ UUID 生成 trace_id，例如 trace_a1b2c3d4
#     │
#     ▼
# 生成 AgentContext
#   ├─ current_user = alice
#   ├─ trace_id = trace_a1b2c3d4
#   └─ debug = True
#     │
#     ▼
# 调用 run_agents(request, context)
#     │
#     ▼
# 当前代码拼接模拟回答
# “用户 alice 调用了 agent_chat，问题是：什么是 AI Agent？”
#     │
#     ▼
# 构造 AgentRunResponse
#   ├─ answer
#   ├─ trace_id
#   └─ debug
#     │
#     ▼
# 使用 ApiResponse 包装并返回 JSON