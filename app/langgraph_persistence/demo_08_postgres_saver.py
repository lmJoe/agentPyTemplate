from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import settings


from app.langgraph_persistence.graph_factory import build_persistence_graph
from app.langgraph_persistence.schemas import create_initial_state


# 演示了用 PostgreSQL 持久化 LangGraph 状态：
# 先建立数据库连接并准备检查点表，再用指定的 thread_id 运行对话，最后读取并打印该对话的检查点配置。
# 与内存保存器不同，PostgreSQL 中的检查点可以在程序退出后保留，供后续运行恢复。

# PostgreSQL 连接地址，包含用户名、密码、主机、端口和数据库名。
# 实际项目中建议通过环境变量或密钥管理服务读取，避免把凭据写在代码里。
# DB_URI = settings.database_url
DB_URI = "postgresql://postgres:l123456@192.168.2.93:5432/ai_agent"


def main():
    # thread_id 用于标识这段对话。
    # 使用相同的 thread_id 调用图，可以读取并延续该对话的检查点状态。
    config = {
        "configurable": {
            "thread_id": "thread_postgres_demo_001"
        }
    }

    # 建立 PostgreSQL 检查点保存器。
    # with 语句会在代码块结束后关闭相关连接资源。
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 首次使用时创建检查点所需的数据库表和结构。
        # 生产环境通常在部署或数据库迁移时执行，而不是每次处理请求都执行。
        checkpointer.setup()

        # 构建使用 PostgreSQL 保存和读取状态的 LangGraph 应用。
        app = build_persistence_graph(checkpointer=checkpointer)

        # 创建初始状态并运行图，处理用户关于订单 10002 是否可退款的问题。
        result = app.invoke(
            create_initial_state("我的订单 10002 可以退款吗？"),
            config=config,
        )

        # 打印图生成的最终答复。
        print("final_answer:")
        print(result["final_answer"])

        # 根据 thread_id 读取该对话最新的检查点快照。
        snapshot = app.get_state(config)

        # 打印检查点配置，查看与当前状态关联的线程等信息。
        print("=" * 80)
        print("checkpoint config:")
        print(snapshot.config)


# 只有直接运行这个 Python 文件时才执行 main()；
# 如果该文件被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()