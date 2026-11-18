from typing import Any

from pydantic import BaseModel, Field


# 定义 Agent 相关的请求和响应模型 返回结构


# 定义 Agent 消息项模型和 Agent 执行响应模型
class AgentMessageItem(BaseModel):
    type: str = Field(..., description="消息类型")
    content: str = Field(default="", description="消息内容")
    name: str | None = Field(default=None, description="工具名称或消息名称")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="工具调用列表",
    )
    tool_call_id: str | None = Field(
        default=None,
        description="工具调用 ID",
    )


# 定义 Agent 执行响应模型
class AgentRunResponse(BaseModel):
    answer: str = Field(..., description="最终回答")

    messages: list[AgentMessageItem] = Field(
        default_factory=list,
        description="Agent 执行过程中的消息列表",
    )

    used_tools: bool = Field(
        default=False,
        description="是否使用了工具",
    )

    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="执行过程中出现的工具调用",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="扩展信息",
    )


# 定义 Agent 流式事件模型
class AgentStreamEvent(BaseModel):
    event: str = Field(..., description="事件类型")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="事件数据",
    )