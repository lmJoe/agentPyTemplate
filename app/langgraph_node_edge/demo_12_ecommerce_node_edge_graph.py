import asyncio
from typing import Literal

from langgraph.graph import END, START, StateGraph

# 导入初始状态构造函数，以及模拟订单查询、售后政策检索服务。
from app.langgraph_node_edge.mock_services import (
    create_initial_state,
    mock_query_order,
    mock_retrieve_policy,
)

# 导入节点之间共享的状态类型。
from app.langgraph_node_edge.schemas import EcommerceNodeEdgeState

# 代码实现了一个较完整的电商客服 LangGraph 工作流：识别问题类型后，分别处理普通咨询、转人工、订单查询和退款咨询；订单查询会检查订单号，退款咨询还会检索政策并评估风险。
# 整体流程
# - 普通问题：识别为 general，直接生成普通答复。
# - 人工请求：识别为 human_service，进入转人工节点。
# - 订单查询、物流或退款问题：先提取订单号。提取失败时询问用户补充订单号。
# - 订单查询：查询订单后生成状态答复；如果有运单号，还会附上物流信息。
# - 退款问题：查询订单状态，检索对应售后政策，评估风险，再生成退款答复或进入人工确认节点。

# 做 LangGraph 调试，不要只看最终回答。
# 哪个节点执行了
# 节点返回了什么
# State 怎么变化
# 条件边怎么路由
# 有没有进入错误节点
# 这些都能通过 stream 观察。

# Node 调试建议
# 1. 输入 State 是否完整
# 2. Node 返回字段是否正确
# 3. 返回字段是否存在于 State schema 中
# 4. list 字段是否配置 reducer
# 5. 异常是否被捕获
# 6. logs 是否记录关键步骤
# 7. 下一个 Edge 是否符合预期

# 调试 Edge 时建议看：
# 1. 条件路由函数返回值是什么
# 2. 返回值是否在 path_map 中
# 3. 是否遗漏 END
# 4. 是否存在循环退出条件
# 5. 是否从同一个节点同时配置静态边和条件边
# 6. Command 和 add_edge 是否混用
# 7. 可视化图是否符合预期


def classify_intent_node(state: EcommerceNodeEdgeState) -> dict:
    """根据用户问题中的关键词识别意图。"""
    question = state["user_question"]

    # 按优先级判断意图，避免“人工退款”等问题被归到退款分支。
    if "人工" in question:
        intent = "human_service"
    elif "退款" in question or "退货" in question:
        intent = "refund"
    elif "物流" in question:
        intent = "logistics"
    elif "订单" in question:
        intent = "query_order"
    else:
        intent = "general"

    return {
        "intent": intent,
        "logs": [f"classify_intent：{intent}"],
    }


def route_by_intent(
    state: EcommerceNodeEdgeState,
) -> Literal["general", "human", "need_order"]:
    """将意图映射为后续处理分支。"""
    if state["intent"] == "general":
        return "general"

    if state["intent"] == "human_service":
        return "human"

    # 查询订单、物流或退款都需要先获取订单信息。
    return "need_order"


def general_answer_node(state: EcommerceNodeEdgeState) -> dict:
    """生成普通问题的答复。"""
    return {
        "final_answer": "这是一个普通问题，可以走普通 ChatModel 生成回答。",
        "is_finished": True,
        "logs": ["general_answer：普通回答完成"],
    }


def transfer_human_node(state: EcommerceNodeEdgeState) -> dict:
    """模拟创建人工客服工单并告知用户。"""
    return {
        "final_answer": "我已经为您转接人工客服，请稍等。",
        "is_finished": True,

        # 记录模拟的转人工工具调用。
        "tool_calls": [
            {
                "name": "transfer_human",
                "args": {
                    "reason": state["user_question"],
                },
                "id": "tool_call_transfer_human_001",
                "success": True,
                "result_preview": "已创建人工客服工单",
            }
        ],
        "logs": ["transfer_human：已创建人工客服工单"],
    }


def extract_order_id_node(state: EcommerceNodeEdgeState) -> dict:
    """从问题中提取演示用的订单号。"""
    question = state["user_question"]

    # 当前只识别两个固定订单号。
    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = None

    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：{order_id}"],
    }


