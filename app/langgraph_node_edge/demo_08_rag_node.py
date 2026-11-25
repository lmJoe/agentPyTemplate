

import asyncio

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 导入初始状态构造函数，以及模拟订单查询和政策检索服务。
from app.langgraph_node_edge.mock_services import (
    create_initial_state,
    mock_query_order,
    mock_retrieve_policy,
)

# 导入各节点共享的状态类型。
from app.langgraph_node_edge.schemas import EcommerceNodeEdgeState

# 这段代码在订单查询流程后增加了售后政策检索：先提取订单号并查询订单状态，再根据状态检索退款规则，最后组合订单信息和政策说明生成答复。
# 执行流程
# 1. extract_order_id_node 从问题中找到订单号 10002。
# 2. query_order_node 调用模拟订单服务，得到订单状态“已付款，待发货”。
# 3. retrieve_policy_rag_node 根据状态检索未发货退款规则，并保存来源信息。
# 4. answer_node 将订单状态和政策说明合并为最终答复。
# 5. main 打印答复、检索来源和执行日志。
# 这里的 mock_retrieve_policy 是模拟服务。虽然节点名中有 rag，当前代码并未连接真实向量数据库或知识库检索系统。


def extract_order_id_node(state: EcommerceNodeEdgeState) -> dict:
    """从用户问题中提取订单号 10002。"""

    # 这是演示用的固定匹配逻辑，只识别订单号 10002。
    if "10002" in state["user_question"]:
        return {
            "order_id": "10002",
            "logs": ["extract_order_id：订单号为 10002"],
        }

    # 没有匹配到订单号时，将 order_id 设为 None。
    return {
        "order_id": None,
        "logs": ["extract_order_id：未提取到订单号"],
    }


async def query_order_node(state: EcommerceNodeEdgeState) -> dict:
    """异步查询订单，并保存订单信息。"""

    # 调用模拟订单服务，await 等待查询结果。
    order_info = await mock_query_order(state["order_id"])

    return {
        "order_info": order_info,
        "logs": [f"query_order：{order_info['status_text']}"],
    }


async def retrieve_policy_rag_node(
    state: EcommerceNodeEdgeState,
) -> dict:
    """根据订单状态异步检索对应的售后政策。"""

    order_info = state["order_info"]

    # 将订单状态传给模拟政策服务，获取查询文本、政策答案和来源。
    policy_result = await mock_retrieve_policy(
        order_status=order_info.get("status"),
    )

    return {
        "policy_query": policy_result["policy_query"],
        "policy_answer": policy_result["policy_answer"],
        "sources": policy_result["sources"],
        "logs": ["retrieve_policy_rag_node：完成售后规则检索"],
    }


def answer_node(state: EcommerceNodeEdgeState) -> dict:
    """将订单状态和政策说明组合成最终答复。"""

    order_info = state["order_info"]

    return {
        "final_answer": (
            f"您的订单状态是：{order_info['status_text']}。"
            f"{state['policy_answer']}"
        ),
        "is_finished": True,
        "logs": ["answer_node：最终回答完成"],
    }


def build_graph():
    """构建并编译订单查询与政策检索工作流。"""
    graph = StateGraph(EcommerceNodeEdgeState)

    # 注册订单号提取、订单查询、政策检索和答复生成节点。
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("retrieve_policy", retrieve_policy_rag_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：
    # 提取订单号 -> 查询订单 -> 检索政策 -> 生成答复。
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", "retrieve_policy")
    graph.add_edge("retrieve_policy", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


async def main():
    """运行退款问题示例，并打印回答、资料来源和执行日志。"""
    app = build_graph()

    # 创建初始状态，然后异步执行整个图。
    result = await app.ainvoke(
        create_initial_state("我的订单 10002 还没发货，可以退款吗？")
    )

    print("final_answer:")
    print(result["final_answer"])

    print("=" * 80)
    print("sources:")
    for source in result["sources"]:
        print(source)

    print("=" * 80)
    print("logs:")
    for log in result["logs"]:
        print("-", log)


# asyncio.run() 创建事件循环并运行异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())