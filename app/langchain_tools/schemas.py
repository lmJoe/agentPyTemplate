from typing import Literal

from pydantic import BaseModel, Field





# 查询订单参数
class QueryOrderArgs(BaseModel):
    order_id: str = Field(
        ...,
        min_length=1,
        description="订单号，例如 10001",
    )


# 查询物流参数

# QueryOrderResult 继承自 Pydantic 的 BaseModel。创建这个模型时，Pydantic 会检查传入的数据是否符合字段类型和限制
class QueryOrderResult(BaseModel):
    order_id: str = Field(..., description="订单号")

    # 订单状态,Literal 限定它只能是以下值之一
    status: Literal[
        "pending",
        "paid",
        "shipped",
        "delivered",
        "cancelled",
        "refunding",
        "refunded",
        "not_found",
    ] = Field(..., description="订单状态")

    status_text: str = Field(..., description="订单状态中文说明")

    tracking_company: str | None = Field(
        default=None,
        description="物流公司",
    )

    tracking_no: str | None = Field(
        default=None,
        description="物流单号",
    )

    latest_event: str | None = Field(
        default=None,
        description="最新物流节点",
    )


# 查询物流参数
class QueryLogisticsArgs(BaseModel):
    tracking_no: str = Field(
        ...,
        min_length=1,
        description="物流单号，例如 SF10001",
    )


# 查询物流结果
class QueryLogisticsResult(BaseModel):
    tracking_no: str = Field(..., description="物流单号")

    tracking_company: str = Field(..., description="物流公司")

    latest_event: str = Field(..., description="最新物流节点")

    status: Literal[
        "in_transit",
        "delivered",
        "exception",
        "not_found",
    ] = Field(..., description="物流状态")


# 转人工参数
class TransferHumanArgs(BaseModel):
    reason: str = Field(
        ...,
        min_length=1,
        description="转人工原因",
    )


# 转人工结果
class TransferHumanResult(BaseModel):
    ticket_id: str = Field(..., description="人工客服工单 ID")

    status: Literal["created"] = Field(
        default="created",
        description="工单状态",
    )

    message: str = Field(..., description="提示信息")