import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages



# 为什么 sources、tool_calls、logs 用 Reducer
# sources: Annotated[list[SourceInfo], operator.add]
# tool_calls: Annotated[list[ToolCallInfo], operator.add]
# logs: Annotated[list[str], operator.add]
# errors: Annotated[list[str], operator.add]

# 原因是这些字段可能由多个节点追加。如果不用 reducer，后面的更新可能覆盖前面的数据。
# query_order_node 追加一次 tool_call
# retrieve_policy_node 追加一次 source
# generate_answer_node 追加一条 log
# error_handler_node 追加一条 error




# 订单查询或物流查询返回的信息。
# total=False 表示其中的字段都是可选的。
class OrderInfo(TypedDict, total=False):
    order_id: str
    status: str
    status_text: str
    tracking_company: str | None
    tracking_no: str | None
    latest_event: str | None


# RAG（检索增强生成）返回的来源信息。
# 可以用来说明回答依据了哪个文档、片段，以及相关度分数。
class SourceInfo(TypedDict, total=False):
    document_id: str
    chunk_id: str
    source: str
    content_preview: str
    score: float


# 工具调用记录，例如调用订单查询或物流查询工具的结果摘要。
class ToolCallInfo(TypedDict, total=False):
    name: str
    args: dict
    id: str
    success: bool
    result_preview: str


class EcommerceAgentState(TypedDict):
    # 输入和对话历史
    user_question: str
    # add_messages 是 LangGraph 的消息合并函数：
    # 新消息会追加到消息列表；对于具有相同 ID 的消息，也支持更新。
    messages: Annotated[list[AnyMessage], add_messages]

    # 意图分类结果
    # 下游节点可据此决定进入订单查询、物流、退款等处理流程。
    intent: Literal[
        "general",
        "query_order",
        "logistics",
        "refund",
        "after_sales",
        "human_service",
        "unknown",
    ]

    # 从用户问题中提取的订单号和运单号；未提取到时可为 None。
    order_id: str | None
    tracking_no: str | None

    # 业务工具查询结果
    order_info: OrderInfo | None
    # 物流接口返回的数据结构尚未细分，所以暂时使用 dict。
    logistics_info: dict | None

    # RAG 检索相关信息
    # policy_query 是用于检索的查询文本。
    policy_query: str | None
    # policy_answer 是根据检索到的政策内容生成的答案。
    policy_answer: str | None
    # operator.add 表示多个节点写入的来源列表会拼接起来。
    sources: Annotated[list[SourceInfo], operator.add]

    # 风险判断与人工确认
    risk_level: Literal["low", "medium", "high"]
    need_human_confirm: bool
    # 需要确认的待执行动作，例如退款或修改订单。
    pending_action: str | None

    # 执行过程记录
    # operator.add 表示不同节点产生的记录会追加，而不是覆盖。
    tool_calls: Annotated[list[ToolCallInfo], operator.add]
    logs: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]

    # 最终输出
    final_answer: str
    # 标记当前流程是否已经结束。
    is_finished: bool