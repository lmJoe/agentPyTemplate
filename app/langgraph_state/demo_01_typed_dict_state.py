from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class QAState(TypedDict):
    """定义问答工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题
    answer: str         # 节点生成的回答


def answer_node(state: QAState) -> dict:
    """读取用户问题，生成回答并更新状态。"""
    question = state["user_question"]

    return {
        "answer": f"你问的是：{question}。这是 TypedDict State 示例。"
    }


def build_graph():
    """创建并编译只有一个回答节点的工作流。"""
    graph = StateGraph(QAState)

    # 注册回答节点
    graph.add_node("answer", answer_node)

    # 设置执行顺序：开始 → answer → 结束
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行工作流，并打印执行后的状态。"""
    app = build_graph()

    # 提供初始状态，其中 answer 会由 answer_node 填充
    result = app.invoke({
        "user_question": "TypedDict State 有什么用？",
        "answer": "",
    })

    print(result)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()