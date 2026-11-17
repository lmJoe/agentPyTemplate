import uuid

from app.langchain_tools.schemas import (
    QueryLogisticsResult,
    QueryOrderResult,
    TransferHumanResult,
)


# 定义电商业务函数
# 模拟数据库查询结果

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
    "10003": {
        "order_id": "10003",
        "status": "delivered",
        "status_text": "已签收",
        "tracking_company": "圆通",
        "tracking_no": "YT10003",
        "latest_event": "用户本人已签收。",
    },
}


MOCK_LOGISTICS = {
    "SF10001": {
        "tracking_no": "SF10001",
        "tracking_company": "顺丰",
        "latest_event": "包裹已到达成都高新区中转站。",
        "status": "in_transit",
    },
    "YT10003": {
        "tracking_no": "YT10003",
        "tracking_company": "圆通",
        "latest_event": "用户本人已签收。",
        "status": "delivered",
    },
}


# 查询订单
# return QueryOrderResult(**order)效果相当于以下，`order` 里的键名必须和 QueryOrderResult 的字段名匹配，否则可能会因为缺少必填字段或出现未知字段而校验失败。
# result = QueryOrderResult(
#     order_id="10001",
#     status="shipped",
#     status_text="已发货",
#     tracking_company="顺丰",
#     tracking_no="SF10001",
#     latest_event="包裹已发出",
# )
async def query_order(order_id: str) -> QueryOrderResult:
    # 模拟查询订单
    # 真实业务里，--查询真实的业务即可，接口：java -springboot  python -fastapi  nodejs -express  go -gin
    order = MOCK_ORDERS.get(order_id)
    # 如果订单不存在，返回未找到的提示
    if not order:
        return QueryOrderResult(
            order_id=order_id,
            status="not_found",
            status_text="未查询到订单",
            tracking_company=None,
            tracking_no=None,
            latest_event=None,
        )

    return QueryOrderResult(**order)


# 查询物流轨迹
async def query_logistics(tracking_no: str) -> QueryLogisticsResult:

    # 模拟查询物流轨迹
    # 真实业务里，--查询真实的业务即可，接口：java -springboot  python -fastapi  nodejs -express  go -gin
    logistics = MOCK_LOGISTICS.get(tracking_no)

    if not logistics:
        return QueryLogisticsResult(
            tracking_no=tracking_no,
            tracking_company="未知",
            latest_event="未查询到物流信息",
            status="not_found",
        )

    return QueryLogisticsResult(**logistics)


# 创建人工客服工单
async def transfer_human(reason: str) -> TransferHumanResult:
    ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"

    return TransferHumanResult(
        ticket_id=ticket_id,
        status="created",
        message=f"已为您创建人工客服工单，原因：{reason}",
    )