import operator
from typing import Annotated, Literal, TypedDict

# 公共 State

# 订单信息；total=False 表示其中所有字段都是可选的。
class OrderInfo(TypedDict, total=False):
    order_id: str                  # 订单编号
    status: str                    # 订单状态代码或状态值
    status_text: str               # 订单状态的可读说明
    tracking_company: str | None   # 物流公司；None 表示未知或暂缺
    tracking_no: str | None        # 物流单号；None 表示未知或暂缺
    latest_event: str | None       # 最近一条物流动态；None 表示暂无


# 检索到的来源片段信息。
class SourceInfo(TypedDict, total=False):
    document_id: str      # 来源文档编号
    chunk_id: str          # 文档切片编号
    source: str            # 来源名称、路径或链接
    content_preview: str   # 来源内容的简短预览
    score: float           # 检索相关度分数


# 一次工具调用的记录。
class RoutingToolCall(TypedDict, total=False):
    name: str           # 工具名称
    args: dict          # 调用参数
    success: bool       # 调用是否成功
    result_preview: str # 调用结果的简短预览


# 对话路由流程中共享的状态。
# 默认情况下字段都是必填项；实例化 RoutingState 时应提供每个字段。
class RoutingState(TypedDict):
    user_question: str  # 用户原始问题

    # 识别出的意图，用 Literal 限定为以下值之一。
    intent: Literal[
        "general",       # 一般咨询
        "query_order",   # 查询订单
        "logistics",     # 查询物流
        "refund",        # 退款
        "after_sales",   # 售后
        "human_service", # 转人工
        "unknown",       # 无法识别
    ]

    order_id: str | None         # 识别出的订单编号；未识别时为 None
    order_info: OrderInfo | None # 查询到的订单信息；尚未查询或无结果时为 None

    need_policy: bool         # 是否需要查询政策或知识库
    policy_query: str | None  # 用于查询政策的问题；不需要查询时为 None
    policy_answer: str | None # 政策查询结果；尚无结果时为 None

    # 来源列表。Annotated 元数据表示在支持该约定的状态框架中，
    # 更新此字段时用 operator.add 合并新旧列表（即列表拼接）。
    sources: Annotated[list[SourceInfo], operator.add]

    tool_success: bool # 工具调用整体是否成功

    # 工具调用记录列表；通常按列表拼接的方式累积记录。
    tool_calls: Annotated[list[RoutingToolCall], operator.add]

    rag_hit: bool          # 检索增强生成（RAG）是否命中相关内容
    need_human_confirm: bool # 是否需要人工确认后再继续
    risk_level: Literal["low", "medium", "high"] # 当前操作的风险级别
    pending_action: str | None # 等待执行或确认的动作；无待办时为 None

    retry_count: int # 当前已重试次数
    max_retry: int   # 允许的最大重试次数

    final_answer: str # 面向用户的最终回复
    is_finished: bool # 流程是否结束

    # 日志和错误列表同样按 operator.add 所代表的加法约定累积。
    logs: Annotated[list[str], operator.add]   # 流程日志
    errors: Annotated[list[str], operator.add] # 流程中发生的错误