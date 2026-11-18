from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage

from app.langchain_agents.schemas import AgentMessageItem, AgentRunResponse
from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_tools.registry import langchain_tool_registry

# 实现 Agent 消息转换工具，把 LangChain 的消息对象 BaseMessage 转成项目自己的 AgentMessageItem


# 通过 LangchainModelFactory 构建 Agent 模型
def build_agent_model(
    provider: str = "deepseek",
    model_name: str = "deepseek-chat",
    temperature: float = 0,
):
    return LangChainModelFactory.create(
        provider=provider,
        model=model_name,
        temperature=temperature,
    )


# 构建电商客服 Agent
def build_ecommerce_agent(
    provider: str = "deepseek",
    model_name: str = "deepseek-chat",
):
    model = build_agent_model(
        provider=provider,
        model_name=model_name,
        temperature=0,
    )

    tools = langchain_tool_registry.get_many([
        "query_order",
        "query_logistics",
        "transfer_human",
    ])

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "你是一个跨境电商平台的智能客服 Agent。\n"
            "\n"
            "你可以使用工具查询订单、物流和创建转人工工单。\n"
            "\n"
            "核心规则：\n"
            "1. 用户询问订单状态、发货状态、物流状态时，优先调用工具查询真实信息。\n"
            "2. 不要编造订单状态、物流公司或物流单号。\n"
            "3. 如果用户没有提供订单号，要先追问订单号，不要调用 query_order。\n"
            "4. 如果工具返回未查询到订单，要礼貌说明，并建议用户检查订单号。\n"
            "5. 如果问题超出客服范围，建议转人工。\n"
            "6. 回复要简洁、礼貌、可执行。"
        ),
    )


# getattr是python的一个内置函数，用于动态获取对象的属性
# 等同于
# if hasattr(message,"tool_call"):
#     tool_calls = [message.tool_call]
# else:
#     tool_calls = None
# 这段函数把 LangChain 的消息对象 BaseMessage 转成项目自己的 AgentMessageItem，方便统一保存、返回给前端或通过 API 序列化。

# 定义函数 message_to_item。它接收一条 LangChain 消息，返回一个 AgentMessageItem。参数和返回值上的类型标注，便于开发者理解，也方便类型检查工具发现错误
def message_to_item(message: BaseMessage) -> AgentMessageItem:
    """
    总体上，这个函数的核心目的，是把 LangChain 消息里需要的信息提取出来，并统一成项目内部的数据结构。这样 API、前端或日志处理代码不必直接依赖 LangChain 的消息对象。
    
    """
    # 尝试读取消息的 tool_calls 属性，也就是模型要求调用的工具信息
    # getattr(..., None)：如果消息没有这个属性，就返回 None，避免直接访问时报错。
    # or []：属性不存在、为 None 或为空时，统一用空列表表示。
    tool_calls = getattr(message, "tool_calls", None) or []

    # 尝试读取工具调用 ID。工具返回结果通常会带这个 ID，用来对应之前发起的工具调用。普通消息可能没有该属性，所以缺省为 None。
    tool_call_id = getattr(message, "tool_call_id", None)

    # 试读取消息名称。某些消息（例如工具消息）会用名称标识来源；没有名称时设为 None。
    name = getattr(message, "name", None)

    # 取出消息正文。单独赋给变量后，下面可以根据正文的数据类型做统一处理
    content = message.content

    # 检查正文是否为列表。LangChain 的消息正文有时不只是普通字符串，也可能由多个内容块组成，例如文本块或多模态内容块。
    if isinstance(content, list):
        # 正文是列表时，将它转成字符串，以便放进预期为文本的 content 字段。这里得到的通常是 Python 列表的字符串表示，适合简单展示或调试，但不一定是理想的结构化存储格式。
        content_text = str(content)
    else:
        # 如果正文不是列表，就按普通值处理，将正文转成字符串；如果正文是 None 或其他假值，则用空字符串代替。这样返回的 content 始终是字符串，避免出现 None。
        content_text = str(content or "")

    # 开始构造项目自己的消息数据对象。后续代码把 LangChain 消息中关心的信息逐项复制过去。
    return AgentMessageItem(
        type=message.type,
        content=content_text,
        name=name,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
    )


# 定义函数 parse_agent_result。
# - result 预期是一个字典，里面包含 Agent 执行后的数据。
# - dict[str, Any] 表示字典的键是字符串，值可以是任意类型。
# - -> AgentRunResponse 表示函数会返回一个 AgentRunResponse 对象

def parse_agent_result(result: dict[str, Any]) -> AgentRunResponse:

    """
    这段函数把 Agent 的运行结果整理成项目自己的 AgentRunResponse，包含最终答案、完整消息列表、工具调用情况和统计信息。
    """

    # 从结果字典中读取 "messages" 字段。如果没有这个字段，就使用空列表。
    # 这么写可以避免字段缺失时报错。不过它假设取到的值是消息列表；如果 "messages" 存在但值是 None 或其他类型，后续代码仍可能出错。
    messages = result.get("messages", [])

    # 遍历每条 LangChain 消息，并调用前面定义的 message_to_item，把消息转为项目自己的 AgentMessageItem。
    # 转换后得到的 items 会作为响应中的完整消息列表，方便 API 或前端统一处理。
    items = [
        message_to_item(message)
        for message in messages
    ]

    # 先把最终答案设为空字符串。这样即使没有消息，返回对象也有一个可用的默认答案。
    answer = ""


    # 如果消息列表非空，就取最后一条消息的正文作为答案。
    # - messages[-1] 表示列表中的最后一条消息。
    # - or "" 在正文为空或为 None 时提供空字符串。
    # - str(...) 确保答案是字符串。
    if messages:
        answer = str(messages[-1].content or "")

    # 下面的循环事件中， 这样做是为了汇总 Agent 在整个执行过程中发起过的所有工具调用，而不是只查看某一条消息。
    # 创建空列表，用于收集所有消息中的工具调用记录。类型标注表示列表中的每项预期是一个字典，键为字符串，值可以是任意类型
    all_tool_calls: list[dict[str, Any]] = []

    # 遍历 Agent 执行过程中的所有消息，因为工具调用可能出现在任意一条 AI 消息中，不一定只在最后一条
    for message in messages:
        # 安全地读取当前消息的 tool_calls 属性。
        # - 如果消息没有该属性，就得到 None。
        # - 如果属性值为 None 或空值，就统一当作空列表。
        # 这样普通的用户消息、工具消息也可以参与遍历，不需要区分消息类型。
        tool_calls = getattr(message, "tool_calls", None) or []

        # 把当前消息中的工具调用逐项追加到总列表里。使用 extend 是为了合并列表中的元素；如果用 append，会把整组工具调用作为一个嵌套列表放进去。
        all_tool_calls.extend(tool_calls)

    # 开始创建并返回项目定义的 AgentRunResponse，将上面整理出的数据放入响应对象。
    return AgentRunResponse(
        answer=answer,
        messages=items,
        used_tools=bool(all_tool_calls),
        tool_calls=all_tool_calls,
        metadata={
            "message_count": len(messages),
            "tool_call_count": len(all_tool_calls),
        },
    )