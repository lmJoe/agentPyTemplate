from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

# 这段代码构建了一个简单的 LangGraph 问答路由流程：先由 classify_node 检查用户问题是否包含“代码”，再通过条件边选择文字回答节点或代码回答节点，最后返回更新后的状态。
# START → classify → text_answer 或 code_answer → END
# BasicRouteState：定义图中传递的状态字段。
# classify_node：将分类结果写入 answer_type。
# route_answer_type：读取 answer_type，决定下一步执行哪个节点。
# text_answer_node / code_answer_node：分别生成对应类型的答案。
# build_graph()：注册节点和边，并编译成可调用的图。
# main()：用两个示例问题运行图并打印结果。



# 定义图中共享的状态结构。
class BasicRouteState(TypedDict):
    user_question: str  # 用户提出的问题
    answer_type: str    # 分类结果：文字回答或代码回答
    final_answer: str   # 节点生成的最终答案


# 分类节点：根据问题内容判断回答类型。
def classify_node(state: BasicRouteState) -> dict:
    if "代码" in state["user_question"]:
        return {"answer_type": "code"}  # 返回状态更新，表示需要代码回答

    return {"answer_type": "text"}  # 默认使用文字回答


# 条件路由函数：根据分类结果选择下一个节点。
def route_answer_type(
    state: BasicRouteState,
) -> Literal["text", "code"]:
    # type: ignore 用于抑制类型检查器对 str 与 Literal 类型不匹配的提示。
    return state["answer_type"]  # type: ignore[return-value]


# 文字回答节点：生成文字说明。
def text_answer_node(state: BasicRouteState) -> dict:
    return {
        "final_answer": "这是文字解释回答。"
    }


# 代码回答节点：生成代码示例说明。
def code_answer_node(state: BasicRouteState) -> dict:
    return {
        "final_answer": "这是代码示例回答。"
    }


# 创建并编译 LangGraph 工作流。
def build_graph():
    graph = StateGraph(BasicRouteState)  # 使用 BasicRouteState 作为图的状态类型

    # 注册节点：节点名称对应处理函数。
    graph.add_node("classify", classify_node)
    graph.add_node("text_answer", text_answer_node)
    graph.add_node("code_answer", code_answer_node)

    # 设置入口：从 START 开始执行分类节点。
    graph.add_edge(START, "classify")

    # 根据分类结果，从 classify 分支到对应的回答节点。
    graph.add_conditional_edges(
        "classify",
        route_answer_type,
        {
            "text": "text_answer",
            "code": "code_answer",
        },
    )

    # 两种回答节点执行完后都结束流程。
    graph.add_edge("text_answer", END)
    graph.add_edge("code_answer", END)

    return graph.compile()  # 编译图，生成可调用的应用


# 运行示例问题，并打印每次执行的结果。
def main():
    app = build_graph()

    questions = [
        "解释一下 LangGraph。",
        "给我一段 LangGraph 代码。",
    ]

    for question in questions:
        # invoke 会把初始状态传入图，并返回执行后的完整状态。
        result = app.invoke({
            "user_question": question,
            "answer_type": "",  # 等待分类节点填入
            "final_answer": "", # 等待回答节点填入
        })

        print("question:", question)
        print("answer_type:", result["answer_type"])
        print("final_answer:", result["final_answer"])
        print("=" * 80)


# 直接运行此文件时执行 main；作为模块导入时不自动运行。
if __name__ == "__main__":
    main()