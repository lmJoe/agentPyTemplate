import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


# 这段代码用 LangGraph 实现了一个带有日志记录的电商客服流程：
# 1. 识别用户问题是普通聊天、订单查询还是退款咨询。
# 2. 对订单和退款问题提取订单号；没有订单号时请用户补充。
# 3. 根据订单号查询模拟的订单状态。
# 4. 对退款咨询，根据订单状态选择相应的售后规则并生成回复。
# 5. 通过 logs 收集每个节点的执行记录。
# 其中，`logs` 使用 Annotated[list[str], operator.add] 声明了 reducer，因此各节点返回的新日志会追加到列表中。当前订单数据和规则都是示例内容，没有连接真实业务系统。


class EcommerceCoreState(TypedDict):
    """定义电商客服工作流中共享的状态结构。"""

    user_question: str          # 用户提出的问题
    intent: str                 # 问题意图：general、order 或 refund
    order_id: str | None        # 提取出的订单号
    order_status: str | None    # 查询到的订单状态
    policy_type: str | None     # 根据订单状态判断出的售后规则类型
    policy_answer: str | None   # 查询到的售后规则说明
    final_answer: str           # 最终返回给用户的回答

    # operator.add 是 logs 字段的 reducer，用于累加各节点返回的日志列表
    logs: Annotated[list[str], operator.add]


def classify_intent_node(state: EcommerceCoreState) -> dict:
    """根据用户问题中的关键词识别意图。"""
    question = state["user_question"]

    if "退款" in question or "退货" in question:
        intent = "refund"
    elif "订单" in question or "物流" in question:
        intent = "order"
    else:
        intent = "general"

    return {
        "intent": intent,
        "logs": [f"classify_intent：识别意图为 {intent}"],
    }


def route_by_intent(
    state: EcommerceCoreState,
) -> Literal["general", "need_order"]:
    """决定普通问题直接回答，还是进入订单处理流程。"""
    if state["intent"] == "general":
        return "general"

    return "need_order"


def extract_order_id_node(state: EcommerceCoreState) -> dict:
    """从用户问题中提取示例支持的订单号。"""
    question = state["user_question"]

    # 示例只识别订单号 10001 和 10002
    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = None

    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：订单号为 {order_id}"],
    }


def route_after_extract_order_id(
    state: EcommerceCoreState,
) -> Literal["ask_order_id", "query_order"]:
    """提取订单号后，决定询问用户补充信息还是查询订单。"""
    if not state["order_id"]:
        return "ask_order_id"

    return "query_order"


def ask_order_id_node(state: EcommerceCoreState) -> dict:
    """没有提取到订单号时，请用户补充订单号。"""
    return {
        "final_answer": "请您提供订单号，我才能继续查询订单状态和售后规则。",
        "logs": ["ask_order_id：缺少订单号，追问用户。"],
    }


def query_order_node(state: EcommerceCoreState) -> dict:
    """模拟查询订单信息，并返回订单状态。"""
    order_id = state["order_id"]

    # 使用固定数据模拟订单系统的查询结果
    if order_id == "10001":
        order_status = "shipped"
        status_text = "已发货"
    elif order_id == "10002":
        order_status = "paid"
        status_text = "已付款，待发货"
    else:
        order_status = "not_found"
        status_text = "未查询到订单"

    return {
        "order_status": order_status,
        "logs": [f"query_order：订单状态为 {status_text}"],
    }


def route_after_query_order(
    state: EcommerceCoreState,
) -> Literal["retrieve_policy", "generate_order_answer"]:
    """订单查询完成后，决定是否需要继续查退款规则。"""
    if state["intent"] == "refund":
        return "retrieve_policy"

    return "generate_order_answer"


def decide_policy_type_node(state: EcommerceCoreState) -> dict:
    """根据订单状态判断适用的退款规则类型。"""
    order_status = state["order_status"]

    if order_status == "paid":
        policy_type = "refund_before_shipping"
    elif order_status == "shipped":
        policy_type = "refund_after_shipping"
    else:
        policy_type = "unknown"

    return {
        "policy_type": policy_type,
        "logs": [f"decide_policy_type：规则类型为 {policy_type}"],
    }


