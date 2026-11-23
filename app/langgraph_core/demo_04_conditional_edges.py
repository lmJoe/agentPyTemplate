from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


# 这段代码用 LangGraph 建立了一个简单的问题分类和路由流程：
# 1. classify_intent_node 根据关键词把问题分类为普通问题、订单问题或退款问题。
# 2. route_by_intent 读取分类结果，决定下一步进入哪个节点。
# 3. 对应的处理节点生成回复，并将回复写入 answer。
# 4. main() 依次运行三个示例问题，打印分类结果和回复。
# 注意：当前分类方式是关键词匹配，订单和退款节点也只是返回提示文字，还没有连接真实聊天模型或业务工具

class IntentState(TypedDict):
    """定义意图识别工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题
    intent: str         # 识别出的意图：general、order 或 refund
    answer: str         # 对应节点生成的回复


def classify_intent_node(state: IntentState) -> dict:
    """根据问题中的关键词识别意图，并更新 intent 状态。"""
    question = state["user_question"]

    if "退款" in question:
        intent = "refund"
    elif "订单" in question or "物流" in question:
        intent = "order"
    else:
        intent = "general"

    return {
        "intent": intent
    }


def route_by_intent(
    state: IntentState,
) -> Literal["general", "order", "refund"]:
    """返回识别出的意图，供条件边选择后续节点。"""
    # 前面的分类节点会将 intent 设置为这三个值之一。
    # type: ignore 用于告诉静态类型检查器忽略此处的类型提示问题。
    return state["intent"]  # type: ignore[return-value]


def general_node(state: IntentState) -> dict:
    """处理普通问题，并写入对应回复。"""
    return {
        "answer": "这是普通问题，走普通聊天。"
    }


def order_node(state: IntentState) -> dict:
    """处理订单问题；当前仅提示后续应调用订单工具。"""
    return {
        "answer": "这是订单问题，应该查询订单工具。"
    }


def refund_node(state: IntentState) -> dict:
    """处理退款问题；当前仅提示后续应查询订单和退款规则。"""
    return {
        "answer": "这是退款问题，应该查询订单状态和退款规则。"
    }


def build_graph():
    """创建并编译意图识别与路由工作流。"""
    graph = StateGraph(IntentState)

    # 注册意图分类节点和三个意图对应的处理节点
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("general_node", general_node)
    graph.add_node("order_node", order_node)
    graph.add_node("refund_node", refund_node)

    # 工作流从意图分类节点开始
    graph.add_edge(START, "classify_intent")

    # 用来根据当前状态或路由函数的返回值，决定接下来执行哪个节点。它可以让工作流按条件走不同分支
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "general_node",
            "order": "order_node",
            "refund": "refund_node",
        },
    )

    # 各处理节点完成后结束工作流
    graph.add_edge("general_node", END)
    graph.add_edge("order_node", END)
    graph.add_edge("refund_node", END)

    # 编译后返回可调用的工作流应用
    return graph.compile()


def main():
    """运行三个示例问题，并打印识别意图和最终回复。"""
    app = build_graph()

    # 分别演示普通问题、订单问题和退款问题
    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单没发货，可以退款吗？",
    ]

    for question in questions:
        # 每次调用都传入一份初始状态
        result = app.invoke({
            "user_question": question,
            "intent": "",
            "answer": "",
        })

        print("question:", question)
        print("intent:", result["intent"])
        print("answer:", result["answer"])
        print("=" * 80)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()