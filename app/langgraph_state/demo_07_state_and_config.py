from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph


# State 和 Config 配合
# 这段代码构建了一个简单的订单查询流程：
# 1. extract_order_id_node 从用户问题中查找订单号；示例只识别 "10001"。
# 2. query_order_node 从工作流状态读取订单号，并从 config["configurable"] 读取 user_id。
# 3. 如果没有订单号，就提示用户提供；如果找到了，就生成一条示例查询回答。
# 4. 图按“提取订单号 → 查询订单”的顺序执行，最后打印结果。


# 定义订单查询工作流的状态结构
class OrderState(TypedDict):
    user_question: str       # 用户提出的问题
    order_id: str | None     # 从问题中提取出的订单号；未提取到时为 None
    answer: str              # 工作流生成的回答


def extract_order_id_node(state: OrderState) -> dict:
    """从用户问题中提取订单号。"""
    question = state["user_question"]

    # 示例中只识别订单号 10001
    if "10001" in question:
        return {"order_id": "10001"}

    # 没找到符合条件的订单号时，将订单号设为 None
    return {"order_id": None}

# query_order_node 同时读取 State 和 Config：
def query_order_node(
    state: OrderState,
    config: RunnableConfig,
) -> dict:
    """读取订单号和运行配置，生成订单查询结果。"""

    # 从 configurable 中读取调用方传入的用户 ID
    # 如果没有提供 user_id，则使用默认值 "unknown"
    user_id = config.get("configurable", {}).get("user_id", "unknown")

    # 如果没有提取到订单号，请用户补充
    if not state["order_id"]:
        return {
            "answer": "请提供订单号。"
        }

    # 当前只是生成示例回答；真实业务中还需要查询订单，
    # 并校验该订单是否属于当前用户或租户
    return {
        "answer": (
            f"用户 {user_id} 正在查询订单 {state['order_id']}。"
            "这里应该继续做订单归属校验。"
        )
    }


def build_graph():
    """创建并编译订单查询工作流。"""
    graph = StateGraph(OrderState)

    # 注册节点
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)

    # 设置执行顺序：开始 → 提取订单号 → 查询订单 → 结束
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", END)

    # 编译图，得到可调用的工作流
    return graph.compile()


def main():
    """运行示例并打印完整状态。"""
    app = build_graph()

    result = app.invoke(
        {
            "user_question": "帮我查一下订单 10001。",
            "order_id": None,
            "answer": "",
        },
        # config 是运行配置，不属于 OrderState。
        # 其中的 configurable 可携带本次调用所需的上下文信息。
        config={
            "configurable": {
                "thread_id": "thread_order_001",  # 会话或线程标识
                "user_id": "u_10001",             # 当前用户标识
                "tenant_id": "tenant_001",        # 当前租户标识
            }
        },
    )

    print(result)


# 直接运行此文件时执行示例；导入此模块时不自动运行
if __name__ == "__main__":
    main()