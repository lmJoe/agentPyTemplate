import asyncio

from app.langchain_agent_rag.factory import build_ecommerce_agent_with_rag
from app.langchain_agent_rag.index import ensure_rag_index


async def main():
    """准备知识库索引，并以流式方式运行电商客服 Agent。"""

    # 确保知识库索引已准备好。
    # 这是同步函数，所以这里不使用 await。
    ensure_rag_index()

    # 创建包含业务工具和知识库检索工具的 Agent。
    agent = build_ecommerce_agent_with_rag(
        provider="deepseek",
        model_name="deepseek-chat",
    )

    # 异步流式调用 Agent。
    # stream_mode="updates" 表示逐步获取 Agent 执行过程中的状态更新。
    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "我的订单 10002 还没发货，这种情况可以退款吗？",
                }
            ]
        },
        stream_mode="updates",
    ):
        # 输出当前收到的执行更新。
        print("chunk:")
        print(chunk)
        print("=" * 80)


if __name__ == "__main__":
    # 在脚本入口启动异步 main 函数。
    asyncio.run(main())