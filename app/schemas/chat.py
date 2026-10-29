# 从 Pydantic 导入：
# BaseModel：定义请求、响应等数据模型
# Field：为字段设置默认值、校验规则和接口文档描述
# field_validator：自定义字段校验器
from enum import Enum
from typing import Any
from app.core.config import settings

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRole(str, Enum):
    SYSTEM = "system"  # 系统提示词
    USER = "user"  # 用户输入
    ASSISTANT = "assistant"  # AI 的回复
    TOOL = "tool"  # 工具调用结果


# Token 用量统计
class TokenUsage(BaseModel):
    # 用户输入给模型的内容所消耗的 Token 数量
    prompt_tokens: int = Field(default=0, ge=0, description="输入提示词消耗的 Token 数量")
    # 模型生成回答内容所消耗的 Token 数量
    completion_tokens: int = Field(default=0, ge=0, description="模型生成回答消耗的 Token 数量")
    # 本次调用消耗的 Token 总数，通常等于输入 Token 与输出 Token 之和
    total_tokens: int = Field(default=0, ge=0, description="本次请求消耗的 Token 总数")


# 知识库问答中的来源文档
class SourceDocument(BaseModel):
    # 文档的唯一标识，例如数据库主键或知识库中的文档 ID
    document_id: str = Field(..., min_length=1, max_length=500, description="文档唯一标识")
    # 文档标题，便于前端展示和用户识别来源
    title: str = Field(..., description="文档标题")
    # 文档正文或与当前问题最相关的内容片段
    content: str = Field(..., min_length=1, max_length=500, description="文档内容或召回的相关文本片段")
    # 文档与用户问题的相关性得分，范围为 0 到 1，值越大表示越相关
    score: float = Field(0.0, ge=0, le=1, description="文档与当前查询的相关性得分，取值范围为 0 到 1")
    # 文档的额外信息，例如来源链接、作者、创建时间、文件类型或所属知识库
    metadata: dict[str, Any] = Field(default_factory=dict, description="文档附加元数据，如来源链接、作者、创建时间和文件类型")


# 单条聊天消息
class ChatMessage(BaseModel):
    # 消息角色，例如 system、user、assistant、tool
    role: MessageRole = Field(..., description="消息角色类型")
    # 消息具体内容
    content: str = Field(..., min_length=1, max_length=500, description="消息内容")


# 定义聊天接口的请求数据结构
class ChatRequest(BaseModel):
    # Pydantic 模型禁止接收未声明的额外字段
    model_config = ConfigDict(extra="forbid")

    # 对话消息列表，至少需要有一条消息
    messages: list[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    # 要调用的模型名称；未传入时，默认使用 gpt-3.5-turbo
    model: str = Field("gpt-3.5-turbo", description="要使用的大模型名称")
    # 模型温度参数：值越低回答越稳定，值越高回答越有创造性
    temperature: float = Field(0.5, description="模型温度参数")
    # 是否以流式方式返回回答：False 为完整返回，True 为逐步返回
    stream: bool = Field(False, description="是否以流式方式返回响应")
    # 会话唯一标识，用于关联同一个用户的多轮对话
    session_id: str | None = Field(None, description="当前对话的会话唯一标识")
    # 用户唯一标识，用于识别当前请求来自哪个用户
    user_id: str | None = Field(None, description="当前用户的唯一标识")
    # 扩展元数据，可存放客户端、业务类型等额外信息
    metadata: dict[str, Any] = Field(default_factory=dict, description="请求扩展元数据")
    # 提示词
    prompt_scenario:str | None = Field(
        default=None,
        description="Prompt 场景，如 general_chat / ecommerce_customer_service / reg_qa"
    )
    # 对 model 字段进行自定义校验
    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:

        # 如果传入的模型不在配置文件中的支持列表中，抛出参数校验异常
        if value not in settings.supported_model_list:
            raise ValueError(f"Unsupported model: {value}")

        # 校验通过，返回模型名称
        return value


# 定义聊天接口的响应数据结构
class ChatResponse(BaseModel):
    # 大模型生成的最终回答内容；... 表示该字段必须提供
    answer: str = Field(..., description="大模型返回的回答内容")
    # 本次实际调用的大模型名称，例如 gpt-4、deepseek-chat
    model: str = Field(..., description="本次调用使用的模型名称")
    # 会话唯一标识，用于关联同一个用户的多轮对话
    session_id: str | None = Field(None, description="当前对话会话的唯一标识")
    # 当前消息的唯一标识，便于保存、查询或引用消息记录
    message_id: str | None = Field(None, description="当前消息的唯一标识")
    # 本次模型调用的 Token 用量统计，默认创建新的 TokenUsage 对象
    usage: TokenUsage = Field(default_factory=TokenUsage, description="本次模型调用的 Token 用量统计")
    # RAG 检索或知识库问答时，回答参考的来源文档列表
    sources: list[SourceDocument] = Field(default_factory=list, description="生成回答时引用的来源文档列表")
    # 链路追踪 ID，用于在日志和监控系统中定位完整调用过程
    trace_id: str | None = Field(None, description="请求链路追踪唯一标识")