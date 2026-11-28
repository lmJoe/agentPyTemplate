import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages

# PersistenceState 用来规定 LangGraph 工作流中的状态数据结构。图中的节点可以读取这些字段，并返回需要更新的字段。例如：
# - 意图识别节点更新 intent。
# - 订单查询节点更新 order_status。
# - 信息收集节点设置 need_user_input 和 waiting_for。
# - 回复节点填写 final_answer，并用 is_finished 表示流程是否结束。
# - 各节点产生的日志和错误分别写入 logs、`errors`。

def create_initial_state(user_question: str) -> dict:
    return {
        "user_question": user_question,
        "messages": [HumanMessage(content=user_question)],
        "intent": "unknown",
        "order_id": None,
        "order_status": None,
        "policy_answer": None,
        "need_user_input": False,
        "waiting_for": None,
        "final_answer": "",
        "is_finished": False,
        "logs": [],
        "errors": [],
    }

class PersistenceState(TypedDict):
    # 用户当前提出的问题
    user_question: str

    # 对话消息列表；使用 add_messages 合并新消息，
    # 支持按 LangGraph 的消息规则处理消息追加和更新
    messages: Annotated[list[AnyMessage], add_messages]

    # 意图分类结果，只允许使用以下几种值
    intent: Literal[
        "general",       # 一般咨询
        "refund",        # 退款相关
        "query_order",   # 查询订单
        "human_service", # 转人工客服
        "unknown",       # 暂时无法识别
    ]

    # 订单编号；尚未获取时可以为 None
    order_id: str | None

    # 订单状态；尚未查询到时可以为 None
    order_status: str | None

    # 根据业务政策生成的答复；尚未生成时可以为 None
    policy_answer: str | None

    # 是否需要向用户补充收集信息
    need_user_input: bool

    # 需要等待的用户输入内容，例如“订单编号”
    waiting_for: str | None

    # 流程最终返回给用户的答复
    final_answer: str

    # 流程是否已经结束
    is_finished: bool

    # 日志列表；使用 operator.add 将各节点产生的日志追加合并
    logs: Annotated[list[str], operator.add]

    # 错误信息列表；使用 operator.add 将各节点产生的错误追加合并
    errors: Annotated[list[str], operator.add]