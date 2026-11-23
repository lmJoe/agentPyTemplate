from pydantic import BaseModel, Field

from langgraph.graph import END, START, StateGraph


# 这段代码用 Pydantic 模型定义 LangGraph 的状态，并运行一个简单问答流程：
# 1. PydanticQAState 定义 user_question 和 answer 两个字段，并为它们设置校验规则和默认值。
# 2. answer_node 读取问题，生成回答并更新状态。
# 3. build_graph 将节点连接成 START → answer → END。
# 4. main() 传入用户问题并运行工作流。
# 相比 TypedDict，Pydantic 模型可以为字段提供校验和描述信息。当前示例中，`user_question` 不能为空，`answer` 默认是空字符串。


# 这行表示 PydanticQAState 继承 Pydantic 的模型能力
class PydanticQAState(BaseModel):
    """使用 Pydantic 模型定义问答工作流的状态结构。"""

    # BaseModel 是从 Pydantic 导入的基类。
    # PydanticQAState 继承 BaseModel，所以它是一个 Pydantic 模型。

    # ... 表示该字段必填，且至少需要包含 1 个字符
    user_question: str = Field(
        ...,
        min_length=1,
        description="用户问题",
    )

    # 如果没有显式传入 answer，默认使用空字符串
    answer: str = Field(
        default="",
        description="最终回答",
    )


def answer_node(state: PydanticQAState) -> dict:
    """读取问题并生成回答，返回需要更新的状态字段。"""
    return {
        "answer": f"你问的是：{state.user_question}。这是 Pydantic State 示例。"
    }


def build_graph():
    """创建并编译只有一个回答节点的工作流。"""
    graph = StateGraph(PydanticQAState)

    # 注册回答节点
    graph.add_node("answer", answer_node)

    # 设置执行顺序：开始 → answer → 结束
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行工作流，并打印执行后的结果。"""
    app = build_graph()

    # 传入用户问题；answer 会使用 Pydantic 中定义的默认值
    result = app.invoke({
        "user_question": "Pydantic State 适合什么场景？",
    })

    print(result)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()