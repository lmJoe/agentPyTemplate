from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# approve / reject
# 第一次图在 review_action 暂停。
# 人工审核后传：
# Command(resume={
#     "type": "approve"
# })
# 如果 approve，就进入 execute_action。
# 如果 reject，就进入 reject_action。
# 这就是审批分支。

# 段代码展示了一个带审批和拒绝分支的人工审核流程：
# 1. 第一次调用时，`review_action_node` 通过 interrupt(...) 暂停，并提交动作名称、参数和可选决定。
# 2. 审核人提交结果后，第二次调用用 Command(resume=...) 恢复执行。
# 3. route_after_review 检查 human_decision["type"]：
#    - 为 "approve" 时，进入 execute_action_node。
#    - 其他值时，进入 reject_action_node。
# 4. 两个分支都会写入 final_answer，然后结束。



# 定义图中流转的状态。
class ApproveRejectState(TypedDict):
    action_name: str            # 待审核的动作名称
    action_payload: dict        # 执行动作需要的参数
    human_decision: dict | None # 人工审核结果；中断前为 None
    final_answer: str           # 执行或拒绝后的说明


def review_action_node(state: ApproveRejectState) -> dict:
    # 暂停图的执行，并把动作信息交给外部审核流程。
    # 图会等待调用方通过 Command(resume=...) 提交审核结果。
    decision = interrupt({
        "type": "review_action",
        "action_name": state["action_name"],
        "action_payload": state["action_payload"],
        "options": ["approve", "reject"],
    })

    # 恢复后，decision 就是 Command(resume=...) 传入的值。
    return {
        "human_decision": decision
    }


def route_after_review(
    state: ApproveRejectState,
) -> Literal["approved", "rejected"]:
    # 根据人工决定选择后续分支。
    decision = state["human_decision"] or {}

    if decision.get("type") == "approve":
        return "approved"

    # 任何不是 approve 的结果都会走拒绝分支。
    return "rejected"


def execute_action_node(state: ApproveRejectState) -> dict:
    # 审批通过后进入此节点。
    # 当前示例只生成执行说明，并没有真正调用退款接口。
    return {
        "final_answer": (
            f"人工已审批通过，开始执行动作：{state['action_name']}，"
            f"参数：{state['action_payload']}"
        )
    }


def reject_action_node(state: ApproveRejectState) -> dict:
    # 审批拒绝后进入此节点，并读取审核人填写的原因。
    decision = state["human_decision"] or {}

    return {
        "final_answer": (
            "人工已拒绝执行该动作。"
            f"原因：{decision.get('reason', '未填写')}"
        )
    }


def build_graph():
    # 创建使用 ApproveRejectState 作为状态结构的图。
    graph = StateGraph(ApproveRejectState)

    # 注册审核、审批通过和拒绝三个节点。
    graph.add_node("review_action", review_action_node)
    graph.add_node("execute_action", execute_action_node)
    graph.add_node("reject_action", reject_action_node)

    # 图从审核节点开始。
    graph.add_edge(START, "review_action")

    # 审核节点完成后，根据审核结果选择对应分支。
    graph.add_conditional_edges(
        "review_action",
        route_after_review,
        {
            "approved": "execute_action",
            "rejected": "reject_action",
        },
    )

    # 两个分支执行完毕后结束图。
    graph.add_edge("execute_action", END)
    graph.add_edge("reject_action", END)

    # 保存暂停时的执行状态，以便稍后恢复。
    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


def main():
    app = build_graph()

    # thread_id 用来标识这次图执行。
    # 恢复时需要使用相同的 thread_id。
    config = {
        "configurable": {
            "thread_id": "thread_lg35_approve_reject"
        }
    }

    # 第一次调用：图运行到 interrupt 后暂停，并返回待审核信息。
    first = app.invoke(
        {
            "action_name": "refund_order",
            "action_payload": {
                "order_id": "10002",
                "amount": 199.0,
            },
            "human_decision": None,
            "final_answer": "",
        },
        config=config,
    )

    print("first:")
    print(first)

    print("=" * 80)

    # 第二次调用：提交人工审核结果，恢复同一个图执行。
    # 这个字典会成为 interrupt(...) 的返回值。
    second = app.invoke(
        Command(resume={
            "type": "approve",
            "reviewer_id": "admin_001",
            "reason": "订单未发货，可以退款",
        }),
        config=config,
    )

    print("second:")
    print(second)


if __name__ == "__main__":
    main()