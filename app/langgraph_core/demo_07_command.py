from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


# 这段代码用 LangGraph 实现了一个简单的客服问题路由流程：
# 1. router_node 检查用户问题是否包含“退款”。
# 2. 它返回 Command，一次完成两件事：
#    - 用 update 更新状态中的 intent。
#    - 用 goto 指定下一步执行的节点。
# 3. 普通问题进入 general_node；退款问题进入 refund_node。
# 4. 处理节点写入 answer，随后工作流结束。
# 这里的 Command 把状态更新和流程跳转放在同一个返回值里。当前路由只检查“退款”关键词，退款节点也只是返回示例回复，还没有查询订单或规则系统。



class CommandState(TypedDict):
    """定义工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题
    intent: str         # 识别出的意图，例如 general 或 refund
    answer: str         # 处理节点生成的回复


def router_node(
    state: CommandState,
) -> Command[Literal["general_node", "refund_node"]]:
    """识别用户意图，并用 Command 同时更新状态和指定下一节点。"""
    question = state["user_question"]

    if "退款" in question:
        # 将 intent 更新为 refund，并跳转到退款处理节点
        return Command(
            update={"intent": "refund"},
            goto="refund_node",
        )

    # 未检测到“退款”关键词时，按普通问题处理
    return Command(
        update={"intent": "general"},
        goto="general_node",
    )


def general_node(state: CommandState) -> dict:
    """处理普通问题，并写入回复。"""
    return {
        "answer": "这是普通问题。"
    }


def refund_node(state: CommandState) -> dict:
    """处理退款问题，并写入回复。"""
    return {
        "answer": "这是退款问题，后续需要查询订单状态和退款规则。"
    }


def build_graph():
    """创建并编译客服问题路由工作流。"""
    graph = StateGraph(CommandState)

    # 注册路由节点和两个问题处理节点
    graph.add_node("router", router_node)
    graph.add_node("general_node", general_node)
    graph.add_node("refund_node", refund_node)

    # 工作流从 router 开始；router 通过 Command 选择后续节点
    graph.add_edge(START, "router")

    # 两个处理节点完成后结束工作流
    graph.add_edge("general_node", END)
    graph.add_edge("refund_node", END)

    return graph.compile()


def main():
    """运行普通问题和退款问题两个示例。"""
    app = build_graph()

    for question in ["你好", "我的订单可以退款吗？"]:
        # 每次调用都传入一份初始状态
        result = app.invoke({
            "user_question": question,
            "intent": "",
            "answer": "",
        })

        print("question:", question)
        print(result)
        print("=" * 80)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()