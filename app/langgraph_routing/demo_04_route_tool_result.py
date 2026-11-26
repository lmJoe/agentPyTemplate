import asyncio
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import (
    create_initial_state,
    mock_query_order,
)
from app.langgraph_routing.schemas import RoutingState

# 根据工具结果路由
# 在前面“提取订单号”的基础上，增加了异步查询订单和按查询结果分支处理：
# START → 提取订单号 → 查询订单
#                          ├─ 成功 → 返回订单状态
#                          ├─ 订单不存在 → 提示检查订单号
#                          └─ 其他错误 → 返回服务异常提示
# extract_order_id_node：从问题中提取订单号。
# query_order_node：调用模拟订单服务，并记录成功或失败、错误信息和工具调用记录。
# route_after_query_order：根据 tool_success 和 errors 决定后续分支。
# 三个结果节点：分别处理查询成功、订单不存在和其他错误。
# main()：使用 ainvoke() 异步运行 LangGraph。

# 从用户问题中提取订单号。
# 当前示例只识别 10001 和 99999。
def extract_order_id_node(state: RoutingState) -> dict:
    question = state["user_question"]

    if "10001" in question:
        order_id = "10001"
    elif "99999" in question:
        order_id = "99999"
    else:
        order_id = None  # 没有识别到支持的订单号

    # 返回状态更新，并将提取结果写入日志。
    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：order_id={order_id}"],
    }


# 异步查询订单，并把调用结果写入状态。
async def query_order_node(state: RoutingState) -> dict:
    # 调用模拟订单服务，使用当前状态中的订单号进行查询。
    result = await mock_query_order(state["order_id"])

    # 查询失败时，记录失败状态、错误信息和工具调用记录。
    if not result["success"]:
        return {
            "tool_success": False,
            "order_info": result.get("data"),
            "errors": [result["error"]],
            "tool_calls": [
                {
                    "name": "query_order",  # 工具名称
                    "args": {"order_id": state["order_id"]},  # 调用参数
                    "success": False,
                    "result_preview": result["error"],  # 错误结果摘要
                }
            ],
            "logs": [f"query_order：失败 {result['error']}"],
        }

    # 查询成功时，保存订单数据及调用记录。
    return {
        "tool_success": True,
        "order_info": result["data"],
        "tool_calls": [
            {
                "name": "query_order",
                "args": {"order_id": state["order_id"]},
                "success": True,
                "result_preview": result["data"]["status_text"],  # 订单状态摘要
            }
        ],
        "logs": [f"query_order：成功 {result['data']['status_text']}"],
    }


# 根据订单查询结果选择成功、订单不存在或其他错误分支。
def route_after_query_order(
    state: RoutingState,
) -> Literal["success", "not_found", "error"]:
    if state["tool_success"]:
        return "success"

    # 检查错误列表，区分“订单不存在”和其他查询错误。
    if state["errors"] and "order_not_found" in state["errors"]:
        return "not_found"

    return "error"


# 查询成功后的回答节点。
def order_success_node(state: RoutingState) -> dict:
    return {
        "final_answer": f"您的订单状态是：{state['order_info']['status_text']}。",
        "is_finished": True,  # 标记本次流程结束
        "logs": ["order_success：订单查询成功"],
    }


# 订单不存在时的回答节点。
def order_not_found_node(state: RoutingState) -> dict:
    return {
        "final_answer": "没有查询到该订单，请检查订单号是否正确。",
        "is_finished": True,
        "logs": ["order_not_found：订单不存在"],
    }


# 其他查询错误的兜底节点。
def error_handler_node(state: RoutingState) -> dict:
    return {
        "final_answer": "订单查询服务暂时异常，请稍后再试。",
        "is_finished": True,
        "logs": ["error_handler：工具失败兜底"],
    }


# 构建并编译订单查询流程图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中共享状态的结构

    # 注册处理节点。
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("order_success", order_success_node)
    graph.add_node("order_not_found", order_not_found_node)
    graph.add_node("error_handler", error_handler_node)

    # 设置执行入口和固定边：先提取订单号，再查询订单。
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")

    # 查询结束后，根据状态中的结果选择处理分支。
    graph.add_conditional_edges(
        "query_order",
        route_after_query_order,
        {
            "success": "order_success",
            "not_found": "order_not_found",
            "error": "error_handler",
        },
    )

    # 各结果分支处理完后结束流程。
    graph.add_edge("order_success", END)
    graph.add_edge("order_not_found", END)
    graph.add_edge("error_handler", END)

    return graph.compile()  # 编译图，得到可异步调用的应用


# 异步运行示例问题并打印执行结果。
async def main():
    app = build_graph()

    for question in ["帮我查一下订单 10001。", "帮我查一下订单 99999。"]:
        # ainvoke 用于异步执行图，并返回执行后的完整状态。
        result = await app.ainvoke(create_initial_state(question))

        print("question:", question)
        print("final_answer:", result["final_answer"])
        print("errors:", result["errors"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时启动异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())