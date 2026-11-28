from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# 多轮 Chat Memory
# 子演示多轮 Chat Memory。
# 关键有两个：messages 使用 add_messages，两次 invoke 使用同一个 thread_id
# 这样第二轮执行时，State 里还会有第一轮的 messages。
# LangChain 的短期记忆文档也说明，短期记忆是 agent state 的一部分，通过 checkpointer 持久化后，同一个 thread 可以在交互之间恢复上下文。


class ChatMemoryState(TypedDict):
    # 对话消息列表；add_messages 会按 LangGraph 的消息规则合并新旧消息
    messages: Annotated[list[AnyMessage], add_messages]


def chat_node(state: ChatMemoryState) -> dict:
    """读取当前对话消息，并生成一条简单的回复。"""
    # 当前状态中的最后一条消息，通常是用户刚提交的问题
    last_message = state["messages"][-1]

    # 统计当前 thread 中已有的消息数量
    history_count = len(state["messages"])

    # 返回的新 AI 消息会通过 add_messages 合并到消息历史中
    return {
        "messages": [
            AIMessage(
                content=(
                    f"我收到了：{last_message.content}。"
                    f"当前 thread 里一共有 {history_count} 条历史消息。"
                )
            )
        ]
    }


def build_graph():
    """创建只包含聊天节点、并启用内存检查点的图。"""
    graph = StateGraph(ChatMemoryState)

    # 注册聊天处理节点
    graph.add_node("chat", chat_node)

    # 设置流程：开始 → 聊天节点 → 结束
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # 使用内存保存每个 thread 的状态检查点
    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


def main():
    # 创建图应用
    app = build_graph()

    # 两次调用使用相同的 thread_id，因此会访问同一会话的检查点
    config = {
        "configurable": {
            "thread_id": "thread_chat_memory_demo"
        }
    }

    # 第一次调用：提交一条用户消息
    first = app.invoke(
        {
            "messages": [
                HumanMessage(content="我叫大伟。")
            ]
        },
        config=config,
    )

    # 打印第一次调用后的消息历史
    print("first:")
    for message in first["messages"]:
        print(message.type, ":", message.content)

    print("=" * 80)

    # 第二次调用：使用相同 thread_id，继续同一会话
    second = app.invoke(
        {
            "messages": [
                HumanMessage(content="你还记得我刚才说了什么吗？")
            ]
        },
        config=config,
    )

    # 打印第二次调用后的消息历史
    print("second:")
    for message in second["messages"]:
        print(message.type, ":", message.content)


# 直接运行此文件时执行 main；
# 被其他模块导入时不自动运行
if __name__ == "__main__":
    main()