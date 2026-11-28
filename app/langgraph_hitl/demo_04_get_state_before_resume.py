from langgraph.types import Command

from app.langgraph_hitl.demo_03_edit_payload import build_graph


# 恢复前查看 State 快照，查看当前状态。
# 启动图并等待审核、通过 app.get_state(config) 查看暂停时的状态、再用 Command(resume=...) 提交审核结果并继续执行。

def main():
    # 创建图应用。build_graph() 中配置的 checkpointer 会保存运行状态。
    app = build_graph()

    # thread_id 标识本次图运行；查看状态和恢复运行时需使用相同的 config。
    config = {
        "configurable": {
            "thread_id": "thread_lg35_get_state_before_resume"
        }
    }

    # 首次运行图。执行到 interrupt(...) 时会暂停，等待人工审核。
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

    # 输出暂停时返回的中断信息，通常会包含待审核动作和参数。
    print("first interrupt:")
    print(first)

    print("=" * 80)
    print("人工审核前查看当前 State:")

    # 读取当前 thread 已保存的状态快照。
    # snapshot.values 包含图中各状态字段的当前值。
    snapshot = app.get_state(config)
    print(snapshot.values)

    print("=" * 80)
    print("人工审核通过后恢复:")

    # 向暂停点提交人工审核结果并恢复图运行。
    # 这个对象会作为 interrupt(...) 的返回值，之后图按 "approve" 分支继续。
    second = app.invoke(
        Command(resume={
            "type": "approve",
            "reviewer_id": "admin_001",
            "reason": "审核通过",
        }),
        config=config,
    )

    # 输出恢复执行后的结果。
    print(second)


if __name__ == "__main__":
    main()