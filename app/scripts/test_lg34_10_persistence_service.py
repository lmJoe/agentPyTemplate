from app.langgraph_persistence.service import langgraph_persistence_service


def main():
    # 用于定位会话的租户、用户和会话标识。
    # 后续调用使用相同的三个值，才能继续同一条 LangGraph 线程。
    tenant_id = "tenant_001"
    user_id = "u_10001"
    conversation_id = "conv_refund_001"

    # 第一次调用：用户提出退款请求，启动退款流程
    first = langgraph_persistence_service.start_refund_flow(
        user_question="我要退款。",
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # 查看第一轮执行结果
    print("first:")
    print("final_answer:", first["final_answer"])  # 图生成的回答
    print("intent:", first["intent"])              # 识别出的用户意图
    print("waiting_for:", first["waiting_for"])    # 流程正在等待用户补充的信息
    print("=" * 80)

    # 第二次调用：提供订单号，继续之前的退款流程
    second = langgraph_persistence_service.continue_flow(
        user_question="订单号是 10002。",
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # 查看补充订单号后的执行结果
    print("second:")
    print("final_answer:", second["final_answer"])
    print("intent:", second["intent"])
    print("order_id:", second["order_id"])          # 提取或保存的订单号
    print("order_status:", second["order_status"])  # 查询或处理后的订单状态
    print("=" * 80)

    # 读取这条会话线程最近保存的状态快照
    current = langgraph_persistence_service.get_current_state(
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # 打印快照中的图状态数据
    print("current state:")
    print(current["values"])


# 直接运行此文件时，执行 main 函数
if __name__ == "__main__":
    main()