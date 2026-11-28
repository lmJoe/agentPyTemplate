from langgraph.checkpoint.memory import InMemorySaver

from app.langgraph_persistence.graph_factory import (
    add_user_message_to_state,
    build_persistence_graph,
)
from app.langgraph_persistence.schemas import create_initial_state

# 演示了基于检查点恢复对话状态的流程：
# 1. 创建 InMemorySaver，在内存中保存图的状态。
# 2. 使用固定的 thread_id 发起第一轮对话。用户没有提供订单号时，图可以记录当前状态并请求补充信息。
# 3. 用相同的 thread_id 发送第二条消息，图从保存的状态继续处理，获取订单号 10002。
# 4. 打印最终答复、订单相关字段、消息记录和执行日志。
# 第一轮用户只说：我要退款。
# Graph 没找到订单号，于是保存状态：
# intent=refund
# need_user_input=True
# waiting_for=order_id
# 第二轮用户说：订单号是 10002。
# 因为使用同一个 thread_id，Graph 还记得上一轮 intent 是 refund。
# 所以它可以继续走退款流程，而不是把“订单号是 10002”当成一个孤立问题。
# 这就是 Persistence 在业务里的价值。

# InMemorySaver 的限制
# 1. 简单
# 2. 不需要数据库
# 3. 适合本地测试
# 4. 进程重启数据会丢
# 5. 不适合生产环境


def main():
    # 创建内存检查点保存器，用来暂存图的运行状态。
    # 同一个 checkpointer 和 thread_id 配合使用，才能让第二次调用接着第一次的对话继续。
    checkpointer = InMemorySaver()

    # 构建带有持久化能力的 LangGraph 应用。
    app = build_persistence_graph(checkpointer=checkpointer)

    # thread_id 是这段对话的标识。
    # 后续使用相同的 thread_id 调用图时，可以读取之前保存的状态。
    config = {
        "configurable": {
            "thread_id": "thread_ecommerce_resume_demo"
        }
    }

    # 开始一轮新对话：用户只说“我要退款”，没有提供订单号。
    # create_initial_state 用于创建图所需的初始状态。
    first_result = app.invoke(
        create_initial_state("我要退款。"),
        config=config,
    )

    # 输出第一轮处理结果，观察图是否识别出退款意图并等待用户提供订单号。
    print("first_result:")
    print("final_answer:", first_result["final_answer"])
    print("intent:", first_result["intent"])
    print("need_user_input:", first_result["need_user_input"])
    print("waiting_for:", first_result["waiting_for"])
    print("order_id:", first_result["order_id"])
    print("=" * 80)

    # 添加用户的后续消息，并沿用相同的 config/thread_id。
    # 图会基于已保存的对话状态继续处理，而不是重新开始。
    second_result = app.invoke(
        add_user_message_to_state("订单号是 10002。"),
        config=config,
    )

    # 输出第二轮结果，检查图是否提取订单号并继续处理退款请求。
    print("second_result:")
    print("final_answer:", second_result["final_answer"])
    print("intent:", second_result["intent"])
    print("need_user_input:", second_result["need_user_input"])
    print("waiting_for:", second_result["waiting_for"])
    print("order_id:", second_result["order_id"])
    print("order_status:", second_result["order_status"])

    # 打印完整消息列表，查看用户与图中各节点产生的消息。
    print("=" * 80)
    print("messages:")
    for message in second_result["messages"]:
        print(message.type, ":", message.content)

    # 打印图执行过程中记录的日志，便于了解状态变化和处理步骤。
    print("=" * 80)
    print("logs:")
    for log in second_result["logs"]:
        print("-", log)


# 只有直接运行这个 Python 文件时才执行 main()；
# 如果该文件被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()