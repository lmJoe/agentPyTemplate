from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import create_initial_state
from app.langgraph_routing.schemas import RoutingState

# 路由到 END
# 某个条件下不需要继续执行任何节点，可以直接结束
# START → 检查是否需要继续
#              ├─ 用户表示“不用处理” → END
#              └─ 其他情况 → 继续处理节点 → END
# check_finished_node：检查问题是否包含“不用处理”，并更新 is_finished 和回复内容。
# route_after_check_finished：根据 is_finished 返回 "end" 或 "continue"，决定图的下一步。
# continue_node：在用户仍需要处理时执行后续处理，并生成回复。
# build_graph()：定义节点、入口、条件边和结束边。
# main()：分别演示用户要求停止和继续处理的情况。

# 检查用户是否表示不需要继续处理。
def check_finished_node(state: RoutingState) -> dict:
    if "不用处理" in state["user_question"]:
        # 用户表示无需处理：生成回复、标记流程结束并记录日志。
        return {
            "final_answer": "好的，本次不做处理。",
            "is_finished": True,
            "logs": ["check_finished：用户表示不用处理"],
        }

    # 用户没有表示停止，流程保持未完成，等待路由到后续节点。
    return {
        "is_finished": False,
        "logs": ["check_finished：需要继续处理"],
    }


# 根据 is_finished 决定结束流程或继续处理。
def route_after_check_finished(
    state: RoutingState,
) -> Literal["continue", "end"]:
    if state["is_finished"]:
        return "end"

    return "continue"


# 用户仍需处理时执行的后续节点。
def continue_node(state: RoutingState) -> dict:
    return {
        "final_answer": "继续进入后续处理流程。",
        "is_finished": True,
        "logs": ["continue_node：继续处理完成"],
    }


# 构建并编译流程图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中共享状态的结构

    # 注册检查节点和继续处理节点。
    graph.add_node("check_finished", check_finished_node)
    graph.add_node("continue_node", continue_node)

    # 设置入口，从检查节点开始。
    graph.add_edge(START, "check_finished")

    # 检查后根据状态决定结束或继续。
    graph.add_conditional_edges(
        "check_finished",
        route_after_check_finished,
        {
            "continue": "continue_node",
            "end": END,
        },
    )

    # 继续处理节点执行后结束流程。
    graph.add_edge("continue_node", END)

    return graph.compile()  # 编译图，得到可调用的应用


# 运行两个示例问题，并打印最终回复和日志。
def main():
    app = build_graph()

    questions = [
        "不用处理了。",
        "帮我继续处理订单。",
    ]

    for question in questions:
        # 创建问题对应的初始状态并运行流程图。
        result = app.invoke(create_initial_state(question))

        print("question:", question)
        print("final_answer:", result["final_answer"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时执行示例。
if __name__ == "__main__":
    main()