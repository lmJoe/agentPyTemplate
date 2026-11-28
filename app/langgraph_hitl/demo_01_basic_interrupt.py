from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# 演示 LangGraph 的**人工介入（Human-in-the-Loop，HITL）**流程：
# 1. 第一次调用时，图从 START 进入 human_review 节点。
# 2. 节点运行到 interrupt(...) 后暂停，并输出待审核信息。
# 3. 外部人员或程序审核后，通过 Command(resume="approve") 恢复执行。
# 4. "approve" 成为 interrupt(...) 的返回值，节点据此生成 final_answer。
# 5. 图到达 END，返回更新后的状态。


# 定义图中流转的状态结构。
# user_question 保存待审核的问题，final_answer 保存审核后的结果。
class BasicHITLState(TypedDict):
    user_question: str
    final_answer: str


def human_review_node(state: BasicHITLState) -> dict:
    # interrupt 会暂停当前图的执行，并将这份数据交给外部程序或人工审核界面。
    # 暂停时，图的状态会由 checkpointer 保存，之后可通过 Command(resume=...) 恢复。
    decision = interrupt({
        "type": "human_review",  # 供调用方识别这是人工审核请求
        "question": state["user_question"],  # 提供需要审核的问题
        "message": "请人工审核这个回答是否可以继续。",
    })

    # 恢复执行后，decision 的值就是 Command(resume=...) 传入的内容。
    # 返回的字典会合并到图的状态中，更新 final_answer。
    return {
        "final_answer": f"人工审核结果：{decision}"
    }


def build_graph():
    # 创建使用 BasicHITLState 作为状态结构的图。
    graph = StateGraph(BasicHITLState)

    # 注册人工审核节点。
    graph.add_node("human_review", human_review_node)

    # 设置执行顺序：开始 -> 人工审核 -> 结束。
    graph.add_edge(START, "human_review")
    graph.add_edge("human_review", END)

    # 使用内存检查点保存中断时的执行状态。
    # 这样同一个 thread_id 才能在后续调用中恢复。
    checkpointer = InMemorySaver()

    # 编译图，并启用检查点功能。
    return graph.compile(checkpointer=checkpointer)


def main():
    app = build_graph()

    # thread_id 用于标识这次图执行。
    # 恢复执行时必须使用相同的 thread_id 和 checkpointer。
    config = {
        "configurable": {
            "thread_id": "thread_lg35_basic_interrupt"
        }
    }

    print("第一次执行，会在 interrupt 暂停：")

    # 第一次调用图。运行到 interrupt 时会暂停，并返回中断信息。
    first = app.invoke(
        {
            "user_question": "请帮我执行一个需要人工审核的动作。",
            "final_answer": "",
        },
        config=config,
    )

    print(first)

    print("=" * 80)
    print("第二次执行，用 Command(resume=...) 恢复：")

    # 用 Command(resume=...) 提供人工审核结果并恢复执行。
    # 这里传入 "approve"，恢复后它会成为 interrupt(...) 的返回值。
    second = app.invoke(
        Command(resume="approve"),
        config=config,
    )

    print(second)


if __name__ == "__main__":
    main()