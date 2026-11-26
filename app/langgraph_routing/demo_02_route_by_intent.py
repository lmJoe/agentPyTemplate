from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import create_initial_state
from app.langgraph_routing.schemas import RoutingState

# 根据 intent 路由：先判断用户问题属于哪种意图，再根据判断结果选择要执行的处理节点
# 这段代码构建了一个简单的客服意图路由流程：
# START → 意图识别 → 普通回答 / 转人工 / 订单相关流程 → END
# classify_intent_node：用关键词识别意图，并把结果和日志写入状态。
# route_by_intent：把识别出的意图转换成图的分支名称。
# general_answer_node、`transfer_human_node`、`need_order_node`：分别处理普通问题、转人工和订单相关问题。
# build_graph()：注册节点与边，编译 LangGraph。
# main()：用示例问题调用图，并打印执行结果。


# 意图识别节点：根据用户问题中的关键词判断问题类型。
def classify_intent_node(state: RoutingState) -> dict:
    question = state["user_question"]

    # 按照从上到下的顺序匹配；如果问题同时包含多个关键词，
    # 第一个匹配到的条件会决定最终意图。
    if "人工" in question:
        intent = "human_service"
    elif "退款" in question or "退货" in question:
        intent = "refund"
    elif "物流" in question:
        intent = "logistics"
    elif "订单" in question:
        intent = "query_order"
    else:
        intent = "general"

    # 返回要更新的状态字段。logs 会记录本节点的处理结果。
    return {
        "intent": intent,
        "logs": [f"classify_intent：识别到 intent={intent}"],
    }


# 条件路由函数：将识别出的意图映射为图中的分支名称。
def route_by_intent(
    state: RoutingState,
) -> Literal["general", "human", "need_order"]:
    intent = state["intent"]

    if intent == "general":
        return "general"

    if intent == "human_service":
        return "human"

    # 当前示例中，除普通问题和转人工外的意图，
    # 都进入需要订单信息的分支。
    return "need_order"


# 普通问题回答节点。
def general_answer_node(state: RoutingState) -> dict:
    return {
        "final_answer": "这是普通问题，可以走普通 Chat。",
        "is_finished": True,  # 标记本次流程已完成
        "logs": ["general_answer：完成普通回答"],
    }


# 转人工节点。
def transfer_human_node(state: RoutingState) -> dict:
    return {
        "final_answer": "我已经为您转接人工客服，请稍等。",
        "is_finished": True,
        "logs": ["transfer_human：完成转人工"],
    }


# 订单相关流程节点。此示例只提示后续需要订单号提取，
# 还没有实际实现订单号提取或订单查询。
def need_order_node(state: RoutingState) -> dict:
    return {
        "final_answer": "这个问题需要订单号，后续会进入订单号提取流程。",
        "logs": ["need_order：进入订单相关流程"],
    }


# 构建并编译意图路由图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中共享状态的类型

    # 注册节点名称及其对应的处理函数。
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("general_answer", general_answer_node)
    graph.add_node("transfer_human", transfer_human_node)
    graph.add_node("need_order", need_order_node)

    # 设置图的入口，从意图识别节点开始。
    graph.add_edge(START, "classify_intent")

    # 根据 route_by_intent 的返回值选择后续节点。
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "general_answer",
            "human": "transfer_human",
            "need_order": "need_order",
        },
    )

    # 每个分支节点执行后都结束本次流程。
    graph.add_edge("general_answer", END)
    graph.add_edge("transfer_human", END)
    graph.add_edge("need_order", END)

    return graph.compile()  # 编译后得到可调用的 LangGraph 应用


# 使用多个示例问题运行图，并输出关键状态。
def main():
    app = build_graph()

    questions = [
        "你好，介绍一下 LangGraph。",
        "我要找人工客服。",
        "帮我查一下订单 10001。",
        "我的订单还没发货，可以退款吗？",
    ]

    for question in questions:
        # 创建该问题对应的初始状态，并执行整张图。
        result = app.invoke(create_initial_state(question))

        print("question:", question)
        print("intent:", result["intent"])
        print("final_answer:", result["final_answer"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时执行 main；被导入为模块时不自动运行。
if __name__ == "__main__":
    main()