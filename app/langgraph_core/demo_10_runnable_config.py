from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

# 这段代码演示如何通过 RunnableConfig 向 LangGraph 节点传递运行时配置：
# - state 保存工作流的业务数据，这里是用户问题和最终回答。
# - config 保存本次运行的配置，比如 user_id、`tenant_id` 和 trace_id。
# - answer_node 从 config["configurable"] 中读取这些信息，并与用户问题一起生成回答。
# thread_id 是常用于标识会话线程的配置项；但这段代码没有配置 checkpointer，因此单独传入 thread_id 不会保存或恢复工作流状态。


class ConfigState(TypedDict):
    """定义工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题
    answer: str         # 节点生成的回答


def answer_node(
    state: ConfigState,
    config: RunnableConfig,
) -> dict:
    """读取工作流配置中的信息，并生成回答。"""

    # 获取 configurable 配置；如果没有该字段，就使用空字典
    configurable = config.get("configurable", {})

    # 从配置中读取用户、租户和追踪 ID；缺少时使用默认值
    user_id = configurable.get("user_id", "unknown")
    tenant_id = configurable.get("tenant_id", "unknown")
    trace_id = configurable.get("trace_id", "unknown")

    # 返回本节点要更新的状态字段
    return {
        "answer": (
            f"用户 {user_id} 来自租户 {tenant_id}，"
            f"trace_id={trace_id}，"
            f"问题是：{state['user_question']}"
        )
    }


def build_graph():
    """创建并编译只有一个回答节点的工作流。"""
    graph = StateGraph(ConfigState)

    # 注册回答节点
    graph.add_node("answer", answer_node)

    # 设置执行顺序：开始 → answer → 结束
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行工作流，并传入问题和运行配置。"""
    app = build_graph()

    result = app.invoke(
        {
            # 这是传给工作流的业务状态
            "user_question": "RunnableConfig 有什么用？",
            "answer": "",
        },
        # 这是传给工作流的运行配置，不属于 ConfigState
        config={
            "configurable": {
                "thread_id": "thread_001",
                "user_id": "u_10001",
                "tenant_id": "tenant_001",
                "trace_id": "trace_abc123",
            }
        },
    )

    print(result)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()