from app.langgraph_persistence.graph_factory import build_memory_graph
from app.langgraph_persistence.schemas import create_initial_state


# InMemorySaver 最小使用
# 这段代码是工作流的运行入口。它创建带内存检查点的图，为对话配置 thread_id，再将用户问题转换为初始状态并调用 app.invoke() 执行。
# 对于示例问题“我的订单 10002 可以退款吗？”，工作流会提取订单号、查询订单状态、匹配售后规则并生成答复。最后代码打印最终答复和节点日志，方便查看处理结果与执行过程。


def main():
    # 创建使用内存检查点的 LangGraph 应用
    app = build_memory_graph()

    # 为本次对话指定 thread_id。
    # 使用同一个 checkpointer 和 thread_id 运行图时，
    # LangGraph 可以找到该对话对应的检查点。
    config = {
        "configurable": {
            "thread_id": "thread_lg34_demo_001"
        }
    }

    # 创建初始状态并运行工作流
    result = app.invoke(
        create_initial_state("我的订单 10002 可以退款吗？"),
        config=config,
    )

    # 输出工作流生成的最终答复
    print("final_answer:")
    print(result["final_answer"])

    # 输出各节点执行时记录的日志
    print("=" * 80)
    print("logs:")
    for log in result["logs"]:
        print("-", log)


# 直接运行此脚本时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main()