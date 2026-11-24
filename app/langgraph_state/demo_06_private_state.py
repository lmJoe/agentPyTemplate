from typing import TypedDict

from langgraph.graph import END, START, StateGraph


#  Private State 的常见设计。
# 主要通过 OverallState 中的 internal_query 和 raw_docs 字段体现 Private State 的常见设计
# 它们用于图内部节点之间传递数据：
# - rewrite_query_node 写入 internal_query，供后续检索步骤使用。
# - retrieve_docs_node 写入 raw_docs，供 answer_node 使用。
# - InputState 只暴露用户输入的 question。
# - OutputState 只暴露最终结果 answer。
# 因此，输入和输出 schema 将内部字段与调用者隔离，而 OverallState 保留这些字段供工作流内部使用。这就是这段代码中 Private State 的主要体现。

# 定义工作流的输入结构：调用者只需提供问题
class InputState(TypedDict):
    question: str

# 实现的是基于预设文档的回答流程，和demo05的区别是：demo05是基于关键词的意图识别和回答，
# 定义工作流内部流转的完整状态
class OverallState(TypedDict):
    question: str
    internal_query: str  # 改写后的内部检索问题
    raw_docs: list[str]  # 检索到的原始文档
    answer: str           # 生成的最终回答


# 定义工作流的输出结构：最终只返回 answer
class OutputState(TypedDict):
    answer: str


def rewrite_query_node(state: OverallState) -> dict:
    """将用户问题改写为适合内部检索的查询。"""
    return {
        "internal_query": f"知识库检索：{state['question']}"
    }


def retrieve_docs_node(state: OverallState) -> dict:
    """模拟从知识库检索相关文档。"""
    return {
        "raw_docs": [
            "订单未发货时，用户可以申请取消订单并退款。",
            "订单已发货后，需要收到商品后再申请退货退款。",
        ]
    }


def answer_node(state: OverallState) -> dict:
    """根据检索到的文档和原始问题生成回答。"""
    # 将文档列表合并为一段文本，方便放入回答
    docs_text = "\n".join(state["raw_docs"])

    return {
        "answer": (
            f"根据内部检索到的规则：\n{docs_text}\n\n"
            f"针对你的问题：{state['question']}，未发货订单通常可以申请取消并退款。"
        )
    }


def build_graph():
    """创建并编译检索问答工作流。"""
    graph = StateGraph(
        OverallState,             # 节点之间共享的完整内部状态
        input_schema=InputState,  # 限定调用者可以传入的字段
        output_schema=OutputState,  # 限定工作流最终返回的字段
    )

    # 注册三个处理节点
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("retrieve_docs", retrieve_docs_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：开始 → 改写问题 → 检索文档 → 生成回答 → 结束
    graph.add_edge(START, "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve_docs")
    graph.add_edge("retrieve_docs", "answer")
    graph.add_edge("answer", END)

    # 编译图，返回可调用的工作流
    return graph.compile()


def main():
    """运行工作流并打印结果。"""
    app = build_graph()

    # 输入符合 InputState，只包含用户问题
    result = app.invoke({
        "question": "订单未发货可以退款吗？"
    })

    # OutputState 只定义了 answer，因此结果只包含最终回答
    print(result)


# 直接运行文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()