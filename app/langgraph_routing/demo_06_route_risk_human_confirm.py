from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import create_initial_state
from app.langgraph_routing.schemas import RoutingState

# 风险评估触发人工确认
# START → 评估风险
#              ├─ 需要人工确认 → 提示等待人工处理 → END
#              └─ 无需人工确认 → 提示可自动处理 → END
# assess_risk_node：用简单关键词规则评估风险，并更新风险级别、人工确认标记和待处理动作。
# route_after_risk：读取 need_human_confirm，选择后续分支。
# human_confirm_node 和 auto_answer_node：分别生成对应的提示。
# build_graph()：注册节点和流程边，并编译 LangGraph。
# main()：用普通退款和大额退款问题演示两种分支。



# 根据用户问题评估操作风险，并决定是否需要人工确认。
def assess_risk_node(state: RoutingState) -> dict:
    question = state["user_question"]

    # 示例规则：问题中包含“大额”或“1000”时，标记为高风险。
    if "大额" in question or "1000" in question:
        return {
            "risk_level": "high",              # 风险级别
            "need_human_confirm": True,        # 需要人工确认
            "pending_action": "refund_order",  # 暂缓执行的动作
            "logs": ["assess_risk：高风险，需要人工确认"],
        }

    # 未触发高风险规则时，按低风险处理。
    return {
        "risk_level": "low",
        "need_human_confirm": False,
        "pending_action": None,  # 没有等待确认的动作
        "logs": ["assess_risk：低风险，可自动处理"],
    }


# 根据风险评估结果，选择人工确认或自动处理分支。
def route_after_risk(
    state: RoutingState,
) -> Literal["human_confirm", "auto_answer"]:
    if state["need_human_confirm"]:
        return "human_confirm"

    return "auto_answer"


# 高风险分支：告知用户需要人工确认。
def human_confirm_node(state: RoutingState) -> dict:
    return {
        "final_answer": "该操作风险较高，需要人工客服确认后继续处理。",
        "is_finished": True,  # 当前流程结束，等待人工后续处理
        "logs": ["human_confirm：等待人工确认"],
    }


# 低风险分支：告知用户请求可以继续自动处理。
def auto_answer_node(state: RoutingState) -> dict:
    return {
        "final_answer": "该请求风险较低，可以继续自动处理。",
        "is_finished": True,
        "logs": ["auto_answer：自动处理"],
    }


# 构建并编译风险评估流程图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中共享状态的结构

    # 注册风险评估和两种处理结果节点。
    graph.add_node("assess_risk", assess_risk_node)
    graph.add_node("human_confirm", human_confirm_node)
    graph.add_node("auto_answer", auto_answer_node)

    # 设置入口，从风险评估节点开始。
    graph.add_edge(START, "assess_risk")

    # 根据风险评估结果选择后续节点。
    graph.add_conditional_edges(
        "assess_risk",
        route_after_risk,
        {
            "human_confirm": "human_confirm",
            "auto_answer": "auto_answer",
        },
    )

    # 两种处理节点执行后都结束流程。
    graph.add_edge("human_confirm", END)
    graph.add_edge("auto_answer", END)

    return graph.compile()  # 编译图，得到可调用的应用


# 运行示例问题，并打印风险评估及处理结果。
def main():
    app = build_graph()

    questions = [
        "我要退款。",
        "我要申请大额退款 1000 元。",
    ]

    for question in questions:
        # 创建初始状态并运行流程图。
        result = app.invoke(create_initial_state(question))

        print("question:", question)
        print("risk_level:", result["risk_level"])
        print("need_human_confirm:", result["need_human_confirm"])
        print("final_answer:", result["final_answer"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时执行示例。
if __name__ == "__main__":
    main()