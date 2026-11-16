from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMRole,
    LLMToolCall,
    LLMUsage,
)
from app.llm.schemas import LLMProviderName


def to_langchain_message(message: LLMMessage) -> BaseMessage:
    """
    将内部统一的消息对象转换为 LangChain 消息对象。

    Args:
        message: 内部消息对象，包含角色、内容及可选的工具调用 ID。

    Returns:
        与消息角色对应的 LangChain 消息实例，如 SystemMessage、HumanMessage、
        AIMessage 或 ToolMessage。

    Raises:
        ValueError: 当工具消息缺少 tool_call_id，或消息角色不受支持时抛出。
    """
    if message.role == LLMRole.SYSTEM:
        return SystemMessage(content=message.content)

    if message.role == LLMRole.USER:
        return HumanMessage(content=message.content)

    if message.role == LLMRole.ASSISTANT:
        return AIMessage(content=message.content)

    if message.role == LLMRole.TOOL:
        if not message.tool_call_id:
            raise ValueError("ToolMessage 必须提供 tool_call_id")

        return ToolMessage(
            content=message.content,
            tool_call_id=message.tool_call_id,
        )

    raise ValueError(f"不支持的消息角色：{message.role}")


def to_langchain_messages(messages: list[LLMMessage]) -> list[BaseMessage]:
    """
    批量将内部统一的消息对象列表转换为 LangChain 消息对象列表。

    Args:
        messages: 内部消息对象列表，每个元素包含角色、内容及可选的工具调用 ID。

    Returns:
        与输入顺序一致的 LangChain 消息实例列表。

    Raises:
        ValueError: 当某条消息的角色不受支持，或工具消息缺少 tool_call_id 时抛出。
    """
    return [
        to_langchain_message(message)
        for message in messages
    ]


def to_llm_usage(ai_message: AIMessage) -> LLMUsage:
    """
    从 LangChain AI 消息中提取 token 用量并转换为内部用量对象。

    Args:
        ai_message: LangChain AI 消息实例，其 usage_metadata 中包含 token 用量信息。

    Returns:
        内部统一的 LLMUsage 实例；当用量元数据缺失时各字段取值为 0。
    """
    usage = ai_message.usage_metadata or {}

    return LLMUsage(
        prompt_tokens=usage.get("input_tokens", 0),
        completion_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )


def to_llm_tool_calls(ai_message: AIMessage) -> list[LLMToolCall]:
    """
    从 LangChain AI 消息中提取工具调用并转换为内部统一的工具调用对象列表。

    Args:
        ai_message: LangChain AI 消息实例，其 tool_calls 中可能包含模型发起的工具调用。

    Returns:
        内部统一的 LLMToolCall 实例列表；当消息不含工具调用时返回空列表。
        由于 LangChain 已解析调用参数，raw_arguments 统一置为空字符串。
    """
    tool_calls: list[LLMToolCall] = []

    for item in ai_message.tool_calls or []:
        tool_calls.append(
            LLMToolCall(
                id=item.get("id", ""),
                name=item.get("name", ""),
                arguments=item.get("args", {}),
                raw_arguments="",
            )
        )

    return tool_calls


def to_llm_response(
    ai_message: AIMessage,
    provider: LLMProviderName,
    model: str,
) -> LLMResponse:
    """
    将 LangChain AI 消息转换为内部统一的 LLM 响应对象。

    Args:
        ai_message: LangChain AI 消息实例，包含模型返回的文本内容、
            用量元数据、工具调用及响应元数据。
        provider: 模型服务提供商标识，将写入响应对象的 provider 字段。
        model: 模型名称，将写入响应对象的 model 字段。

    Returns:
        内部统一的 LLMResponse 实例，包含文本内容、token 用量、工具调用、
        结束原因及原始响应元数据；各来源字段缺失时取对应的默认值。
    """
    return LLMResponse(
        provider=provider,
        model=model,
        content=str(ai_message.content or ""),
        usage=to_llm_usage(ai_message),
        tool_calls=to_llm_tool_calls(ai_message),
        finish_reason=(ai_message.response_metadata or {}).get("finish_reason"),
        raw_response={
            "id": ai_message.id,
            "response_metadata": ai_message.response_metadata,
            "usage_metadata": ai_message.usage_metadata,
            "tool_calls": ai_message.tool_calls,
        },
    )