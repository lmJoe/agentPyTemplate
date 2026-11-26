from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import create_initial_state
from app.langgraph_routing.schemas import RoutingState

# 演示了工具调用失败后的重试流程：
# START → 调用工具
#           ├─ 成功 → 成功处理节点 → END
#           ├─ 失败且未达到重试上限 → 回到调用工具
#           └─ 失败且达到重试上限 → 兜底节点 → END
# call_unstable_tool_node：模拟工具调用。前两次失败，之后成功，并更新重试次数和日志。
# route_after_unstable_tool：根据 tool_success、`retry_count` 和 max_retry 决定下一步。
# success_node：工具成功时生成完成回复。
# fallback_node：达到重试上限仍失败时生成兜底回复。
# max_retry：允许的最大重试次数。
# recursion_limit：限制 LangGraph 图的最大执行步数，避免循环图无限运行。


# 模拟一个可能失败、之后可能成功的工具调用。
def call_unstable_tool_node(state: RoutingState) -> dict:
    retry_count = state["retry_count"]

    # 前两次调用模拟失败，并递增重试计数。
    if retry_count < 2:
        return {
            "tool_success": False,
            "retry_count": retry_count + 1,
            "errors": [f"第 {retry_count + 1} 次工具调用失败"],
            "logs": [f"call_unstable_tool：失败 retry_count={retry_count + 1}"],
        }

    # 重试两次后，模拟工具调用成功。
    return {
        "tool_success": True,
        "logs": ["call_unstable_tool：工具调用成功"],
    }


# 根据调用结果和重试次数，决定重试、成功结束或进入兜底。
def route_after_unstable_tool(
    state: RoutingState,
) -> Literal["retry", "success", "fallback"]:
    if state["tool_success"]:
        return "success"

    if state["retry_count"] < state["max_retry"]:
        return "retry"

    return "fallback"


# 工具调用成功后的处理节点。
def success_node(state: RoutingState) -> dict:
    return {
        "final_answer": "工具调用成功，已完成处理。",
        "is_finished": True,
        "logs": ["success：处理完成"],
    }


# 达到最大重试次数仍失败时的兜底节点。
def fallback_node(state: RoutingState) -> dict:
    return {
        "final_answer": "工具多次调用失败，请稍后再试或联系人工客服。",
        "is_finished": True,
        "logs": ["fallback：超过最大重试次数"],
    }


# 构建并编译带重试分支的流程图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定流程中传递的状态结构

    # 注册工具调用、成功处理和兜底节点。
    graph.add_node("call_unstable_tool", call_unstable_tool_node)
    graph.add_node("success", success_node)
    graph.add_node("fallback", fallback_node)

    # 设置入口，从工具调用节点开始。
    graph.add_edge(START, "call_unstable_tool")

    # 每次工具调用后，根据状态决定回到调用节点、成功结束或进入兜底。
    graph.add_conditional_edges(
        "call_unstable_tool",
        route_after_unstable_tool,
        {
            "retry": "call_unstable_tool",
            "success": "success",
            "fallback": "fallback",
        },
    )

    # 成功和兜底节点执行后都结束流程。
    graph.add_edge("success", END)
    graph.add_edge("fallback", END)

    return graph.compile()  # 编译图，生成可调用的应用


# 执行示例并打印最终结果、重试次数、错误和日志。
def main():
    app = build_graph()

    # 创建初始状态，并将允许的最大重试次数设置为 3。
    state = create_initial_state("测试不稳定工具。")
    state["max_retry"] = 3

    # invoke 同步运行图。recursion_limit 限制图的最大执行步数，
    # 防止循环流程意外运行过久。
    result = app.invoke(
        state,
        config={
            "recursion_limit": 10
        },
    )

    print("final_answer:", result["final_answer"])
    print("retry_count:", result["retry_count"])

    print("errors:")
    for error in result["errors"]:
        print("-", error)

    print("logs:")
    for log in result["logs"]:
        print("-", log)


# 直接运行此文件时执行示例。
if __name__ == "__main__":
    main()