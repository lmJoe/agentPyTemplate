from typing import Literal, TypedDict

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 条件 Edge
# 条件路由如何工作
# 图的执行过程是：
# 1. 每个问题先进入 classify_intent_node。
# 2. route_by_intent 读取状态中的 intent。
# 3. add_conditional_edges 根据意图选择分支：
#    - "general" → general_answer_node
#    - "query_order" → query_order_node
#    - "refund" → refund_node
# 4. 分支节点生成答复后，流程结束。
# 这与固定顺序执行不同：每次运行只会进入匹配的处理分支。
# 一个类型标注上的改进点
# RouteState 中的 intent 标注为普通 str，所以类型检查器无法确认它一定是三个合法路由值之一。可以用 Literal 收紧类型，避免依赖 # type: ignore：



class RouteState(TypedDict):
    """条件路由工作流中各节点共享的状态。"""

    user_question: str  # 用户输入的问题
    intent: str         # 分类节点识别出的意图
    final_answer: str   # 分支节点生成的答复


def classify_intent_node(state: RouteState) -> dict:
    """通过关键词判断用户意图。"""
    question = state["user_question"]

    # 优先检查“退款”，再检查“订单”，否则归类为普通问题。
    if "退款" in question:
        intent = "refund"
    elif "订单" in question:
        intent = "query_order"
    else:
        intent = "general"

    return {
        "intent": intent
    }


def route_by_intent(
    state: RouteState,
) -> Literal["general", "query_order", "refund"]:
    """读取分类结果，返回条件边使用的路由名称。"""
    # type: ignore 用来抑制类型检查器的提示：
    # RouteState 中的 intent 标注为 str，而本函数声明只返回三个固定值。
    return state["intent"]  # type: ignore[return-value]


def general_answer_node(state: RouteState) -> dict:
    """处理普通问题分支。"""
    return {
        "final_answer": "这是普通问题，走普通 Chat。"
    }


def query_order_node(state: RouteState) -> dict:
    """处理订单查询分支。"""
    return {
        "final_answer": "这是订单查询问题，下一步应该调用订单工具。"
    }


def refund_node(state: RouteState) -> dict:
    """处理退款问题分支。"""
    return {
        "final_answer": "这是退款问题，下一步应该查订单状态和退款规则。"
    }


def build_graph():
    """构建并编译带条件分支的工作流。"""
    graph = StateGraph(RouteState)

    # 注册意图识别节点和三个不同的处理分支。
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("general_answer", general_answer_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("refund", refund_node)

    # 所有请求先进入意图识别节点。
    graph.add_edge(START, "classify_intent")

    # 根据 route_by_intent 的返回值选择对应节点。
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "general_answer",
            "query_order": "query_order",
            "refund": "refund",
        },
    )

    # 每个分支完成后都结束工作流。
    graph.add_edge("general_answer", END)
    graph.add_edge("query_order", END)
    graph.add_edge("refund", END)

    return graph.compile()


def main():
    """依次运行三个示例问题，并打印分类及处理结果。"""
    app = build_graph()

    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单还没发货，可以退款吗？",
    ]

    for question in questions:
        # 每次调用都传入一份新的初始状态。
        result = app.invoke({
            "user_question": question,
            "intent": "unknown",
            "final_answer": "",
        })

        print("question:", question)
        print("intent:", result["intent"])
        print("final_answer:", result["final_answer"])
        print("=" * 80)


# 直接运行该文件时执行 main()；作为模块导入时不会自动运行。
if __name__ == "__main__":
    main()