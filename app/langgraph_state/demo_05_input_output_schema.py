from typing import TypedDict

from langgraph.graph import END, START, StateGraph



# Input / Output Schema
# 这个例子里有三个 schema。
# InputState 只有：question
# OverallState 有 question, intent, answer, debug_info
# OutputState 只有：answer
# 所以最终 result 只会暴露 answer。内部 debug_info 不会返回给外部。



# 定义图的输入结构：调用者只需要提供问题
class InputState(TypedDict):
    question: str

# 这里实际实现的是基于关键词的意图识别和回答；和demo06的区别是：demo06是基于预设文档的回答流程，而demo05是基于关键词的意图识别和回答；
# 定义图内部使用的完整状态结构
class OverallState(TypedDict):
    question: str
    intent: str #内部处理状态：由意图识别节点写入，供后续节点使用
    answer: str # 最终回答：由回答节点生成，并通过 OutputState 返回给调用者
    debug_info: str  # 用于记录调试信息，不会出现在最终输出中


# 定义图的输出结构：最终只返回 answer
class OutputState(TypedDict):
    answer: str


def classify_node(state: OverallState) -> dict:
    """根据问题内容识别意图，并写入意图和调试信息。"""
    question = state["question"]

    # 简单判断问题是否涉及退款
    if "退款" in question:
        intent = "refund"
    else:
        intent = "general"

    # 节点返回的字段会更新到图的内部状态中
    return {
        "intent": intent,
        "debug_info": f"识别意图为 {intent}",
    }


def answer_node(state: OverallState) -> dict:
    """读取问题和意图，生成回答。"""
    return {
        "answer": f"当前意图是 {state['intent']}，问题是：{state['question']}"
    }


def build_graph():
    """创建并编译 LangGraph 工作流。"""
    graph = StateGraph(
        OverallState,          # 图内部流转的完整状态
        input_schema=InputState,   # 限定调用者输入的字段
        output_schema=OutputState, # 限定最终返回的字段
    )

    # 注册节点
    graph.add_node("classify", classify_node)
    graph.add_node("answer", answer_node)

    # 连接节点：开始 → 意图识别 → 生成回答 → 结束
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "answer")
    graph.add_edge("answer", END)

    # 编译后得到可调用的工作流
    return graph.compile()


def main():
    """运行工作流并打印结果。"""
    app = build_graph()

    # 输入只需包含 InputState 中定义的 question
    result = app.invoke({
        "question": "我的订单可以退款吗？"
    })

    # 因为 OutputState 只包含 answer，结果中只会返回该字段
    print(result)


# 直接运行此文件时执行 main；作为模块导入时不自动执行
if __name__ == "__main__":
    main()