from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

# 演示了一个带审核与返工循环的 LangGraph 工作流：先生成草稿，审核后决定通过，或返回生成节点再改进一次。
# 执行过程
# 1. 首次运行 generate_draft_node，生成“很粗糙”的草稿。
# 2. review_node 检测到“粗糙”，将审核结果设为 "need_refine"，并把 retry_count 加到 1。
# 3. route_after_review 将流程送回 generate_draft_node。
# 4. 第二次生成较完整的草稿，审核通过后进入 finish_node。
# 5. finish_node 将草稿保存为 final_answer，工作流结束。
# recursion_limit 为图执行设置步数上限。这个示例的循环条件会在一次返工后通过；实际工作流中，审核规则若可能一直不通过，应设置明确的最大重试次数和兜底处理。


class LoopState(TypedDict):
    """草稿生成与审核循环中各节点共享的状态。"""

    user_question: str   # 用户的问题
    draft: str           # 当前生成的草稿
    review_result: str   # 审核结果，例如 need_refine 或 pass
    retry_count: int     # 已经返工的次数
    final_answer: str    # 最终答复


def generate_draft_node(state: LoopState) -> dict:
    """根据返工次数生成草稿。"""
    retry_count = state["retry_count"]

    # 首次生成较粗糙的草稿；返工后生成更完整的版本。
    if retry_count == 0:
        draft = "这是一个很粗糙的回答。"
    else:
        draft = "这是一个更完整、更清晰的回答。"

    return {
        "draft": draft
    }


def review_node(state: LoopState) -> dict:
    """检查草稿；首次遇到“粗糙”时要求返工。"""

    # 如果草稿含“粗糙”且还没有返工过，就更新审核结果和次数。
    if "粗糙" in state["draft"] and state["retry_count"] < 1:
        return {
            "review_result": "need_refine",
            "retry_count": state["retry_count"] + 1,
        }

    # 其他情况视为审核通过。
    return {
        "review_result": "pass"
    }


def route_after_review(
    state: LoopState,
) -> Literal["refine", "finish"]:
    """根据审核结果决定返工还是进入最终输出节点。"""
    if state["review_result"] == "need_refine":
        return "refine"

    return "finish"


def finish_node(state: LoopState) -> dict:
    """将审核通过的草稿写入最终答复。"""
    return {
        "final_answer": state["draft"]
    }


def build_graph():
    """构建并编译带条件循环的工作流。"""
    graph = StateGraph(LoopState)

    graph.add_node("generate_draft", generate_draft_node)
    graph.add_node("review", review_node)
    graph.add_node("finish", finish_node)

    # 首次执行：生成草稿，然后进入审核。
    graph.add_edge(START, "generate_draft")
    graph.add_edge("generate_draft", "review")

    # 审核不通过时回到生成节点；通过后进入 finish 节点。
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "refine": "generate_draft",
            "finish": "finish",
        },
    )

    graph.add_edge("finish", END)

    return graph.compile()


def main():
    """运行示例，并限制工作流最多递归执行的步数。"""
    app = build_graph()

    result = app.invoke(
        {
            "user_question": "解释一下 LangGraph Node 与 Edge。",
            "draft": "",
            "review_result": "",
            "retry_count": 0,
            "final_answer": "",
        },
        config={
            # 限制图的执行步数，避免意外的无限循环。
            "recursion_limit": 10
        },
    )

    print(result)


# 直接运行文件时执行 main()；作为模块导入时不自动运行。
if __name__ == "__main__":
    main()