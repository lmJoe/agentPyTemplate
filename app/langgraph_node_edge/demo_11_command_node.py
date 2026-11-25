from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
# Command 用于在节点返回时同时更新状态并指定后续节点。
from langgraph.types import Command

# Command Node:Command 可以让 Node 同时做两件事：更新 State，指定下一步 goto
# 但是要注意，不要在同一个节点上又返回 Command，又给它加普通静态边。
# 否则可能会出现两个后续节点都执行的情况。
# 官方 Graph API 文档明确提醒，如果节点返回 Command(goto=...)，同时又配置了普通 add_edge，两个目标都可能运行，因此每个节点应该选择一种路由方式。


# 演示了用 LangGraph 的 Command 在节点中同时更新状态并决定下一步路由。路由节点判断问题是否包含“退款”，然后直接转到普通问题节点或退款处理节点。
# 执行流程
# 每个问题都会先进入 router_node。该节点返回的 Command 包含两部分：
# - update：要写入共享状态的字段，例如把 intent 更新为 "refund"。
# - goto：下一步要执行的节点名称，例如 "refund_node"。
# 因此，普通问题会进入 general_node，包含“退款”的问题会进入 refund_node。两个处理节点生成答复后，流程结束。

# 与单独使用条件边相比，`Command` 把状态更新和路由选择放在同一个节点返回值里。当前示例只做关键词判断，处理节点也只是返回固定文本。


class CommandRouteState(TypedDict):
    """条件路由工作流中各节点共享的状态。"""

    user_question: str   # 用户输入的问题
    intent: str          # 识别出的意图
    final_answer: str    # 最终答复


def router_node(
    state: CommandRouteState,
) -> Command[Literal["general_node", "refund_node"]]:
    """判断用户意图，并直接指定要执行的节点。"""
    question = state["user_question"]

    # 包含“退款”时，更新意图并跳转到退款处理节点。
    if "退款" in question:
        return Command(
            update={
                "intent": "refund"
            },
            goto="refund_node",
        )

    # 其他问题按普通问题处理。
    return Command(
        update={
            "intent": "general"
        },
        goto="general_node",
    )


def general_node(state: CommandRouteState) -> dict:
    """生成普通问题的答复。"""
    return {
        "final_answer": "这是普通问题。"
    }


def refund_node(state: CommandRouteState) -> dict:
    """生成退款问题的答复。"""
    return {
        "final_answer": "这是退款问题，需要进入订单和售后规则流程。"
    }


def build_graph():
    """构建并编译使用 Command 路由的工作流。"""
    graph = StateGraph(CommandRouteState)

    # 注册路由节点及两个目标处理节点。
    graph.add_node("router", router_node)
    graph.add_node("general_node", general_node)
    graph.add_node("refund_node", refund_node)

    # 所有问题先进入 router。
    graph.add_edge(START, "router")

    # 两个处理节点完成后都结束流程。
    graph.add_edge("general_node", END)
    graph.add_edge("refund_node", END)

    return graph.compile()


def main():
    """分别运行普通问题和退款问题，并打印结果。"""
    app = build_graph()

    for question in ["你好", "我的订单可以退款吗？"]:
        result = app.invoke({
            "user_question": question,
            "intent": "unknown",
            "final_answer": "",
        })

        print("question:", question)
        print(result)
        print("=" * 80)


# 直接运行此文件时执行 main()；被导入时不自动执行。
if __name__ == "__main__":
    main()