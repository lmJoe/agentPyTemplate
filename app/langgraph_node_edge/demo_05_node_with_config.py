from typing import TypedDict

# RunnableConfig 是 LangChain Runnable 使用的运行配置类型。
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

# Node 读取 Config
# 演示了如何通过 LangGraph 的 config 向节点传递运行时配置，例如用户 ID 和追踪 ID。它先从问题中提取订单号，再在查询节点中读取配置并生成答复。
# state 和 config 的区别
# - state 保存工作流中的业务数据，例如用户问题、订单号和最终答复。节点可以读取它，也可以通过返回字典更新它。
# - config 保存本次运行的配置信息，例如线程标识、用户 ID 和追踪 ID。节点通过函数参数 config 读取它。
# 运行时，`query_order_node` 会从 config["configurable"] 中取出 user_id 和 trace_id，并结合状态中的订单号生成答复。


class ConfigNodeState(TypedDict):
    """工作流节点之间共享的业务状态。"""

    user_question: str      # 用户输入的问题
    order_id: str | None    # 从问题中提取的订单号
    final_answer: str       # 最终答复


def extract_order_id_node(state: ConfigNodeState) -> dict:
    """从用户问题中提取示例订单号。"""

    # 这里只检查固定字符串 10001，属于演示用的简化逻辑。
    if "10001" in state["user_question"]:
        return {"order_id": "10001"}

    return {"order_id": None}


def query_order_node(
    state: ConfigNodeState,
    config: RunnableConfig,
) -> dict:
    """读取运行时配置，并生成订单查询说明。"""

    # configurable 用来放置调用时传入的自定义配置。
    configurable = config.get("configurable", {})

    # 从配置中读取用户 ID 和追踪 ID；缺省时使用 "unknown"。
    user_id = configurable.get("user_id", "unknown")
    trace_id = configurable.get("trace_id", "unknown")

    return {
        "final_answer": (
            f"trace_id={trace_id}，"
            f"用户 {user_id} 查询订单 {state['order_id']}。"
            "真实项目这里要做订单归属校验。"
        )
    }


def build_graph():
    """构建并编译订单号提取与查询工作流。"""
    graph = StateGraph(ConfigNodeState)

    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)

    # 执行顺序：提取订单号 -> 读取配置并生成答复 -> 结束。
    graph.add_edge(START, "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", END)

    return graph.compile()


def main():
    """运行示例，并向图传入本次调用的运行时配置。"""
    app = build_graph()

    result = app.invoke(
        {
            "user_question": "帮我查一下订单 10001。",
            "order_id": None,
            "final_answer": "",
        },
        config={
            "configurable": {
                # thread_id 常用于标识一次对话或工作流线程。
                "thread_id": "thread_lg32_config_001",

                # 下面两个是应用自定义配置，节点可从 config 中读取。
                "user_id": "u_10001",
                "trace_id": "trace_lg32_abc",
            }
        },
    )

    print(result)


# 直接运行文件时启动示例；被导入时不自动运行。
if __name__ == "__main__":
    main()