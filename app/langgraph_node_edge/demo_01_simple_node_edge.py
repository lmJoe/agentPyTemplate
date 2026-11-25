from typing import TypedDict

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph


# Node 和 Edge 是什么？
# - Node（节点）：工作流中的一个处理步骤。这里的 answer 节点执行 answer_node 函数，读取问题并生成答复。
# - Edge（边）：节点之间的执行连接。`START → answer → END` 表示流程从入口开始，执行 answer，随后结束。
# - State（状态）：节点之间共享的数据。这里包含 user_question 和 final_answer。

# Edge 的设计原则是：
# 原则一：固定流程用普通 Edge
# graph.add_edge("parse_file", "split_text")
# graph.add_edge("split_text", "embed_chunks")
# graph.add_edge("embed_chunks", "save_vector")

# 原则二：动态流程用 Conditional Edge
# graph.add_conditional_edges(
#     "classify_intent",
#     route_by_intent,
#     {
#         "general": "general_answer",
#         "refund": "refund_flow",
#     },
# )

# 原则三：同一个节点不要混用静态边和动态路由
# graph.add_edge("router", "node_a")
# graph.add_conditional_edges("router", route_func, ...)

# 原则四：循环一定要有退出条件
# retry_count
# max_steps
# is_finished
# tool_calls_count
# 原则五：路由函数只负责路由
# 不推荐在路由函数里调用模型、工具、数据库。
# 路由函数应该尽量简单。


class SimpleState(TypedDict):
    """图中传递的状态结构。"""

    user_question: str  # 用户输入的问题
    final_answer: str   # 生成的最终答复


def answer_node(state: SimpleState) -> dict:
    """读取用户问题，并生成一条简单回复。"""
    return {
        "final_answer": f"你问的是：{state['user_question']}"
    }


def build_graph():
    """创建并编译只有一个处理节点的工作流。"""
    graph = StateGraph(SimpleState)

    # 将 answer_node 注册为名为 answer 的节点。
    graph.add_node("answer", answer_node)

    # 设置执行路径：从入口进入 answer 节点，再到出口结束。
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)

    # 编译后得到可以通过 invoke() 执行的应用。
    return graph.compile()


def main():
    """运行示例并打印完整状态。"""
    app = build_graph()

    # 输入初始状态。节点执行后会在其中写入 final_answer。
    result = app.invoke({
        "user_question": "Node 和 Edge 是什么？",
        "final_answer": "",
    })

    print(result)


# 直接运行此文件时执行 main()；作为模块导入时不会自动执行。
if __name__ == "__main__":
    main()