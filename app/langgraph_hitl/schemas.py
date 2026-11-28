import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages


class RefundOrderInfo(TypedDict, total=False):
    """退款流程中使用的订单信息。所有字段都是可选的。"""

    order_id: str       # 订单编号
    status: str         # 订单状态代码
    status_text: str    # 订单状态的可读描述
    amount: float       # 订单金额
    currency: str       # 货币单位，例如 CNY


class HumanDecision(TypedDict, total=False):
    """人工审核员对待处理操作作出的决定。所有字段都是可选的。"""

    # 审核结果：批准、拒绝，或修改待执行内容
    type: Literal["approve", "reject", "edit"]

    reviewer_id: str                # 审核员标识
    reason: str | None               # 审核说明
    edited_payload: dict | None      # 审核员修改后的操作参数


class HITLState(TypedDict):
    """Human-in-the-Loop 流程在 LangGraph 中共享的状态结构。"""

    user_question: str  # 用户当前提出的问题

    # 对话消息列表。add_messages 会按 LangGraph 的规则合并消息；
    # 例如，向状态中追加新消息，而不是直接覆盖整个列表。
    messages: Annotated[list[AnyMessage], add_messages]

    # 用户意图，只能取以下值之一
    intent: Literal[
        "general",
        "refund",
        "query_order",
        "human_service",
        "unknown",
    ]

    order_id: str | None                   # 订单编号；尚未获取时为 None
    order_info: RefundOrderInfo | None     # 订单详情；尚未查询时为 None

    refund_amount: float | None            # 申请退款的金额
    refund_reason: str | None              # 申请退款的原因

    # 风险等级
    risk_level: Literal["low", "medium", "high"]

    need_human_confirm: bool   # 是否需要人工审核
    pending_action: str | None  # 等待审核的操作名称
    pending_payload: dict | None  # 待审核操作的参数

    human_decision: HumanDecision | None  # 人工审核结果
    action_result: dict | None            # 操作执行结果，例如退款接口的返回值

    final_answer: str  # 返回给用户的最终答复
    is_finished: bool  # 流程是否已经结束

    # operator.add 会将新日志追加到已有列表中
    logs: Annotated[list[str], operator.add]

    # 错误信息也采用追加方式保存
    errors: Annotated[list[str], operator.add]


def create_initial_state(user_question: str) -> HITLState:
    """根据用户问题创建 HITL 流程的初始状态。"""

    return {
        # 保存原始问题，并将其作为对话中的第一条用户消息
        "user_question": user_question,
        "messages": [HumanMessage(content=user_question)],

        # 意图尚未识别，等待后续节点分类
        "intent": "unknown",

        # 初始时还没有订单信息或退款申请详情
        "order_id": None,
        "order_info": None,
        "refund_amount": None,
        "refund_reason": None,

        # 默认风险较低，暂时不需要人工审核
        "risk_level": "low",
        "need_human_confirm": False,

        # 当前没有等待审核的操作
        "pending_action": None,
        "pending_payload": None,
        "human_decision": None,

        # 尚未执行操作
        "action_result": None,

        # 最终答复由后续节点生成，流程初始时尚未结束
        "final_answer": "",
        "is_finished": False,

        # 日志和错误列表从空列表开始
        "logs": [],
        "errors": [],
    }