def retrieve_policy_node(state: EcommerceCoreState) -> dict:
    """根据规则类型生成对应的售后规则说明。"""
    policy_type = state["policy_type"]

    if policy_type == "refund_before_shipping":
        policy_answer = "根据售后规则，订单未发货时，用户可以申请取消订单并退款。"
    elif policy_type == "refund_after_shipping":
        policy_answer = "根据售后规则，订单已发货后，需要收到商品后再发起退货退款申请。"
    else:
        policy_answer = "当前状态无法从规则中确认，建议转人工客服。"

    return {
        "policy_answer": policy_answer,
        "logs": ["retrieve_policy：完成售后规则查询。"],
    }


def generate_general_answer_node(state: EcommerceCoreState) -> dict:
    """为普通问题生成回复。"""
    return {
        "final_answer": "这是普通问题，后续可以接入普通 ChatModel 生成回答。",
        "logs": ["generate_general_answer：普通回答完成。"],
    }


def generate_order_answer_node(state: EcommerceCoreState) -> dict:
    """将订单状态转换为用户可读文字并生成回复。"""
    order_status = state["order_status"]

    status_map = {
        "paid": "已付款，待发货",
        "shipped": "已发货",
        "not_found": "未查询到订单",
    }

    return {
        "final_answer": f"您的订单当前状态是：{status_map.get(order_status, '未知')}。",
        "logs": ["generate_order_answer：订单回答完成。"],
    }


def generate_refund_answer_node(state: EcommerceCoreState) -> dict:
    """组合订单状态和退款规则，生成退款咨询回复。"""
    order_status = state["order_status"]

    status_map = {
        "paid": "已付款，待发货",
        "shipped": "已发货",
        "not_found": "未查询到订单",
    }

    return {
        "final_answer": (
            f"您的订单当前状态是：{status_map.get(order_status, '未知')}。"
            f"{state.get('policy_answer')}"
        ),
        "logs": ["generate_refund_answer：退款回答完成。"],
    }


def build_graph():
    """创建并编译电商客服工作流。"""
    graph = StateGraph(EcommerceCoreState)

    # 注册流程中的各个节点
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("ask_order_id", ask_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("decide_policy_type", decide_policy_type_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("generate_general_answer", generate_general_answer_node)
    graph.add_node("generate_order_answer", generate_order_answer_node)
    graph.add_node("generate_refund_answer", generate_refund_answer_node)

    # 工作流从意图识别节点开始
    graph.add_edge(START, "classify_intent")

    # 普通问题直接回答；订单和退款问题进入订单处理流程
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "generate_general_answer",
            "need_order": "extract_order_id",
        },
    )

    # 找不到订单号就追问用户，否则查询订单
    graph.add_conditional_edges(
        "extract_order_id",
        route_after_extract_order_id,
        {
            "ask_order_id": "ask_order_id",
            "query_order": "query_order",
        },
    )

    # 查询订单后，退款问题继续查询规则；订单查询问题直接生成回复
    graph.add_conditional_edges(
        "query_order",
        route_after_query_order,
        {
            "retrieve_policy": "decide_policy_type",
            "generate_order_answer": "generate_order_answer",
        },
    )

    # 退款流程：判断规则类型 → 获取规则说明 → 生成最终回复
    graph.add_edge("decide_policy_type", "retrieve_policy")
    graph.add_edge("retrieve_policy", "generate_refund_answer")

    # 各个最终回复节点执行完成后，结束工作流
    graph.add_edge("ask_order_id", END)
    graph.add_edge("generate_general_answer", END)
    graph.add_edge("generate_order_answer", END)
    graph.add_edge("generate_refund_answer", END)

    return graph.compile()


def main():
    """运行示例问题，并打印最终回复和各节点日志。"""
    app = build_graph()

    # 覆盖普通问题、订单查询、退款咨询和缺少订单号的情况
    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单 10002 还没发货，可以退款吗？",
        "我要退款，但是忘记订单号了。",
    ]

    for question in questions:
        print("question:", question)
        print("=" * 80)

        # 每个问题使用一份全新的初始状态
        result = app.invoke({
            "user_question": question,
            "intent": "",
            "order_id": None,
            "order_status": None,
            "policy_type": None,
            "policy_answer": None,
            "final_answer": "",
            "logs": [],
        })

        print("final_answer:", result["final_answer"])
        print("logs:")
        for log in result["logs"]:
            print("-", log)

        print("=" * 120)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()