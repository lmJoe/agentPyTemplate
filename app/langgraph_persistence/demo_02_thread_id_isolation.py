from app.langgraph_persistence.graph_factory import build_memory_graph
from app.langgraph_persistence.schemas import create_initial_state

# 演示如何用同一个图实例处理两个独立会话。`run_once` 接收图实例、会话 ID 和用户问题，构造包含 thread_id 的配置后调用 app.invoke()，再打印意图、订单号和最终答复


def run_once(app, thread_id: str, question: str):
    """使用指定的会话 ID 运行一次工作流，并打印处理结果。"""
    # thread_id 用于区分不同会话的检查点
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # 把用户问题转换为初始状态，并运行 LangGraph
    result = app.invoke(
        create_initial_state(question),
        config=config,
    )

    # 打印会话标识、输入问题以及工作流处理结果
    print("thread_id:", thread_id)
    print("question:", question)
    print("intent:", result["intent"])
    print("order_id:", result["order_id"])
    print("final_answer:", result["final_answer"])
    print("=" * 80)


def main():
    # 创建一个带内存检查点的图实例
    app = build_memory_graph()

    # 用 thread_user_a 处理一个订单咨询
    run_once(
        app,
        "thread_user_a",
        "我的订单 10002 可以退款吗？",
    )

    # 用 thread_user_b 处理另一个订单咨询
    run_once(
        app,
        "thread_user_b",
        "我的订单 10001 可以退款吗？",
    )


# 直接运行此文件时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main() 