def route_after_extract_order_id(
    state: EcommerceNodeEdgeState,
) -> Literal["ask_order_id", "query_order"]:
    """订单号缺失时询问用户，否则继续查询。"""
    if not state["order_id"]:
        return "ask_order_id"

    return "query_order"


def ask_order_id_node(state: EcommerceNodeEdgeState) -> dict:
    """订单号缺失时，请用户补充信息。"""
    return {
        "final_answer": "请您提供订单号，我才能继续查询订单状态。",
        "is_finished": True,
        "logs": ["ask_order_id：缺少订单号"],
    }


async def query_order_node(state: EcommerceNodeEdgeState) -> dict:
    """异步调用模拟订单服务，并保存订单信息。"""
    order_info = await mock_query_order(
        order_id=state["order_id"]
    )

    return {
        "order_info": order_info,

        # 记录订单查询工具的参数和结果摘要。
        "tool_calls": [
            {
                "name": "query_order",
                "args": {
                    "order_id": state["order_id"],
                },
                "id": "tool_call_query_order_001",
                "success": True,
                "result_preview": order_info["status_text"],
            }
        ],
        "logs": [f"query_order：{order_info['status_text']}"],
    }


def route_after_query_order(
    state: EcommerceNodeEdgeState,
) -> Literal["retrieve_policy", "generate_order_answer", "error_handler"]:
    """根据订单结果和问题意图选择后续处理节点。"""
    order_info = state["order_info"]

    # 没有订单信息时进入错误处理分支。
    if not order_info:
        return "error_handler"

    # 未找到订单时直接生成订单查询答复。
    if order_info["status"] == "not_found":
        return "generate_order_answer"

    # 退款问题需要查询售后政策；其他订单问题直接回复订单信息。
    if state["intent"] == "refund":
        return "retrieve_policy"

    return "generate_order_answer"


async def retrieve_policy_node(state: EcommerceNodeEdgeState) -> dict:
    """根据订单状态异步检索售后政策。"""
    order_info = state["order_info"]

    policy_result = await mock_retrieve_policy(
        order_status=order_info.get("status"),
    )

    return {
        "policy_query": policy_result["policy_query"],
        "policy_answer": policy_result["policy_answer"],
        "sources": policy_result["sources"],
        "logs": ["retrieve_policy：完成规则检索"],
    }


def assess_risk_node(state: EcommerceNodeEdgeState) -> dict:
    """评估退款场景的风险并更新人工确认状态。"""
    order_info = state["order_info"]

    # 已发货订单的退款请求被标记为中风险，
    # 当前规则建议用户收到商品后再申请退货退款。
    if state["intent"] == "refund" and order_info["status"] == "shipped":
        return {
            "risk_level": "medium",
            "need_human_confirm": False,
            "pending_action": None,
            "logs": ["assess_risk：已发货退款，建议用户收货后申请退货退款"],
        }

    # 其他情况按低风险处理。
    return {
        "risk_level": "low",
        "need_human_confirm": False,
        "pending_action": None,
        "logs": ["assess_risk：低风险"],
    }


def route_after_assess_risk(
    state: EcommerceNodeEdgeState,
) -> Literal["human_confirm", "generate_refund_answer"]:
    """根据风险评估结果决定是否进入人工确认节点。"""
    if state["need_human_confirm"]:
        return "human_confirm"

    return "generate_refund_answer"


def human_confirm_node(state: EcommerceNodeEdgeState) -> dict:
    """为需要人工确认的操作生成提示。"""
    return {
        "final_answer": "该操作需要人工确认，我已经为您提交人工处理。",
        "is_finished": True,
        "logs": ["human_confirm：进入人工确认"],
    }


def generate_order_answer_node(state: EcommerceNodeEdgeState) -> dict:
    """根据订单查询结果生成订单答复。"""
    order_info = state["order_info"]

    if order_info["status"] == "not_found":
        answer = "没有查询到该订单，请您检查订单号是否正确。"
    else:
        answer = f"您的订单当前状态是：{order_info['status_text']}。"

        # 有物流单号时，把承运公司、运单号和最新物流节点也加入答复。
        if order_info.get("tracking_no"):
            answer += (
                f"物流公司：{order_info['tracking_company']}，"
                f"物流单号：{order_info['tracking_no']}，"
                f"最新节点：{order_info['latest_event']}"
            )

    return {
        "final_answer": answer,
        "is_finished": True,
        "logs": ["generate_order_answer：订单回答完成"],
    }


