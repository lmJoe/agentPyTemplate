import operator
from typing import Annotated, Literal, TypedDict


class OrderInfo(TypedDict, total=False):
    """订单查询结果；total=False 表示所有字段都可以省略。"""

    order_id: str
    status: str
    status_text: str

    # 物流信息可能暂时没有，因此值可以是 None。
    tracking_company: str | None
    tracking_no: str | None
    latest_event: str | None


class SourceInfo(TypedDict, total=False):
    """知识库检索结果的来源信息。"""

    document_id: str
    chunk_id: str
    source: str
    content_preview: str
    score: float


class ToolCallInfo(TypedDict, total=False):
    """一次工具调用的名称、参数、执行结果等信息。"""

    name: str
    args: dict
    id: str
    success: bool
    result_preview: str


class EcommerceNodeEdgeState(TypedDict):
    """电商客服 LangGraph 节点之间传递的共享状态。"""

    # 用户输入的问题。
    user_question: str

    # 意图分类结果，只能是列出的几种类型之一。
    intent: Literal[
        "general",
        "query_order",
        "logistics",
        "refund",
        "human_service",
        "unknown",
    ]

    # 从问题中提取的订单号，以及订单查询结果。
    order_id: str | None
    order_info: OrderInfo | None

    # 售后政策检索所用的查询，以及生成或检索到的答案。
    policy_query: str | None
    policy_answer: str | None

    # 检索到的资料来源。
    # operator.add 指定多个节点返回的来源列表会拼接起来。
    sources: Annotated[list[SourceInfo], operator.add]

    # 风险评估与人工确认相关状态。
    need_human_confirm: bool
    risk_level: Literal["low", "medium", "high"]
    pending_action: str | None

    # 工具调用记录。
    # operator.add 表示新记录追加到列表中，而非覆盖已有记录。
    tool_calls: Annotated[list[ToolCallInfo], operator.add]

    # 节点执行日志和错误信息，也采用追加方式合并。
    logs: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]

    # 最终给用户的答复。
    final_answer: str

    # 流程重试次数，可用于限制重复尝试。
    retry_count: int

    # 标记整个处理流程是否已经完成。
    is_finished: bool