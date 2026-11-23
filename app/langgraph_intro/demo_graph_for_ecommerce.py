from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


# 定义电商客服工作流的状态结构。

class EcommerceGraphState(TypedDict):
    """定义电商客服工作流中共享的状态结构。"""

    user_question: str          # 用户提出的问题
    intent: str                 # 问题意图：refund、order 或 general
    order_id: str | None        # 提取到的订单号；未识别到时为 None
    order_status: str | None    # 查询到的订单状态
    policy_answer: str | None   # 根据订单状态得到的退款规则说明
    final_answer: str           # 最终返回给用户的回复


def classify_intent_node(state: EcommerceGraphState) -> dict:
    """根据问题中的关键词识别用户意图。"""
    question = state["user_question"]

    # 退款关键词优先判断，退款问题也可能同时提到订单
    if "退款" in question:
        return {"intent": "refund"}

    # 提到订单或物流时，归类为订单查询
    if "订单" in question or "物流" in question:
        return {"intent": "order"}

    # 没有匹配到上述关键词时，按普通问题处理
    return {"intent": "general"}


def extract_order_id_node(state: EcommerceGraphState) -> dict:
    """从用户问题中查找示例支持的订单号。"""
    question = state["user_question"]

    # 当前示例只识别两个写死的订单号
    if "10001" in question:
        return {"order_id": "10001"}

    if "10002" in question:
        return {"order_id": "10002"}

    # 没有找到订单号时，将订单号设为 None
    return {"order_id": None}


def route_after_extract_order_id(
    state: EcommerceGraphState,
) -> Literal["ask_order_id", "query_order"]:
    """检查是否提取到订单号，决定询问用户还是查询订单。"""
    if not state.get("order_id"):
        return "ask_order_id"

    return "query_order"


def query_order_node(state: EcommerceGraphState) -> dict:
    """模拟查询订单系统，并返回对应的订单状态。"""
    order_id = state["order_id"]

    # 这里用固定数据模拟订单查询结果
    if order_id == "10001":
        return {"order_status": "已发货"}

    if order_id == "10002":
        return {"order_status": "已付款，待发货"}

    # 未匹配到已知订单时返回未查询到
    return {"order_status": "未查询到订单"}


def retrieve_policy_node(state: EcommerceGraphState) -> dict:
    """根据订单状态查找对应的退款规则说明。"""
    order_status = state.get("order_status")

    if order_status == "已付款，待发货":
        return {
            "policy_answer": "根据售后规则，订单未发货时可以申请取消订单并退款。"
        }

    if order_status == "已发货":
        return {
            "policy_answer": "根据售后规则，订单已发货后，需要收到商品后再发起退货退款申请。"
        }

    # 状态未知或订单未查询到时，建议交由人工客服确认
    return {
        "policy_answer": "当前状态无法确认退款规则，建议转人工客服。"
    }


def ask_order_id_node(state: EcommerceGraphState) -> dict:
    """订单号缺失时，请用户补充订单号。"""
    return {
        "final_answer": "请您提供订单号，我帮您继续查询和判断。"
    }


def generate_general_answer_node(state: EcommerceGraphState) -> dict:
    """生成普通问题的回复。"""
    return {
        "final_answer": "这是一个普通问题，可以走普通 Chat。"
    }


def generate_order_answer_node(state: EcommerceGraphState) -> dict:
    """生成订单查询问题的回复。"""
    return {
        "final_answer": f"您的订单当前状态是：{state.get('order_status')}。"
    }


def generate_refund_answer_node(state: EcommerceGraphState) -> dict:
    """组合订单状态和退款规则，生成退款问题的回复。"""
    return {
        "final_answer": (
            f"您的订单当前状态是：{state.get('order_status')}。"
            f"{state.get('policy_answer')}"
        )
    }


def route_by_intent(
    state: EcommerceGraphState,
) -> Literal["general", "order_or_refund"]:
    """按意图决定走普通问答分支，还是订单处理分支。"""
    if state["intent"] == "general":
        return "general"

    # 订单查询和退款请求都需要先提取订单号
    return "order_or_refund"


def route_after_query_order(
    state: EcommerceGraphState,
) -> Literal["retrieve_policy", "generate_order_answer"]:
    """订单查询完成后，退款请求继续查规则，普通订单查询直接回复。"""
    if state["intent"] == "refund":
        return "retrieve_policy"

    return "generate_order_answer"


def build_graph():
    """创建并编译电商客服工作流。"""
    graph = StateGraph(EcommerceGraphState)

    # 注册工作流中的处理节点
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("ask_order_id", ask_order_id_node)
    graph.add_node("generate_general_answer", generate_general_answer_node)
    graph.add_node("generate_order_answer", generate_order_answer_node)
    graph.add_node("generate_refund_answer", generate_refund_answer_node)

    # 工作流从意图识别开始
    graph.add_edge(START, "classify_intent")

    # 意图分类后，普通问题直接回答；订单和退款问题进入订单处理流程
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "generate_general_answer",
            "order_or_refund": "extract_order_id",
        },
    )

    # 提取订单号后，缺少订单号时询问用户，否则查询订单
    graph.add_conditional_edges(
        "extract_order_id",
        route_after_extract_order_id,
        {
            "ask_order_id": "ask_order_id",
            "query_order": "query_order",
        },
    )

    # 查询订单后，退款请求查退款规则；普通订单问题直接生成回复
    graph.add_conditional_edges(
        "query_order",
        route_after_query_order,
        {
            "retrieve_policy": "retrieve_policy",
            "generate_order_answer": "generate_order_answer",
        },
    )

    # 退款规则查询完成后，生成最终退款回复
    graph.add_edge("retrieve_policy", "generate_refund_answer")

    # 以下节点完成后，工作流结束
    graph.add_edge("ask_order_id", END)
    graph.add_edge("generate_general_answer", END)
    graph.add_edge("generate_order_answer", END)
    graph.add_edge("generate_refund_answer", END)

    # 编译图，得到可调用的工作流应用
    return graph.compile()


def main():
    """运行几个示例问题，并打印处理结果。"""
    app = build_graph()

    # 覆盖普通问题、订单查询、退款咨询和缺少订单号的情况
    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单 10002 还没发货，可以退款吗？",
        "我要退款，但是忘记订单号了。",
    ]

    for question in questions:
        # 每次调用都传入一份初始状态
        result = app.invoke({
            "user_question": question,
            "intent": "",
            "order_id": None,
            "order_status": None,
            "policy_answer": None,
            "final_answer": "",
        })

        # 打印用户问题、最终回复和完整工作流状态
        print("question:", question)
        print("final_answer:", result["final_answer"])
        print("full_state:", result)
        print("=" * 80)


# 直接运行此文件时执行示例；被导入时不自动运行
if __name__ == "__main__":
    main()