def generate_refund_answer_node(state: EcommerceNodeEdgeState) -> dict:
    """组合订单状态和售后政策，生成退款答复。"""
    order_info = state["order_info"]

    answer = (
        f"您的订单当前状态是：{order_info['status_text']}。"
        f"{state['policy_answer']}"
    )

    # 如果存在检索来源，告知用户答复参考了售后规则知识库。
    if state["sources"]:
        answer += " 回答依据来自售后规则知识库。"

    return {
        "final_answer": answer,
        "is_finished": True,
        "logs": ["generate_refund_answer：退款回答完成"],
    }


def error_handler_node(state: EcommerceNodeEdgeState) -> dict:
    """订单信息异常或缺失时生成兜底答复。"""
    return {
        "final_answer": "当前处理失败，请稍后再试，或联系人工客服。",
        "is_finished": True,
        "errors": ["order_info 为空"],
        "logs": ["error_handler：兜底处理"],
    }


def build_graph():
    """创建并编译包含多个条件分支的客服工作流。"""
    graph = StateGraph(EcommerceNodeEdgeState)

    # 注册意图识别、订单查询、政策检索及各种答复节点。
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("general_answer", general_answer_node)
    graph.add_node("transfer_human", transfer_human_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("ask_order_id", ask_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("assess_risk", assess_risk_node)
    graph.add_node("human_confirm", human_confirm_node)
    graph.add_node("generate_order_answer", generate_order_answer_node)
    graph.add_node("generate_refund_answer", generate_refund_answer_node)
    graph.add_node("error_handler", error_handler_node)

    # 所有请求从意图识别开始。
    graph.add_edge(START, "classify_intent")

    # 普通问题直接回答；人工请求转接；其他类型先提取订单号。
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "general": "general_answer",
            "human": "transfer_human",
            "need_order": "extract_order_id",
        },
    )

    # 未提取到订单号时询问用户；否则查询订单。
    graph.add_conditional_edges(
        "extract_order_id",
        route_after_extract_order_id,
        {
            "ask_order_id": "ask_order_id",
            "query_order": "query_order",
        },
    )

    # 订单查询后，按查询结果及意图选择政策检索、订单答复或错误处理。
    graph.add_conditional_edges(
        "query_order",
        route_after_query_order,
        {
            "retrieve_policy": "retrieve_policy",
            "generate_order_answer": "generate_order_answer",
            "error_handler": "error_handler",
        },
    )

    # 退款政策检索完成后评估风险。
    graph.add_edge("retrieve_policy", "assess_risk")

    # 风险评估后决定进入人工确认或生成退款答复。
    graph.add_conditional_edges(
        "assess_risk",
        route_after_assess_risk,
        {
            "human_confirm": "human_confirm",
            "generate_refund_answer": "generate_refund_answer",
        },
    )

    # 所有终止处理节点完成后结束工作流。
    graph.add_edge("general_answer", END)
    graph.add_edge("transfer_human", END)
    graph.add_edge("ask_order_id", END)
    graph.add_edge("generate_order_answer", END)
    graph.add_edge("generate_refund_answer", END)
    graph.add_edge("human_confirm", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


async def main():
    """运行多个示例问题，并打印答复、日志、工具调用和检索来源。"""
    app = build_graph()

    questions = [
        "你好，介绍一下 LangGraph。",
        "帮我查一下订单 10001。",
        "我的订单 10002 还没发货，可以退款吗？",
        "我要退款，但是忘记订单号了。",
        "我要找人工客服。",
    ]

    for question in questions:
        print("question:", question)
        print("=" * 80)

        # 每个问题使用新建的初始状态；recursion_limit 限制图的执行步数。
        result = await app.ainvoke(
            create_initial_state(question),
            config={
                "recursion_limit": 20
            },
        )

        print("final_answer:")
        print(result["final_answer"])

        print("\nlogs:")
        for log in result["logs"]:
            print("-", log)

        print("\ntool_calls:")
        for tool_call in result["tool_calls"]:
            print("-", tool_call)

        print("\nsources:")
        for source in result["sources"]:
            print("-", source)

        print("=" * 120)


# 通过 asyncio 启动异步主函数。
if __name__ == "__main__":
    asyncio.run(main())