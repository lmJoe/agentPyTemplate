from app.langgraph_persistence.graph_factory import build_memory_graph
from app.langgraph_persistence.schemas import create_initial_state


# 代码演示如何查看 LangGraph 保存的状态快照：
# 1. 创建带 InMemorySaver 检查点的图，并指定 thread_id。
# 2. 调用 app.invoke() 执行工作流，让图保存运行状态。
# 3. 调用 app.get_state(config) 获取该会话最近一次检查点。
# 4. 打印快照的状态值、后续待执行节点和关联配置。

def main():
    # 创建使用内存检查点的 LangGraph 应用
    app = build_memory_graph()

    # 指定要读取状态的会话 ID
    config = {
        "configurable": {
            "thread_id": "thread_get_state_demo"
        }
    }

    # 运行一次工作流，执行后的状态会由 checkpointer 保存
    app.invoke(
        create_initial_state("我的订单 10002 可以退款吗？"),
        config=config,
    )

    # 根据 thread_id 读取该会话最近一次保存的状态快照
    snapshot = app.get_state(config)

    # values 包含当前状态字段及其值
    print("snapshot values:")
    print(snapshot.values)

    # next 表示快照对应的下一步节点；
    # 工作流正常结束后通常为空元组
    print("=" * 80)
    print("next:")
    print(snapshot.next)

    # config 包含该快照关联的运行配置和会话信息
    print("=" * 80)
    print("config:")
    print(snapshot.config)


# 直接运行此文件时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main()