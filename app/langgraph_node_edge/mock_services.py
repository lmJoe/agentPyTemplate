import asyncio

# 主要作用
# - MOCK_ORDERS：保存两条示例订单数据，供模拟查询使用。
# - mock_query_order()：根据订单号返回订单信息；缺少订单号或查无此单时返回对应状态。它是 async 函数，因此调用时需要使用 await。
# - mock_retrieve_policy()：根据订单状态返回政策说明和模拟检索来源。
# - create_initial_state()：初始化客服工作流所需的各项数据，供后续 LangGraph 节点读写。
# 两个异步函数中的 asyncio.sleep(0.05) 只是模拟外部服务的等待时间，不会真的查询订单系统或知识库。调用示


# order_info = await mock_query_order("10002")
# policy = await mock_retrieve_policy(order_info["status"])


# 模拟订单数据库，使用订单号作为键。
MOCK_ORDERS = {
    "10001": {
        "order_id": "10001",
        "status": "shipped",
        "status_text": "已发货",
        "tracking_company": "顺丰",
        "tracking_no": "SF10001",
        "latest_event": "包裹已到达成都高新区中转站。",
    },
    "10002": {
        "order_id": "10002",
        "status": "paid",
        "status_text": "已付款，待发货",
        "tracking_company": None,
        "tracking_no": None,
        "latest_event": None,
    },
}


async def mock_query_order(order_id: str | None) -> dict:
    """异步模拟订单查询，返回订单信息或相应的兜底结果。"""

    # 模拟网络请求耗时；真实服务中这里通常会调用订单 API。
    await asyncio.sleep(0.05)

    # 没有提供订单号时，返回“缺少订单号”结果。
    if not order_id:
        return {
            "order_id": "",
            "status": "missing_order_id",
            "status_text": "缺少订单号",
            "tracking_company": None,
            "tracking_no": None,
            "latest_event": None,
        }

    # 返回模拟数据库中的订单；若订单号不存在，则返回“未查询到订单”。
    return MOCK_ORDERS.get(
        order_id,
        {
            "order_id": order_id,
            "status": "not_found",
            "status_text": "未查询到订单",
            "tracking_company": None,
            "tracking_no": None,
            "latest_event": None,
        },
    )


async def mock_retrieve_policy(
    order_status: str | None,
) -> dict:
    """根据订单状态异步模拟检索退款政策及其来源。"""

    # 模拟检索服务的响应时间。
    await asyncio.sleep(0.05)

    if order_status == "paid":
        # 已付款但未发货：返回取消订单并退款的规则。
        return {
            "policy_query": "订单未发货退款规则",
            "policy_answer": "订单未发货时，用户可以申请取消订单并退款。",
            "sources": [
                {
                    "document_id": "ecommerce_after_sales",
                    "chunk_id": "ecommerce_after_sales_chunk_0",
                    "source": "data/knowledge_base/ecommerce_after_sales.md",
                    "content_preview": "订单未发货时，用户可以申请取消订单并退款。",
                    "score": 0.92,
                }
            ],
        }

    if order_status == "shipped":
        # 已发货：返回收到商品后再申请退货退款的规则。
        return {
            "policy_query": "订单已发货退货退款规则",
            "policy_answer": "订单已发货后，需要用户收到商品后再发起退货退款申请。",
            "sources": [
                {
                    "document_id": "ecommerce_after_sales",
                    "chunk_id": "ecommerce_after_sales_chunk_1",
                    "source": "data/knowledge_base/ecommerce_after_sales.md",
                    "content_preview": "订单已发货后，需要用户收到商品后再发起退货退款申请。",
                    "score": 0.89,
                }
            ],
        }

    # 订单状态无法匹配已知规则时，返回兜底说明，不附带来源。
    return {
        "policy_query": "退款规则",
        "policy_answer": "当前订单状态无法确认退款规则，建议转人工客服。",
        "sources": [],
    }


def create_initial_state(
    user_question: str,
) -> dict:
    """创建客服工作流的初始状态。"""
    return {
        "user_question": user_question,

        # 后续节点会识别用户意图。
        "intent": "unknown",

        # 订单查询结果尚未生成。
        "order_id": None,
        "order_info": None,

        # 政策查询结果尚未生成。
        "policy_query": None,
        "policy_answer": None,
        "sources": [],

        # 初始时不需要人工确认，风险设为低。
        "need_human_confirm": False,
        "risk_level": "low",
        "pending_action": None,

        # 初始化工具调用、日志和错误记录。
        "tool_calls": [],
        "logs": [],
        "errors": [],

        # 最终答复暂为空；流程尚未完成，也没有重试。
        "final_answer": "",
        "retry_count": 0,
        "is_finished": False,
    }