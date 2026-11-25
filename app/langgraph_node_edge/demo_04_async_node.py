import asyncio
from typing import TypedDict

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 异步 Node
# 执行流程
# 工作流依次执行三个异步节点：
# 1. extract_order_id_node 从问题中查找订单号。
# 2. query_order_node 根据订单号返回订单状态。
# 3. answer_node 将订单状态整理成答复。
# 4. app.ainvoke(...) 异步运行整个图，`await` 等待工作流完成。
# async def 定义异步函数，`await` 用来等待异步操作完成。这里的 asyncio.sleep(0.05) 只是模拟等待时间；实际应用中可以替换为异步数据库查询、HTTP 请求或其他异步服务调用。


class AsyncNodeState(TypedDict):
    """异步订单查询流程中各节点共享的状态。"""

    user_question: str      # 用户输入的问题
    order_id: str | None    # 提取到的订单号；未找到时为 None
    order_status: str       # 查询到的订单状态
    final_answer: str       # 最终生成的答复


async def extract_order_id_node(state: AsyncNodeState) -> dict:
    """异步从用户问题中提取演示用的订单号。"""

    # 模拟异步操作的等待时间，例如等待外部服务响应。
    await asyncio.sleep(0.05)

    # 此示例只识别固定订单号 10001。
    if "10001" in state["user_question"]:
        return {"order_id": "10001"}

    # 问题中没有该订单号时，记录为 None。
    return {"order_id": None}


async def query_order_node(state: AsyncNodeState) -> dict:
    """根据提取到的订单号异步查询订单状态。"""

    # 模拟查询订单接口的等待时间。
    await asyncio.sleep(0.05)

    if state["order_id"] == "10001":
        return {"order_status": "已发货"}

    # 未识别到订单号或订单号不匹配时返回兜底状态。
    return {"order_status": "未查询到订单"}


async def answer_node(state: AsyncNodeState) -> dict:
    """根据订单状态异步生成最终答复。"""

    # 模拟生成回复或调用其他异步服务所需的等待时间。
    await asyncio.sleep(0.05)

    return {
        "final_answer": f"订单状态：{state['order_status']}"
    }


def build_graph():
    """创建并编译异步订单查询工作流。"""
    graph = StateGraph(AsyncNodeState)

    # 注册三个异步处理节点。
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：提取订单号 -> 查询订单 -> 生成答复。
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


async def main():
    """以异步方式运行工作流并打印完整结果。"""
    app = build_graph()

    # ainvoke() 是异步调用方式，需要使用 await 等待结果。
    result = await app.ainvoke({
        "user_question": "帮我查一下订单 10001。",
        "order_id": None,
        "order_status": "",
        "final_answer": "",
    })

    print(result)


# asyncio.run() 创建并运行事件循环，以启动异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())