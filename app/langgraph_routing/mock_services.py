import asyncio

from app.langgraph_routing.schemas import RoutingState

# 这段代码的作用
# - MOCK_ORDERS：提供三条模拟订单，方便测试不同订单状态下的路由和回复逻辑。
# - mock_query_order()：异步模拟订单查询。缺少订单号、订单不存在和查询成功时，分别返回不同结果。
# - mock_search_policy()：异步模拟售后政策检索，根据查询文字中的关键词返回模拟答案及来源。
# - create_initial_state()：建立 LangGraph 流程使用的初始状态。它为 RoutingState 中定义的字段设置默认值，后续节点可以读取或更新这些字段。


# 模拟订单数据，用于本地测试订单查询流程。
MOCK_ORDERS = {
    "10001": {
        "order_id": "10001",                       # 订单编号
        "status": "shipped",                       # 状态代码
        "status_text": "已发货",                    # 面向用户的状态说明
        "tracking_company": "顺丰",                 # 物流公司
        "tracking_no": "SF10001",                  # 物流单号
        "latest_event": "包裹已到达成都高新区中转站。",  # 最新物流动态
    },
    "10002": {
        "order_id": "10002",
        "status": "paid",
        "status_text": "已付款，待发货",
        "tracking_company": None,  # 尚未发货，因此暂无物流公司
        "tracking_no": None,       # 尚未发货，因此暂无物流单号
        "latest_event": None,      # 暂无物流动态
    },
    "10003": {
        "order_id": "10003",
        "status": "delivered",
        "status_text": "已签收",
        "tracking_company": "圆通",
        "tracking_no": "YT10003",
        "latest_event": "用户本人已签收。",
    },
}


async def mock_query_order(order_id: str | None) -> dict:
    """模拟异步查询订单，返回查询状态、错误信息和订单数据。"""
    # 模拟网络请求或数据库查询所需的耗时。
    await asyncio.sleep(0.05)

    # 没有提供订单号时，返回失败结果。
    if not order_id:
        return {
            "success": False,          # 查询是否成功
            "error": "missing_order_id",  # 错误类型：缺少订单号
            "data": None,              # 没有可返回的订单数据
        }

    # 根据订单号从模拟数据中查找订单。
    order = MOCK_ORDERS.get(order_id)

    # 找不到订单时返回失败结果，并附带未找到订单的信息。
    if not order:
        return {
            "success": False,
            "error": "order_not_found",  # 错误类型：订单不存在
            "data": {
                "order_id": order_id,
                "status": "not_found",
                "status_text": "未查询到订单",
            },
        }

    # 找到订单时返回成功结果和订单数据。
    return {
        "success": True,
        "error": None,
        "data": order,
    }


async def mock_search_policy(query: str | None) -> dict:
    """模拟政策知识库检索，返回命中情况、答案和来源。"""
    # 模拟检索所需的耗时。
    await asyncio.sleep(0.05)

    # 没有查询内容时，无法执行有效检索。
    if not query:
        return {
            "hit": False,  # 是否命中知识库
            "answer": "根据当前知识库无法确认。",
            "sources": [],  # 命中来源列表
        }

    # 查询涉及未发货或待发货订单时，返回对应的售后政策。
    if "未发货" in query or "待发货" in query:
        return {
            "hit": True,
            "answer": "订单未发货时，用户可以申请取消订单并退款。",
            "sources": [
                {
                    "document_id": "ecommerce_after_sales",  # 来源文档编号
                    "chunk_id": "ecommerce_after_sales_chunk_0",  # 文档片段编号
                    "source": "data/knowledge_base/ecommerce_after_sales.md",  # 来源文件
                    "content_preview": "订单未发货时，用户可以申请取消订单并退款。",  # 来源内容摘要
                    "score": 0.92,  # 模拟检索相关度分数
                }
            ],
        }

    # 查询涉及已发货或已签收订单时，返回对应的售后政策。
    if "已发货" in query or "已签收" in query:
        return {
            "hit": True,
            "answer": "订单已发货后，需要用户收到商品后再发起退货退款申请。",
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

    # 查询内容不匹配当前模拟规则时，视为没有检索到答案。
    return {
        "hit": False,
        "answer": "根据当前知识库无法确认。",
        "sources": [],
    }


def create_initial_state(
    user_question: str,
) -> RoutingState:
    """创建路由流程的初始状态，并为所有状态字段设置默认值。"""
    return {
        "user_question": user_question,  # 保存用户原始问题

        "intent": "unknown",  # 意图识别前，先标记为未知

        "order_id": None,   # 尚未识别出订单号
        "order_info": None, # 尚未查询订单信息

        "need_policy": False,  # 初始时不需要查询政策
        "policy_query": None,  # 尚未生成政策查询内容
        "policy_answer": None, # 尚无政策答案
        "sources": [],         # 尚无知识库来源

        "tool_success": True, # 当前尚未执行工具，默认没有失败
        "tool_calls": [],     # 记录工具调用的列表

        "rag_hit": False,           # 尚未命中知识库
        "need_human_confirm": False, # 暂无人工确认需求
        "risk_level": "low",         # 初始风险级别
        "pending_action": None,      # 暂无等待执行的动作

        "retry_count": 0, # 当前重试次数
        "max_retry": 2,   # 最多允许重试的次数

        "final_answer": "",  # 流程完成后写入面向用户的回复
        "is_finished": False, # 标记流程尚未结束

        "logs": [],   # 记录流程运行日志
        "errors": [], # 记录流程中发生的错误
    }