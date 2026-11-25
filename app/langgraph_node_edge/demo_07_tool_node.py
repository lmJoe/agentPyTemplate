import asyncio

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 导入初始状态构造函数和异步模拟订单查询服务。
from app.langgraph_node_edge.mock_services import (
    create_initial_state,
    mock_query_order,
)

# 导入各个节点共享的状态类型。
from app.langgraph_node_edge.schemas import EcommerceNodeEdgeState

# Tool Node
# 这段代码把前面定义的模拟订单服务接入 LangGraph：先从用户问题提取订单号，再异步查询订单，最后生成答复，同时记录工具调用和执行日志。
# 工作流按以下顺序运行：
# 1. extract_order_id_node 从问题中找到订单号 10001。
# 2. query_order_tool_node 调用 mock_query_order()，异步获取模拟订单信息，并记录工具调用和日志。
# 3. answer_node 读取订单状态，生成最终答复并将 is_finished 设为 True。
# 4. main 打印答复、工具调用记录和日志。
# query_order_tool_node 是异步节点，因此使用 await 等待模拟服务；整个图也通过 app.ainvoke() 异步执行。
# 这个节点只负责
# 拿到 order_id
# 调用订单工具
# 写入 order_info
# 追加 tool_calls
# 追加 logs

def extract_order_id_node(state: EcommerceNodeEdgeState) -> dict:
    """从用户问题中提取示例订单号。"""
    question = state["user_question"]

    # 这里只识别两个固定订单号，属于演示逻辑。
    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = None

    return {
        "order_id": order_id,

        # 记录本节点提取到的订单号。
        "logs": [f"extract_order_id：订单号为 {order_id}"],
    }


async def query_order_tool_node(
    state: EcommerceNodeEdgeState,
) -> dict:
    """调用异步模拟服务查询订单，并记录工具调用信息。"""

    # await 等待订单查询协程完成。
    order_info = await mock_query_order(
        order_id=state["order_id"]
    )

    return {
        "order_info": order_info,

        # 保存工具名称、参数、调用标识、成功状态和结果摘要。
        "tool_calls": [
            {
                "name": "query_order",
                "args": {
                    "order_id": state["order_id"],
                },
                "id": "tool_call_query_order_001",
                "success": True,
                "result_preview": order_info["status_text"],
            }
        ],
        "logs": [
            f"query_order_tool_node：{order_info['status_text']}"
        ],
    }


def answer_node(state: EcommerceNodeEdgeState) -> dict:
    """根据订单查询结果生成最终答复。"""
    order_info = state["order_info"]

    return {
        "final_answer": f"您的订单状态是：{order_info['status_text']}。",

        # 标记工作流已经完成。
        "is_finished": True,

        # 记录最终答复已生成。
        "logs": ["answer_node：订单回答生成完成"],
    }


def build_graph():
    """构建并编译订单查询工作流。"""
    graph = StateGraph(EcommerceNodeEdgeState)

    # 注册提取订单号、查询订单和生成答复三个节点。
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_tool_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：提取订单号 -> 查询订单 -> 生成答复。
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


async def main():
    """异步运行工作流并打印答复、工具调用记录和日志。"""
    app = build_graph()

    # 创建初始状态，并通过 ainvoke 异步执行工作流。
    result = await app.ainvoke(
        create_initial_state("帮我查一下订单 10001。")
    )

    print("final_answer:", result["final_answer"])
    print("tool_calls:", result["tool_calls"])
    print("logs:", result["logs"])


# asyncio.run() 创建事件循环并运行异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())