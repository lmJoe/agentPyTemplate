from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class RouterState(TypedDict):
    """定义图中各节点共享的状态结构。"""

    user_question: str  # 用户输入的问题
    intent: str          # 分类得到的意图，例如 refund、order、general
    answer: str          # 节点生成的回复


def classify_intent_node(state: RouterState) -> dict:
    """根据问题中的关键词判断用户意图，并更新 intent 状态。"""
    question = state["user_question"]

    # 使用简单的关键词规则进行分类
    if "退款" in question:
        intent = "refund"
    elif "订单" in question or "物流" in question:
        intent = "order"
    else:
        intent = "general"

    # 节点只返回需要更新的状态字段
    return {
        "intent": intent
    }


def route_by_intent(
    state: RouterState,
) -> Literal["general_answer", "order_answer", "refund_answer"]:
    """读取 intent，决定接下来执行哪个回答节点。"""
    intent = state["intent"]

    if intent == "refund":
        return "refund_answer"

    if intent == "order":
        return "order_answer"

    # 其他情况都走普通问题分支
    return "general_answer"


def general_answer_node(state: RouterState) -> dict:
    """处理普通问题，并写入 answer 状态。"""
    return {
        "answer": "这是普通问题，走普通 Chat。"
    }


def order_answer_node(state: RouterState) -> dict:
    """处理订单类问题。当前只是提示后续可以接入订单系统。"""
    return {
        "answer": "这是订单问题，下一步应该查询订单系统。"
    }


def refund_answer_node(state: RouterState) -> dict:
    """处理退款类问题。当前只是提示后续需要检查订单状态和退款规则。"""
    return {
        "answer": "这是退款问题，下一步应该查询订单状态和退款规则。"
    }


def build_graph():
    """创建并编译 LangGraph 工作流。"""
    graph = StateGraph(RouterState)

    # 注册各个处理节点
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("general_answer", general_answer_node)
    graph.add_node("order_answer", order_answer_node)
    graph.add_node("refund_answer", refund_answer_node)

    # 工作流从意图分类节点开始
    graph.add_edge(START, "classify_intent")

    # 分类完成后，根据 intent 选择对应的回答节点
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general_answer": "general_answer",
            "order_answer": "order_answer",
            "refund_answer": "refund_answer",
        },
    )

    # 每个回答节点处理完毕后，结束本次工作流
    graph.add_edge("general_answer", END)
    graph.add_edge("order_answer", END)
    graph.add_edge("refund_answer", END)

    # 编译图，得到可以调用的应用
    return graph.compile()


def main():
    # 构建 LangGraph 应用
    app = build_graph()

    # 准备三个不同类型的问题，用于演示不同路由分支
    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单还没发货，可以退款吗？",
    ]

    # 逐个调用工作流，并打印输入和完整状态结果
    for question in questions:
        result = app.invoke({
            "user_question": question,
            "intent": "",  # 初始时意图尚未分类
            "answer": "",  # 初始时还没有生成回复
        })

        print("question:", question)
        print("result:", result)
        print("=" * 80)


# 直接运行此文件时执行示例；被其他模块导入时不自动执行
if __name__ == "__main__":
    main()