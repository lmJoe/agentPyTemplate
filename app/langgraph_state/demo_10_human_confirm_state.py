from typing import Literal, TypedDict

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph


# 示例退款金额是 899.0：
# 1. assess_risk_node 判断金额大于等于 500，将风险设为 "high"。
# 2. 状态被标记为需要人工确认，确认状态设为 "pending"。
# 3. 订单号、退款金额和审核原因被放入 human_confirm_payload。
# 4. generate_answer_node 发现需要人工确认，生成提示用户等待人工客服处理的回复。
# 5. print(result) 打印工作流运行后的完整状态。
# StateGraph 按照 add_edge 指定的顺序执行节点。每个节点返回一个字典，LangGraph 会把这些字段更新到共享状态中。



class RefundConfirmState(TypedDict):
    """退款审核流程中各节点共享的状态。"""

    user_question: str

    # 订单号可能尚未提取到。
    order_id: str | None

    # 本次申请的退款金额。
    refund_amount: float

    # 风险等级只能是这三个值之一。
    risk_level: Literal["low", "medium", "high"]

    # 是否需要人工确认。
    need_human_confirm: bool

    # 人工确认状态：未涉及、待确认、已批准或已拒绝。
    human_confirm_status: Literal["none", "pending", "approved", "rejected"]

    # 等待执行或确认的操作，例如退款订单。
    pending_action: str | None

    # 提交给人工审核的上下文信息。
    human_confirm_payload: dict | None

    # 面向用户的最终回复。
    final_answer: str


def assess_risk_node(state: RefundConfirmState) -> dict:
    """按退款金额评估风险，并更新审核相关状态。"""
    refund_amount = state["refund_amount"]

    # 示例规则：退款金额达到 500 时，需要人工审核。
    if refund_amount >= 500:
        return {
            "risk_level": "high",
            "need_human_confirm": True,
            "human_confirm_status": "pending",
            "pending_action": "refund_order",

            # 将订单号、金额和审核原因打包，供后续审核流程使用。
            "human_confirm_payload": {
                "order_id": state["order_id"],
                "refund_amount": refund_amount,
                "reason": "大额退款需要人工确认",
            },
        }

    # 未达到阈值时，按低风险处理，不需要人工确认。
    return {
        "risk_level": "low",
        "need_human_confirm": False,
        "human_confirm_status": "none",
    }


def generate_answer_node(state: RefundConfirmState) -> dict:
    """根据风险评估结果生成用户可见的答复。"""
    if state["need_human_confirm"]:
        return {
            "final_answer": "该退款金额较高，需要人工客服确认后才能继续处理。"
        }

    return {
        "final_answer": "该退款金额较低，可以进入自动退款流程。"
    }


def build_graph():
    """构建并编译退款审核工作流。"""
    graph = StateGraph(RefundConfirmState)

    # 注册风险评估和回复生成节点。
    graph.add_node("assess_risk", assess_risk_node)
    graph.add_node("generate_answer", generate_answer_node)

    # 设置执行顺序：开始 -> 风险评估 -> 生成回复 -> 结束。
    graph.add_edge(START, "assess_risk")
    graph.add_edge("assess_risk", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


def main():
    """运行一个退款金额为 899 元的示例。"""
    app = build_graph()

    # invoke() 将初始状态传入图中。
    # 示例金额 899 元，大于等于 500 元，因此会进入待人工确认状态。
    result = app.invoke({
        "user_question": "我要申请退款。",
        "order_id": "10002",
        "refund_amount": 899.0,
        "risk_level": "low",
        "need_human_confirm": False,
        "human_confirm_status": "none",
        "pending_action": None,
        "human_confirm_payload": None,
        "final_answer": "",
    })

    # 打印运行后的完整状态，包括风险等级、审核信息和最终回复。
    print(result)


# 直接运行此文件时执行 main()；被其他模块导入时不自动运行。
if __name__ == "__main__":
    main()