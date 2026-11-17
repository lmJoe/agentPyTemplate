import json

from langchain_core.tools import StructuredTool, tool

from app.langchain_tools.ecommerce_functions import (
    query_logistics,
    query_order,
    transfer_human,
)
from app.langchain_tools.schemas import (
    QueryLogisticsArgs,
    QueryOrderArgs,
    TransferHumanArgs,
)
# 两种注册方式：

# @tool 装饰器 定义工具函数，用于在 Agent 中调用外部函数
# 会把函数包装成 LangChain 的工具对象。LangChain 通常会从函数名、参数类型和文档字符串中推断工具名称、参数结构和用途。
# 这个函数内部调用底层逻辑，再把 Pydantic 结果转换成 JSON 字符串返回。

# 查询订单状态
@tool
async def query_order_simple(order_id: str) -> str:
    """根据订单号查询订单状态和物流信息。当用户询问订单状态、发货状态、物流状态时使用。"""
    # 调用底层订单查询逻辑，获取订单状态与物流信息
    result = await query_order(order_id=order_id)

    # json.dumps() 是 Python json 模块里的函数，用来把 Python 数据转换成 JSON 格式的字符串，ensure_ascii=False 保证中文正常显示

    # result.model_dump()，先把 Pydantic 模型 result 转换成 Python 字典，例如：
    # {
    #     "order_id": "10001",
    #     "status": "shipped",
    #     "status_text": "已发货",
    #     "tracking_company": "顺丰",
    #     "tracking_no": "SF10001",
    #     "latest_event": "包裹已发出"
    # }
    # 然后json.dumps(..., ensure_ascii=False)把这个字典转换成字符串：
    # {"order_id": "10001", "status": "shipped", "status_text": "已发货", "tracking_company": "顺丰", "tracking_no": "SF10001", "latest_event": "包裹已发出"}
    # ensure_ascii=False 表示中文直接以汉字显示；如果不设置，中文可能会被编码成类似 \u5df2\u53d1\u8d27 的形式。


    return json.dumps(
        result.model_dump(),
        ensure_ascii=False,
    )

# 查询物流轨迹
@tool
async def query_logistics_simple(tracking_no: str) -> str:
    """根据物流单号查询物流轨迹。当用户已经提供物流单号，并询问包裹运输状态时使用。"""
    result = await query_logistics(tracking_no=tracking_no)

    return json.dumps(
        result.model_dump(),
        ensure_ascii=False,
    )

# 创建人工客服工单
@tool
async def transfer_human_simple(reason: str) -> str:
    """当用户明确要求人工客服，或者问题超出 AI 能力范围时创建人工客服工单。

    Args:
        reason (str): 转接人工客服的原因说明，用于记录用户诉求或超出 AI 能力范围的具体情况。

    Returns:
        str: 人工客服工单信息的 JSON 字符串，包含工单详情等字段。
    """
    result = await transfer_human(reason=reason)

    return json.dumps(
        result.model_dump(),
        ensure_ascii=False,
    )



# StructuredTool.from_function()：显式指定工具配置
# 这种写法把已有的 query_order 函数包装成工具，并明确指定：
# - coroutine：要调用的异步函数。
# - name：工具对 Agent 显示的名称。
# - description：告诉 Agent 这个工具何时使用。
# - args_schema：用哪个 Pydantic 模型校验输入参数。
query_order_tool = StructuredTool.from_function(
    coroutine=query_order,
    name="query_order",
    description=(
        "根据订单号查询订单状态和物流信息。"
        "当用户询问订单状态、发货状态、物流状态时使用。"
        "如果用户没有提供订单号，不要调用该工具，应先追问订单号。"
    ),
    args_schema=QueryOrderArgs,
)


query_logistics_tool = StructuredTool.from_function(
    coroutine=query_logistics,
    name="query_logistics",
    description=(
        "根据物流单号查询物流轨迹。"
        "当用户已经提供物流单号，并询问包裹运输状态时使用。"
    ),
    args_schema=QueryLogisticsArgs,
)


transfer_human_tool = StructuredTool.from_function(
    coroutine=transfer_human,
    name="transfer_human",
    description=(
        "当用户明确要求人工客服，或者问题超出 AI 能力范围时创建人工客服工单。"
        "该工具只创建工单，不处理退款、赔付、删除、支付等高风险操作。"
    ),
    args_schema=TransferHumanArgs,
)


ECOMMERCE_LANGCHAIN_TOOLS = [
    query_order_tool,
    query_logistics_tool,
    transfer_human_tool,
]



# 两种注册方式的区别：
# - @tool 装饰器：自动推断工具名称、参数结构和用途，适合快速原型开发。
# - StructuredTool.from_function()：显式指定工具配置，适合需要精确控制工具行为的场景。
# 项目	        @tool 版本	                    StructuredTool.from_function() 版本
# 包装的函数	query_order_simple 等包装函数	    底层的 query_order 等函数
# 参数定义	    从函数签名推断	                    显式使用 args_schema
# 名称和用途	通常从函数名和 docstring 推断	    显式指定名称和描述
# 返回值处理	手动转成 JSON 字符串	            直接返回底层函数的结果


# 所以它们不只是两种不同的注册语法：当前代码里，每种方式包装的函数也不同，返回值形式可能不同。

# ECOMMERCE_TOOLS 最后只包含三个 StructuredTool 对象，并没有包含上面的 @tool 函数。若 Agent 绑定的是 ECOMMERCE_TOOLS，实际使用的就是 StructuredTool.from_function() 创建的那组工具。



# 选哪种方式把函数注册为 LangChain 工具？
# 推荐 StructuredTool + args_schema，因为可以明确控制工具名称、描述和输入参数校验。name,description,args_schema,coroutine
# StructuredTool 参考文档也提供了结构化工具类，并包含工具调用 schema、运行、异步运行、stream events 等能力。
