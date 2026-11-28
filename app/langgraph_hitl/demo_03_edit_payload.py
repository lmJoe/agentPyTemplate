from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# 人工修改参数 edit
# EditPayloadState 描述图中传递的状态，包括待审核参数、人工决定和最终结果。
# review_payload_node 用 interrupt(...) 暂停流程，并提供审核所需的信息。
# Command(resume=...) 恢复暂停的流程，并把人工决定传回审核节点。
# route_after_review 根据决定类型选择分支：`approve` 使用原参数，`edit` 使用修改后的参数，其他情况走拒绝分支。
# InMemorySaver 保存暂停期间的状态；这里的 thread_id 用来找到并恢复对应运行。

# 定义图中共享状态的结构。
# TypedDict 用于描述状态字段及其类型，不会在运行时自动校验字段值。
class EditPayloadState(TypedDict):
    pending_action: str       # 待执行的动作名称，例如 "refund_order"
    pending_payload: dict     # 原始动作参数
    human_decision: dict | None  # 人工审核结果；尚未审核时为 None
    final_payload: dict | None   # 最终采用的参数；拒绝时为 None
    final_answer: str            # 流程结束时生成的说明


def review_payload_node(state: EditPayloadState) -> dict:
    """向人工审核者展示待审核动作和参数，并暂停流程等待回复。"""

    # interrupt 会暂停图的执行，并把这个对象作为中断信息返回给调用方。
    # 恢复执行时，Command(resume=...) 中的内容会成为 decision 的值。
    decision = interrupt({
        "type": "review_payload",
        "pending_action": state["pending_action"],
        "pending_payload": state["pending_payload"],
        "options": ["approve", "reject", "edit"],
        "message": "请审核动作参数，可以同意、拒绝或修改。",
    })

    # 将人工回复写入共享状态，供后续路由节点和处理节点读取。
    return {
        "human_decision": decision
    }


def route_after_review(
    state: EditPayloadState,
) -> Literal["approved", "edited", "rejected"]:
    """根据人工决定选择后续分支。"""

    decision = state["human_decision"] or {}
    decision_type = decision.get("type")

    if decision_type == "approve":
        return "approved"

    if decision_type == "edit":
        return "edited"

    # 未识别的决定也会进入拒绝分支，避免继续使用未经确认的参数。
    return "rejected"


def use_original_payload_node(state: EditPayloadState) -> dict:
    """人工同意时，采用原始参数。"""

    return {
        "final_payload": state["pending_payload"],
        "final_answer": f"使用原始参数执行：{state['pending_payload']}",
    }


def use_edited_payload_node(state: EditPayloadState) -> dict:
    """人工修改时，采用回复中提供的 edited_payload。"""

    decision = state["human_decision"] or {}
    edited_payload = decision.get("edited_payload") or {}

    return {
        "final_payload": edited_payload,
        "final_answer": f"使用人工修改后的参数执行：{edited_payload}",
    }


def reject_node(state: EditPayloadState) -> dict:
    """人工拒绝时，不设置最终参数，并记录拒绝原因。"""

    decision = state["human_decision"] or {}

    return {
        "final_payload": None,
        "final_answer": f"人工拒绝执行。原因：{decision.get('reason', '未填写')}",
    }


def build_graph():
    """创建并编译包含人工审核流程的 LangGraph。"""

    graph = StateGraph(EditPayloadState)

    # 注册节点：审核、采用原参数、采用修改参数、拒绝。
    graph.add_node("review_payload", review_payload_node)
    graph.add_node("use_original_payload", use_original_payload_node)
    graph.add_node("use_edited_payload", use_edited_payload_node)
    graph.add_node("reject", reject_node)

    # 图的入口是人工审核节点。
    graph.add_edge(START, "review_payload")

    # 审核节点结束后，根据 human_decision 的 type 选择处理分支。
    graph.add_conditional_edges(
        "review_payload",
        route_after_review,
        {
            "approved": "use_original_payload",
            "edited": "use_edited_payload",
            "rejected": "reject",
        },
    )

    # 每个处理分支执行完后结束流程。
    graph.add_edge("use_original_payload", END)
    graph.add_edge("use_edited_payload", END)
    graph.add_edge("reject", END)

    # 检查点用于保存图的状态，使流程暂停后可以继续。
    # InMemorySaver 只把数据保存在内存中，适合示例和短期运行。
    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


def main():
    app = build_graph()

    # thread_id 用于标识一次可恢复的图运行。
    # 恢复时需使用相同的 thread_id 和 checkpointer。
    config = {
        "configurable": {
            "thread_id": "thread_lg35_edit_payload"
        }
    }

    # 首次调用：图从 START 进入审核节点，执行到 interrupt 后暂停。
    first = app.invoke(
        {
            "pending_action": "refund_order",
            "pending_payload": {
                "order_id": "10002",
                "amount": 199.0,
                "reason": "用户申请未发货退款",
            },
            "human_decision": None,
            "final_payload": None,
            "final_answer": "",
        },
        config=config,
    )

    print("first:")
    print(first)

    print("=" * 80)

    # 恢复已暂停的流程，并将人工审核结果传给 interrupt。
    # type 为 "edit"，因此后续会进入 use_edited_payload 节点。
    second = app.invoke(
        Command(resume={
            "type": "edit",
            "reviewer_id": "admin_001",
            "reason": "优惠券不可退，只退实付金额",
            "edited_payload": {
                "order_id": "10002",
                "amount": 149.0,
                "reason": "人工修改为仅退实付金额",
            },
        }),
        config=config,
    )

    print("second:")
    print(second)


if __name__ == "__main__":
    main()