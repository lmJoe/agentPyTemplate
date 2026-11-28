from app.langgraph_persistence.graph_factory import build_memory_graph
from app.langgraph_persistence.schemas import create_initial_state



# update_state 人工修正状态
# update_state 可以手动修改 thread 的状态
# 适合：
# 人工修正
# 调试
# 审批后写入结果
# 从外部系统回调更新状态


def main():
    # 创建使用内存检查点的 LangGraph 应用
    app = build_memory_graph()

    # 指定需要读取和更新的会话
    config = {
        "configurable": {
            "thread_id": "thread_update_state_demo"
        }
    }

    # 先运行工作流。由于问题中没有订单号，图会暂停在等待用户补充信息的状态
    app.invoke(
        create_initial_state("我要退款，但是忘记订单号了。"),
        config=config,
    )

    # 读取更新前的状态快照
    before = app.get_state(config)

    print("before:")
    print(before.values)

    print("=" * 80)

    # 手动更新该会话的状态：补上订单号并追加一条日志
    # update_state 会返回更新后检查点对应的配置
    updated_config = app.update_state(
        config,
        {
            "order_id": "10002",
            "logs": ["manual_update：人工补充 order_id=10002"],
        },
    )

    print("updated_config:")
    print(updated_config)

    print("=" * 80)

    # 再次读取状态，查看更新结果
    after = app.get_state(config)

    print("after:")
    print(after.values)


# 直接运行此文件时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main()