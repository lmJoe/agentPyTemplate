from app.langgraph_persistence.graph_factory import build_memory_graph
from app.langgraph_persistence.schemas import create_initial_state

# get_state_history 查看历史状态


def main():
    # 创建使用内存检查点的 LangGraph 应用
    app = build_memory_graph()

    # 指定需要查看历史记录的会话 ID
    config = {
        "configurable": {
            "thread_id": "thread_history_demo"
        }
    }

    # 运行一次工作流；执行过程中产生的检查点会保存在内存中
    app.invoke(
        create_initial_state("我的订单 10002 可以退款吗？"),
        config=config,
    )

    # 获取该会话的检查点历史，并转为列表以便计算数量和遍历
    history = list(app.get_state_history(config))

    print("checkpoint count:", len(history))
    print("=" * 80)

    # 逐个查看检查点快照
    for index, snapshot in enumerate(history, start=1):
        print("snapshot:", index)

        # 显示当前快照关联的配置，以及当时待执行的节点
        print("checkpoint config:", snapshot.config)
        print("next:", snapshot.next)

        # values 保存该检查点对应的图状态
        values = snapshot.values
        print("intent:", values.get("intent"))
        print("order_id:", values.get("order_id"))
        print("order_status:", values.get("order_status"))
        print("final_answer:", values.get("final_answer"))
        print("-" * 80)


# 直接运行此文件时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main()