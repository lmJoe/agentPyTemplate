from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# 这段代码演示了一个只有一步的聊天工作流：
# 1. 初始状态中的 messages 包含一条用户消息。
# 2. assistant_node 读取最后一条消息，并生成一条 AIMessage 作为回复。
# 3. messages 字段通过 add_messages 合并新消息，因此执行结果中同时保留用户消息和 AI 回复。
# 4. 最后循环打印两条消息的类型和内容。
# add_messages 是这里的 reducer。它会把节点返回的新消息合并到状态中的消息列表；如果消息带有相同 ID，还可以按消息 ID 更新已有消息。



class ChatState(TypedDict):
    """定义聊天工作流的状态结构。"""

    # add_messages 是 messages 字段的 reducer：
    # 节点返回新消息时，会按消息规则合并到现有消息列表中
    messages: Annotated[list[AnyMessage], add_messages]


def assistant_node(state: ChatState) -> dict:
    """读取最后一条消息，生成并返回一条 AI 回复。"""
    last_message = state["messages"][-1]

    return {
        # 返回的 AIMessage 会由 add_messages 合并进 messages 列表
        "messages": [
            AIMessage(
                content=f"我收到你的问题了：{last_message.content}"
            )
        ]
    }


def build_graph():
    """创建并编译聊天工作流。"""
    graph = StateGraph(ChatState)

    # 注册 AI 回复节点
    graph.add_node("assistant", assistant_node)

    # 设置执行顺序：开始 → assistant → 结束
    graph.add_edge(START, "assistant")
    graph.add_edge("assistant", END)

    return graph.compile()


def main():
    """运行聊天工作流，并打印对话中的所有消息。"""
    app = build_graph()

    # 将用户消息作为初始对话状态传入工作流
    result = app.invoke({
        "messages": [
            HumanMessage(content="LangGraph 的 add_messages 是什么？")
        ]
    })

    # 打印合并后的消息列表，包括用户消息和 AI 回复
    for message in result["messages"]:
        print(message.type, ":", message.content)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()