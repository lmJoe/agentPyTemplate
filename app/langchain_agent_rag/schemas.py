from typing import Any

from pydantic import BaseModel, Field


class AgentRAGMessageItem(BaseModel):
    """表示 Agent 执行过程中的一条消息。"""

    # 消息类型，例如 system、user、assistant 或 tool。
    # Field(...) 表示该字段必填。
    type: str = Field(..., description="消息类型")

    # 消息正文，未提供时默认为空字符串。
    content: str = Field(default="", description="消息内容")

    # 工具名称；普通消息可能没有工具名称，因此允许为 None。
    name: str | None = Field(default=None, description="工具名称")

    # 当前消息关联的工具调用列表。
    # 使用 default_factory=list，确保每个实例都有独立的列表。
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="工具调用列表",
    )

    # 工具返回消息对应的工具调用 ID；不适用时为 None。
    tool_call_id: str | None = Field(
        default=None,
        description="工具调用 ID",
    )


class AgentRAGSource(BaseModel):
    """表示知识库检索结果中的一个引用来源。"""

    # 来源文档的唯一标识；没有时为 None。
    document_id: str | None = Field(default=None)

    # 文档切片（chunk）的标识；没有时为 None。
    chunk_id: str | None = Field(default=None)

    # 来源名称、路径或其他来源信息；没有时为 None。
    source: str | None = Field(default=None)

    # 引用内容的预览文本，未提供时默认为空字符串。
    content_preview: str = Field(default="")


class AgentRAGRunResponse(BaseModel):
    """表示一次 Agent + RAG 执行完成后的整体响应。"""

    # Agent 最终生成的回答；必填。
    answer: str = Field(..., description="最终回答")

    # 标记本次执行是否调用过工具。
    used_tools: bool = Field(
        default=False,
        description="是否使用了工具",
    )

    # 标记本次执行是否使用了知识库检索（RAG）。
    used_rag: bool = Field(
        default=False,
        description="是否使用了知识库检索",
    )

    # 本次执行涉及的工具调用详情。
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="工具调用列表",
    )

    # Agent 执行期间产生的消息记录。
    messages: list[AgentRAGMessageItem] = Field(
        default_factory=list,
        description="Agent 执行消息",
    )

    # 回答中引用的知识库来源。
    sources: list[AgentRAGSource] = Field(
        default_factory=list,
        description="知识库引用来源",
    )

    # 其他扩展信息，例如耗时、模型名称或调试信息。
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="扩展信息",
    )