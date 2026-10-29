# 定义枚举类型
from enum import Enum

# Any 表示允许任意类型的数据，例如字符串、数字、列表、字典等
from typing import Any

# Pydantic：用于请求校验、响应序列化和自动生成接口文档
from pydantic import BaseModel, Field

# 定义大模型
class LLMProviderName(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"

# 定义大模型消息角色。
# 继承 str 后，枚举值能直接序列化为 JSON 字符串。
class LLMRole(str, Enum):
    SYSTEM = "system"        # 系统提示词
    ASSISTANT = "assistant"  # AI 回复
    USER = "user"            # 用户消息
    TOOL = "tool"            # 工具调用结果


# 表示一条发送给大模型的消息。
class LLMMessage(BaseModel):
    # ... 表示该字段必填
    role: LLMRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")


# 表示调用大模型时的请求体。
class LLMRequest(BaseModel):
    # 要调用的模型名称，例如 gpt-4o-mini
    model: str = Field(..., description="模型名称")

    # 消息列表；min_length=1 表示至少必须有一条消息
    messages: list[LLMMessage] = Field(
        ...,
        min_length=1,
        description="消息列表",
    )

    # 温度越高，回答通常越随机；0.7 是常见默认值
    temperature: float = Field(
        default=0.7,
        description="温度参数，控制随机性",
    )

    # 限制模型最多生成多少 Token；None 表示不在此处限制
    max_tokens: int | None = Field(
        default=None,
        description="最大生成 Token 数",
    )

    # 是否使用流式输出
    stream: bool = Field(
        default=False,
        description="是否流式返回",
    )

    # 额外信息，例如用户 ID、请求来源、业务标签。
    # default_factory=dict 避免不同请求共用同一个字典。
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="扩展消息",
    )


# 统计一次模型调用的 Token 用量。
class LLMUsage(BaseModel):
    prompt_tokens: int = Field(default=0, ge=0, description="输入 Token 数")
    completion_tokens: int = Field(default=0, ge=0, description="输出 Token 数")
    total_tokens: int = Field(default=0, ge=0, description="总 Token 数")


# 表示大模型调用后的响应。
class LLMResponse(BaseModel):

    provider:LLMProviderName = Field(..., description="模型供应商")

    # 实际使用的模型名称
    model: str = Field(..., description="模型名称")

    # 模型最终回复文本；流式响应或异常场景中可能暂时为空
    content: str = Field(
        ...,
        description="模型输出内容",
    )

    # 使用 LLMUsage，结构比 dict 更明确
    usage: LLMUsage = Field(
        default_factory=LLMUsage,
        description="Token 使用统计",
    )

    # 保存第三方大模型 SDK 的原始响应，便于排错
    raw_response: dict[str, Any] = Field(
        default_factory=dict,
        description="原始返回数据",
    )


class LLMStreamChunk(BaseModel):
    provider:LLMProviderName = Field(...,description="模型供应商")
    model:str= Field(..., description="模型名称")
    content:str = Field(default="",description="当前增量内容")
    finish_reason:str | None = Field(default=None, description="结束原因")
    usage:LLMUsage | None = Field(default=None,description="Token用量")
    raw_chunk:dict[str,Any]= Field(default_factory=dict, description="原始Chunk")


    
