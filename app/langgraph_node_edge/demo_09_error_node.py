import asyncio
from typing import Literal

from langgraph.graph import END, START, StateGraph

# 提供客服流程的初始状态。
from app.langgraph_node_edge.mock_services import create_initial_state

# 各节点共享的状态类型。
from app.langgraph_node_edge.schemas import EcommerceNodeEdgeState



# 这段代码演示了 LangGraph 中的异常捕获与条件分支：工具调用失败时记录错误，并转到兜底节点；成功时直接结束流程。
# 执行流程
# - 正常问题：`risky_tool_node` 成功返回答复，错误列表为空，路由直接到 END。
# - 包含“异常”的问题：节点主动抛出 RuntimeError，`except` 捕获后记录错误，路由到 error_handler_node 生成兜底答复。
# 这里的工具调用失败是通过关键词人为模拟的。实际项目中，可以在 try 中调用外部 API 或业务工具，并根据失败类型记录错误或执行重试。


async def risky_tool_node(state: EcommerceNodeEdgeState) -> dict:
    """模拟可能失败的异步工具调用，并捕获异常。"""
    try:
        # 如果用户问题包含“异常”，主动抛出错误以模拟调用失败。
        if "异常" in state["user_question"]:
            raise RuntimeError("模拟工具调用失败")

        # 调用成功时，写入日志、答复，并标记流程已完成。
        return {
            "logs": ["risky_tool_node：工具调用成功"],
            "final_answer": "工具调用成功，正常返回结果。",
            "is_finished": True,
        }

    except Exception as exc:
        # 捕获异常并将错误信息写入状态。
        # 这里不生成最终答复，后续由错误处理节点负责兜底。
        return {
            "errors": [repr(exc)],
            "logs": ["risky_tool_node：工具调用失败"],
        }


def route_after_risky_tool(
    state: EcommerceNodeEdgeState,
) -> Literal["error_handler", "end"]:
    """检查错误列表，决定进入错误处理节点还是结束流程。"""
    if state["errors"]:
        return "error_handler"

    return "end"


def error_handler_node(state: EcommerceNodeEdgeState) -> dict:
    """为工具调用失败的情况生成用户可见的兜底答复。"""
    return {
        "final_answer": "当前服务暂时异常，请稍后再试，或联系人工客服。",
        "is_finished": True,
        "logs": ["error_handler_node：已生成兜底回答"],
    }


def build_graph():
    """构建包含异常分支的工作流。"""
    graph = StateGraph(EcommerceNodeEdgeState)

    # 注册可能失败的工具节点和错误处理节点。
    graph.add_node("risky_tool", risky_tool_node)
    graph.add_node("error_handler", error_handler_node)

    graph.add_edge(START, "risky_tool")

    # 工具节点完成后，根据错误列表选择下一步：
    # 有错误 -> error_handler；没有错误 -> END。
    graph.add_conditional_edges(
        "risky_tool",
        route_after_risky_tool,
        {
            "error_handler": "error_handler",
            "end": END,
        },
    )

    # 兜底答复生成后结束流程。
    graph.add_edge("error_handler", END)

    return graph.compile()


async def main():
    """分别运行正常问题和会触发异常的问题，并打印运行结果。"""
    app = build_graph()

    for question in ["正常问题", "这个问题会触发异常"]:
        # 为每个问题创建独立的初始状态，并异步运行工作流。
        result = await app.ainvoke(
            create_initial_state(question)
        )

        print("question:", question)
        print("final_answer:", result["final_answer"])
        print("errors:", result["errors"])
        print("logs:", result["logs"])
        print("=" * 80)


# 启动异步主函数。
if __name__ == "__main__":
    asyncio.run(main())