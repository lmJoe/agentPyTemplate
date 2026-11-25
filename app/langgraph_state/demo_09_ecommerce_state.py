# 用于表示对话中的用户消息和 AI 回复。
from langchain_core.messages import AIMessage, HumanMessage

# LangGraph 的图结构入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph

# 项目中定义的电商客服共享状态类型。
from app.langgraph_state.schemas import EcommerceAgentState


def create_initial_ecommerce_state(
    user_question: str,
) -> EcommerceAgentState:
    """根据用户问题创建一份完整的初始状态。"""
    return {
        "user_question": user_question,

        # 把用户原始问题放入对话历史。
        "messages": [HumanMessage(content=user_question)],

        # 初始时还没有识别出意图或订单信息。
        "intent": "unknown",
        "order_id": None,
        "tracking_no": None,

        # 业务查询结果暂时为空。
        "order_info": None,
        "logistics_info": None,

        # 尚未检索售后政策。
        "policy_query": None,
        "policy_answer": None,
        "sources": [],

        # 初始风险等级较低，不需要人工确认。
        "risk_level": "low",
        "need_human_confirm": False,
        "pending_action": None,

        # 初始化工具调用、日志和错误列表。
        "tool_calls": [],
        "logs": [],
        "errors": [],

        # 尚未生成最终答复，流程也未结束。
        "final_answer": "",
        "is_finished": False,
    }


def classify_intent_node(state: EcommerceAgentState) -> dict:
    """用简单的关键词规则识别用户意图。"""
    question = state["user_question"]

    # 按关键词判断意图。这里是演示逻辑，不是模型分类。
    if "退款" in question or "退货" in question:
        intent = "refund"
    elif "物流" in question:
        intent = "logistics"
    elif "订单" in question:
        intent = "query_order"
    elif "人工" in question:
        intent = "human_service"
    else:
        intent = "general"

    # 返回本节点需要更新的状态字段。
    return {
        "intent": intent,
        "logs": [f"classify_intent：识别意图为 {intent}"],
    }


def extract_order_id_node(state: EcommerceAgentState) -> dict:
    """从问题中查找演示用的订单号。"""
    question = state["user_question"]

    # 这里只识别两个固定订单号；实际项目通常会用正则或实体抽取。
    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = None

    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：订单号为 {order_id}"],
    }


def query_order_node(state: EcommerceAgentState) -> dict:
    """根据订单号查询模拟订单数据。"""
    order_id = state["order_id"]

    # 用固定数据模拟订单查询接口。
    if order_id == "10001":
        order_info = {
            "order_id": "10001",
            "status": "shipped",
            "status_text": "已发货",
            "tracking_company": "顺丰",
            "tracking_no": "SF10001",
            "latest_event": "包裹已到达成都高新区中转站。",
        }
    elif order_id == "10002":
        order_info = {
            "order_id": "10002",
            "status": "paid",
            "status_text": "已付款，待发货",
            "tracking_company": None,
            "tracking_no": None,
            "latest_event": None,
        }
    else:
        # 未识别到订单号，或订单号不在模拟数据中。
        order_info = {
            "order_id": order_id or "",
            "status": "not_found",
            "status_text": "未查询到订单",
            "tracking_company": None,
            "tracking_no": None,
            "latest_event": None,
        }

    return {
        "order_info": order_info,

        # 记录一次模拟的工具调用及其参数、结果摘要。
        "tool_calls": [
            {
                "name": "query_order",
                "args": {"order_id": order_id},
                "id": "mock_query_order",
                "success": True,
                "result_preview": order_info["status_text"],
            }
        ],
        "logs": [f"query_order：订单状态为 {order_info['status_text']}"],
    }


def retrieve_policy_node(state: EcommerceAgentState) -> dict:
    """根据订单状态选择对应的售后政策说明。"""
    order_info = state.get("order_info")

    if order_info and order_info.get("status") == "paid":
        # 订单已付款但未发货。
        policy_answer = "订单未发货时，用户可以申请取消订单并退款。"
        policy_query = "订单未发货退款规则"
    elif order_info and order_info.get("status") == "shipped":
        # 订单已发货。
        policy_answer = "订单已发货后，需要用户收到商品后再发起退货退款申请。"
        policy_query = "订单已发货退货退款规则"
    else:
        # 订单信息不足时给出兜底建议。
        policy_answer = "当前状态无法确认退款规则，建议转人工客服。"
        policy_query = "退款规则"

    return {
        "policy_query": policy_query,
        "policy_answer": policy_answer,

        # 这里模拟检索来源。实际项目中通常由向量数据库或搜索服务提供。
        "sources": [
            {
                "document_id": "ecommerce_after_sales",
                "chunk_id": "ecommerce_after_sales_chunk_0",
                "source": "data/knowledge_base/ecommerce_after_sales.md",
                "content_preview": policy_answer,
                "score": 0.9,
            }
        ],
        "logs": ["retrieve_policy：完成售后规则查询"],
    }


def generate_answer_node(state: EcommerceAgentState) -> dict:
    """根据意图和前序节点结果生成最终答复。"""
    order_info = state.get("order_info")
    policy_answer = state.get("policy_answer")

    if state["intent"] == "refund":
        # 退款问题：组合订单状态和售后政策。
        answer = (
            f"您的订单当前状态是：{order_info['status_text']}。"
            f"{policy_answer}"
        )
    elif state["intent"] == "query_order":
        # 普通订单查询：只回复订单状态。
        answer = f"您的订单当前状态是：{order_info['status_text']}。"
    else:
        # 其他意图暂时使用通用兜底答复。
        answer = "这是普通问题，可以走普通 Chat。"

    return {
        "final_answer": answer,
        "is_finished": True,

        # 将 AI 回复也加入对话历史。
        "messages": [AIMessage(content=answer)],
        "logs": ["generate_answer：最终回答生成完成"],
    }


def build_graph():
    """创建并编译 LangGraph 工作流。"""
    graph = StateGraph(EcommerceAgentState)

    # 注册各个处理节点。
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("generate_answer", generate_answer_node)

    # 设置固定执行顺序：开始 -> 分类 -> 提取订单号 -> 查订单
    # -> 查政策 -> 生成答复 -> 结束。
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "extract_order_id")
    graph.add_edge("extract_order_id", "query_order")
    graph.add_edge("query_order", "retrieve_policy")
    graph.add_edge("retrieve_policy", "generate_answer")
    graph.add_edge("generate_answer", END)

    # compile() 将图构建成可调用的应用。
    return graph.compile()


def main():
    """运行示例流程并打印结果。"""
    app = build_graph()

    # 传入一个示例问题，启动整个图。
    result = app.invoke(
        create_initial_ecommerce_state(
            "我的订单 10002 还没发货，可以退款吗？"
        )
    )

    print("final_answer:")
    print(result["final_answer"])

    print("=" * 80)
    print("sources:")
    for source in result["sources"]:
        print(source)

    print("=" * 80)
    print("tool_calls:")
    for tool_call in result["tool_calls"]:
        print(tool_call)

    print("=" * 80)
    print("logs:")
    for log in result["logs"]:
        print("-", log)

    print("=" * 80)
    print("messages:")
    for message in result["messages"]:
        print(message.type, ":", message.content)


# 只有直接运行此 Python 文件时才执行 main()；
# 被其他模块 import 时不会自动启动示例。
if __name__ == "__main__":
    main()