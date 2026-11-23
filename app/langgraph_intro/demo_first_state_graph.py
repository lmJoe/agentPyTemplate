from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# 客服处理示例，使用了 LangGraph。


# 定义状态结构。
class SimpleState(TypedDict):
    user_question: str
    answer: str

# 定义节点函数。
def answer_node(state: SimpleState) -> dict:
    question = state["user_question"]

    return {
        "answer": f"你问的是：{question}。这是 LangGraph 的第一个节点回答。"
    }

# 定义图结构。
def build_graph():
    graph = StateGraph(SimpleState)

    graph.add_node("answer", answer_node)

    # 定义边。
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)

    # 编译图。
    return graph.compile()

# 主函数。
def main():
    app = build_graph()

    result = app.invoke({
        "user_question": "为什么需要 LangGraph？",
        "answer": "",
    })

    print(result)


if __name__ == "__main__":
    main()