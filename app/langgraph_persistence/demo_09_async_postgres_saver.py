import asyncio

# 用于将 LangGraph 的检查点保存在 PostgreSQL 中的异步存储器
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# 项目中的图构建函数和初始状态创建函数
from app.langgraph_persistence.graph_factory import build_persistence_graph
from app.langgraph_persistence.schemas import create_initial_state


# AsyncPostgresSaver 异步版本
# FastAPI 项目里，推荐用：AsyncPostgresSaver，因为我们的接口大多是 async。
# 使用这个写法更适合异步服务。
# async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
#     await checkpointer.setup()

# 主要流程
# 1. 设置 PostgreSQL 连接地址和 thread_id。
# 2. 创建异步检查点存储器，并初始化数据库结构。
# 3. 构建接入该存储器的 LangGraph 应用。
# 4. 执行订单查询流程，并打印最终回答。
# 5. 根据 thread_id 读取并打印保存的状态快照配置。



# PostgreSQL 连接字符串
DB_URI = "postgresql://postgres:l123456@192.168.2.93:5432/ai_agent"


async def main():
    # LangGraph 使用 thread_id 标识一段对话或一条运行线程。
    # 相同的 thread_id 可用于后续读取或继续该线程的状态。
    config = {
        "configurable": {
            "thread_id": "thread_async_postgres_demo_001"
        }
    }

    # 创建异步 PostgreSQL 检查点存储器，并在代码块结束后自动关闭连接
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 首次使用时初始化检查点所需的数据库表结构。
        # 在生产环境中，通常会把这一步放到应用启动初始化或数据库迁移流程中。
        await checkpointer.setup()

        # 构建一个使用 PostgreSQL 检查点存储器的 LangGraph 应用
        app = build_persistence_graph(checkpointer=checkpointer)

        # 创建初始状态，并异步执行图。
        # 执行过程中产生的状态会按配置保存到检查点中。
        result = await app.ainvoke(
            create_initial_state("我的订单 10002 可以退款吗？"),
            config=config,
        )

        # 输出图执行后生成的最终回答
        print("final_answer:")
        print(result["final_answer"])

        # 根据 thread_id 读取该线程最近保存的状态快照
        snapshot = await app.aget_state(config)

        print("=" * 80)
        print("checkpoint config:")
        # 输出快照关联的配置，通常包含线程标识等信息
        print(snapshot.config)


# 直接运行此文件时，通过 asyncio 启动异步主函数
if __name__ == "__main__":
    asyncio.run(main())