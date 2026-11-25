from typing import TypedDict

# LangGraph 工作流的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 顺序 Edge
# 执行流程
# 流程通过边连接成：

# START → classify_intent → extract_order_id → answer → END

# 对于示例问题：
# 1. classify_intent_node 发现问题包含“订单”，将 intent 设为 "query_order"。
# 2. extract_order_id_node 找到 "10001"，将其写入 order_id。
# 3. answer_node 使用这两个字段生成答复。
# 最终答复为：
# 意图：query_order，订单号：10001
# 这里的意图判断和订单号提取都是简单的关键词与固定字符串匹配，适合演示节点按顺序共享状态的过程。

class SequenceState(TypedDict):
    """工作流各节点共享的状态结构。"""

    user_question: str       # 用户输入的问题
    intent: str              # 识别出的意图
    order_id: str | None     # 提取到的订单号；未找到时为 None
    final_answer: str        # 最终生成的答复


def classify_intent_node(state: SequenceState) -> dict:
    """根据用户问题中的关键词判断意图。"""
    question = state["user_question"]

    # 包含“订单”时识别为订单查询，否则按普通问题处理。
    if "订单" in question:
        intent = "query_order"
    else:
        intent = "general"

    # 返回需要写入共享状态的字段。
    return {
        "intent": intent
    }


def extract_order_id_node(state: SequenceState) -> dict:
    """检查问题中是否包含示例订单号 10001。"""
    question = state["user_question"]

    # 这是演示用的固定匹配；当前不会提取其他订单号。
    if "10001" in question:
        return {"order_id": "10001"}

    # 没找到时将订单号设为 None。
    return {"order_id": None}


def answer_node(state: SequenceState) -> dict:
    """读取前面节点的结果并拼接成答复。"""
    return {
        "final_answer": (
            f"意图：{state['intent']}，"
            f"订单号：{state['order_id']}"
        )
    }


def build_graph():
    """创建并编译由三个节点组成的顺序工作流。"""
    graph = StateGraph(SequenceState)

    # 注册意图识别、订单号提取和答复生成节点。
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("answer", answer_node)

    # 设置执行顺序：入口 -> 意图识别 -> 提取订单号 -> 生成答复 -> 出口。
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "extract_order_id")
    graph.add_edge("extract_order_id", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行示例并打印工作流的最终状态。"""
    app = build_graph()

    # 提供初始状态；节点会依次更新 intent、order_id 和 final_answer。
    result = app.invoke({
        "user_question": "帮我查一下订单 10001。",
        "intent": "unknown",
        "order_id": None,
        "final_answer": "",
    })

    print(result)


# 直接运行该文件时执行 main()；被其他模块导入时不会自动执行。
if __name__ == "__main__":
    main()