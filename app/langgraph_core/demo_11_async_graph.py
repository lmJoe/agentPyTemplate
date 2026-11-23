import asyncio
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# 这段代码演示了 LangGraph 的异步工作流调用方式：
# - async_answer_node 是异步节点，用 async def 定义，并用 await 模拟异步操作。
# - app.ainvoke(...) 异步运行整个工作流，返回最终状态。
# - app.astream(...) 异步流式运行工作流；`async for` 会逐步读取节点产生的更新。
# - asyncio.run(main()) 启动事件循环来执行异步主函数。
# 实际项目中，异步节点适合调用异步网络接口、数据库或其他支持异步的服务。`asyncio.sleep(0.1)` 在这里仅用于演示。



class AsyncState(TypedDict):
    """定义异步工作流中共享的状态结构。"""

    user_question: str  # 用户提出的问题
    answer: str         # 异步节点生成的回答


async def async_answer_node(state: AsyncState) -> dict:
    """异步处理问题，并返回生成的回答。"""

    # 模拟异步操作，例如等待网络请求或调用外部服务
    await asyncio.sleep(0.1)

    return {
        "answer": f"异步节点已经处理完成：{state['user_question']}"
    }


def build_graph():
    """创建并编译包含异步节点的工作流。"""
    graph = StateGraph(AsyncState)

    # 注册异步回答节点
    graph.add_node("async_answer", async_answer_node)

    # 设置执行顺序：开始 → async_answer → 结束
    graph.add_edge(START, "async_answer")
    graph.add_edge("async_answer", END)

    return graph.compile()


async def main():
    """异步运行工作流，并演示异步调用和流式输出。"""
    app = build_graph()

    # ainvoke 是异步调用方式，需要使用 await
    result = await app.ainvoke({
        "user_question": "LangGraph 支持异步节点吗？",
        "answer": "",
    })

    print(result)

    print("=" * 80)
    print("astream updates:")

    # astream 是异步流式调用方式，使用 async for 逐项读取结果
    async for chunk in app.astream(
        {
            "user_question": "再测试一下异步 stream。",
            "answer": "",
        },
        stream_mode="updates",
    ):
        print(chunk)


# asyncio.run() 创建并运行事件循环，执行异步 main 函数
if __name__ == "__main__":
    asyncio.run(main())