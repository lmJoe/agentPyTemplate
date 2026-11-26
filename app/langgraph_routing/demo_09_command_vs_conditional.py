from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


# Command vs Conditional Edge  Command 用于直接指定下一个节点，而 Conditional Edge 则基于条件判断。
# conditional edge：
# 节点更新 State，路由函数决定下一步。

# Command：
# 一个节点同时更新 State 并指定下一步。


# 演示用 LangGraph 的 Command 同时完成更新状态和选择下一节点：
# START → router
#            ├─ 问题包含“退款” → 更新 intent 为 refund → refund_node → END
#            └─ 其他问题       → 更新 intent 为 general → general_node → END
# Command(update=..., goto=...)：`update` 写入状态，`goto` 指定后续执行的节点。
# command_router_node：判断问题是否包含“退款”，并通过 Command 直接路由。
# Literal["general_node", "refund_node"]：标注 goto 允许跳转到的节点名称，帮助类型检查器检查路由目标。
# general_node 和 refund_node：分别生成普通回答和退款回答。

# 定义这个示例图中传递的状态字段。
class CommandDemoState(TypedDict):
    user_question: str  # 用户提出的问题
    intent: str         # 路由器识别出的意图
    final_answer: str   # 目标节点生成的最终回答


# 根据用户问题判断意图，并直接指定下一个节点。
def command_router_node(
    state: CommandDemoState,
) -> Command[Literal["general_node", "refund_node"]]:
    question = state["user_question"]

    if "退款" in question:
        # update 用于更新图状态，goto 用于指定接下来执行的节点。
        return Command(
            update={"intent": "refund"},
            goto="refund_node",
        )

    # 未匹配到“退款”时，路由到普通回答节点。
    return Command(
        update={"intent": "general"},
        goto="general_node",
    )


# 普通问题的回答节点。
def general_node(state: CommandDemoState) -> dict:
    return {
        "final_answer": "Command 路由到了普通回答节点。"
    }


# 退款问题的回答节点。
def refund_node(state: CommandDemoState) -> dict:
    return {
        "final_answer": "Command 路由到了退款节点。"
    }


# 构建并编译流程图。
def build_graph():
    graph = StateGraph(CommandDemoState)  # 指定图中使用的状态类型

    # 注册路由节点和两个目标节点。
    graph.add_node("router", command_router_node)
    graph.add_node("general_node", general_node)
    graph.add_node("refund_node", refund_node)

    # 设置入口，从 router 节点开始。
    graph.add_edge(START, "router")

    # 两个目标节点执行后都结束流程。
    graph.add_edge("general_node", END)
    graph.add_edge("refund_node", END)

    return graph.compile()  # 编译图，得到可调用的应用


# 使用两个示例问题运行图并打印状态结果。
def main():
    app = build_graph()

    for question in ["你好", "我的订单可以退款吗？"]:
        result = app.invoke({
            "user_question": question,
            "intent": "",       # 等待路由节点填入意图
            "final_answer": "", # 等待目标节点生成回答
        })

        print("question:", question)
        print("intent:", result["intent"])
        print("final_answer:", result["final_answer"])
        print("=" * 80)


# 直接运行此文件时执行示例。
if __name__ == "__main__":
    main()