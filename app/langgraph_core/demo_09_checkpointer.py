from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# 这段代码演示如何使用 LangGraph 的检查点，在同一个会话线程中保存和延续消息状态：
# 1. MemoryChatState 用 add_messages 将新消息合并到已有消息列表中。
# 2. InMemorySaver 在内存中保存工作流状态。
# 3. 两次 app.invoke() 使用相同的 thread_id，因此第二次调用会接续同一线程的消息记录。
# 4. chat_node 会读取当前消息列表的最后一条消息，并生成回复。


class MemoryChatState(TypedDict):
    """定义聊天工作流的状态结构。"""

    # add_messages 负责将新消息合并到已有消息列表中
    messages: Annotated[list[AnyMessage], add_messages]


def chat_node(state: MemoryChatState) -> dict:
    """读取最后一条用户消息，并生成一条 AI 回复。"""
    user_message = state["messages"][-1]

    return {
        # 新消息会由 add_messages 合并到工作流状态中
        "messages": [
            AIMessage(
                content=f"我记住这一轮了：{user_message.content}"
            )
        ]
    }


def build_graph():
    """创建并编译带有内存检查点的聊天工作流。"""
    graph = StateGraph(MemoryChatState)

    # 注册聊天处理节点
    graph.add_node("chat", chat_node)

    # 设置执行顺序：开始 → chat → 结束
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # 创建内存检查点，用于保存工作流状态
    checkpointer = InMemorySaver()

    # 编译时传入 checkpointer，使状态可以按会话线程保存和恢复
    return graph.compile(
        checkpointer=checkpointer,
    )


def main():
    """在同一个会话线程中运行两轮对话。"""
    app = build_graph()

    # thread_id 用来标识会话；两次调用使用相同 ID，才能关联状态
    config = {
        "configurable": {
            "thread_id": "thread_demo_001"
        }
    }

    # 第一轮：提交用户消息，工作流会保存执行后的消息状态
    first_result = app.invoke(
        {
            "messages": [
                HumanMessage(content="我叫大伟。")
            ]
        },
        config=config,
    )

    print("first run:")
    for message in first_result["messages"]:
        print(message.type, ":", message.content)

    print("=" * 80)

    # 第二轮沿用同一个 thread_id，工作流会从该线程保存的状态继续
    second_result = app.invoke(
        {
            "messages": [
                HumanMessage(content="你还记得我刚才说什么吗？")
            ]
        },
        config=config,
    )

    print("second run:")
    for message in second_result["messages"]:
        print(message.type, ":", message.content)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()