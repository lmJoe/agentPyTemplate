import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

# 这段代码演示了如何在 LangGraph 中记录多个节点的执行日志：
# - step_one_node、`step_two_node` 和 answer_node 分别返回一条日志。
# - logs 字段使用 Annotated[list[str], operator.add] 声明了合并方式。每个节点返回的新日志会追加到已有列表中，而不是覆盖列表。
# - answer_node 根据用户问题生成最终回答。
# - 工作流按 START → step_one → step_two → answer → END 的顺序执行。
# 运行后会打印最终回答，以及每个节点追加的日志。


class LogState(TypedDict):
    """定义工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题

    # 使用 operator.add 作为 reducer：用 operator.add 累加每个节点返回的日志
    # 每个节点返回的新日志会追加到已有 logs 列表中
    logs: Annotated[list[str], operator.add]

    answer: str  # 最终生成的回答


def step_one_node(state: LogState) -> dict:
    """记录工作流开始分析问题。"""
    return {
        "logs": ["step_one：开始分析用户问题。"]
    }


def step_two_node(state: LogState) -> dict:
    """记录工作流准备生成最终回答。"""
    return {
        "logs": ["step_two：准备生成最终回答。"]
    }


def answer_node(state: LogState) -> dict:
    """生成回答，并记录回答完成日志。"""
    return {
        "logs": ["answer：回答生成完成。"],
        "answer": f"你问的是：{state['user_question']}",
    }


def build_graph():
    """创建并编译按顺序执行的工作流。"""
    graph = StateGraph(LogState)

    # 注册三个处理节点
    graph.add_node("step_one", step_one_node)
    graph.add_node("step_two", step_two_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：开始 → step_one → step_two → answer → 结束
    graph.add_edge(START, "step_one")
    graph.add_edge("step_one", "step_two")
    graph.add_edge("step_two", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行工作流，并打印最终回答和各步骤日志。"""
    app = build_graph()

    # 传入初始状态；执行过程中 logs 会逐步累积
    result = app.invoke({
        "user_question": "Reducer 有什么作用？",
        "logs": [],
        "answer": "",
    })

    print("answer:", result["answer"])
    print("logs:")
    for log in result["logs"]:
        print("-", log)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()