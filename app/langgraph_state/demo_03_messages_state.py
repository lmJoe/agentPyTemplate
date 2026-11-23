from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph


# 这段代码用 LangGraph 创建了一个简单的消息处理流程：
# 1. MessagesState 提供了预定义的 messages 状态字段，适合保存对话消息。
# 2. 工作流接收一条 HumanMessage。
# 3. assistant_node 读取最后一条消息，并生成一条 AIMessage 回复。
# 4. 工作流返回消息列表，循环将消息类型和内容打印出来。

def assistant_node(state: MessagesState) -> dict:
    """读取最后一条消息，并生成一条 AI 回复。"""
    last_message = state["messages"][-1]

    return {
        # MessagesState 会按消息合并规则将这条回复加入 messages 列表
        "messages": [
            AIMessage(
                content=f"我收到你的消息了：{last_message.content}"
            )
        ]
    }


def build_graph():
    """创建并编译聊天工作流。"""
    # MessagesState 是 LangGraph 提供的预定义状态类型，
    # 其中包含 messages 字段以及相应的消息合并逻辑
    graph = StateGraph(MessagesState)

    # 注册 assistant 节点
    graph.add_node("assistant", assistant_node)

    # 设置执行顺序：开始 → assistant → 结束
    graph.add_edge(START, "assistant")
    graph.add_edge("assistant", END)

    return graph.compile()


def main():
    """运行工作流，并打印用户消息和 AI 回复。"""
    app = build_graph()

    # 将用户消息作为初始消息传入工作流
    result = app.invoke({
        "messages": [
            HumanMessage(content="MessagesState 有什么用？")
        ]
    })

    # 输出执行后的完整消息列表
    for message in result["messages"]:
        print(message.type, ":", message.content)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()