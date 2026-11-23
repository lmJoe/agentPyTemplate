import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage

from app.langchain_agent_rag.schemas import (
    AgentRAGMessageItem,
    AgentRAGRunResponse,
    AgentRAGSource,
)
from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_rag.tools import search_knowledge_base_tool
from app.langchain_tools.registry import langchain_tool_registry


def build_agent_rag_model(
    provider: str = "deepseek",
    model_name: str = "deepseek-chat",
    temperature: float = 0,
):
    """根据指定供应商和模型名称，创建用于 Agent 的语言模型。"""
    return LangChainModelFactory.create(
        provider=provider,
        model=model_name,
        temperature=temperature,
    )


def build_ecommerce_agent_with_rag(
    provider: str = "deepseek",
    model_name: str = "deepseek-chat",
):
    """创建包含电商业务工具和知识库检索工具的客服 Agent。"""

    # 创建语言模型；temperature=0 用于让客服回答更稳定。
    model = build_agent_rag_model(
        provider=provider,
        model_name=model_name,
        temperature=0,
    )

    # 从工具注册表中获取订单、物流和转人工等业务工具。
    business_tools = langchain_tool_registry.get_many(
        [
            "query_order",
            "query_logistics",
            "transfer_human",
        ]
    )

    # 将业务工具和知识库检索工具合并，提供给 Agent 使用。
    tools = [
        *business_tools,
        search_knowledge_base_tool,
    ]

    # 创建 Agent，并通过系统提示词定义角色、工具用途和处理规则。
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "你是一个跨境电商平台的智能客服 Agent。\n"
            "\n"
            "你可以使用两类工具：\n"
            "1. 业务工具：查询订单、查询物流、创建人工客服工单。\n"
            "2. 知识库工具：查询售后规则、退款规则、课程说明、员工制度等文档内容。\n"
            "\n"
            "核心规则：\n"
            "1. 当用户询问订单状态、发货状态、物流状态时，优先调用 query_order 或 query_logistics。\n"
            "2. 当用户询问退款规则、售后规则、公司制度、课程阶段等知识性问题时，优先调用 search_knowledge_base。\n"
            "3. 当用户问题同时包含订单状态和规则判断时，可以先调用 query_order，再调用 search_knowledge_base。\n"
            "4. 不要编造订单状态、物流公司、物流单号。\n"
            "5. 不要编造售后规则、退款规则、公司制度。\n"
            "6. 如果知识库工具返回无法确认，要明确说明无法从知识库确认。\n"
            "7. 如果用户没有提供订单号，不要调用 query_order，要先追问订单号。\n"
            "8. 如果问题超出 AI 能力范围，建议转人工。\n"
            "9. 最终回答要简洁、礼貌、可执行。\n"
            "10. 如果回答使用了知识库内容，要在回答中说明依据来自知识库。"
        ),
    )


def message_to_item(message: BaseMessage) -> AgentRAGMessageItem:
    """将 LangChain 消息转换为项目定义的消息数据模型。"""

    # 读取消息中的工具调用信息；没有工具调用时使用空列表。
    tool_calls = getattr(message, "tool_calls", None) or []

    # 读取工具调用 ID 和工具名称；普通消息可能没有这些属性。
    tool_call_id = getattr(message, "tool_call_id", None)
    name = getattr(message, "name", None)

    # 将消息正文转换为字符串，便于保存到响应模型中。
    content = message.content
    if isinstance(content, list):
        content_text = str(content)
    else:
        content_text = str(content or "")

    # 统一构造项目使用的消息模型。
    return AgentRAGMessageItem(
        type=message.type,
        content=content_text,
        name=name,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
    )


def extract_sources_from_tool_message_content(
    content: str,
) -> list[AgentRAGSource]:
    """
    从知识库工具返回的 JSON 字符串中提取引用来源。

    当前实现假设工具返回内容中包含 sources 字段，
    且其格式与 RAGAnswer.model_dump() 序列化后的结构一致。
    """
    try:
        # 将工具返回的 JSON 字符串解析为字典。
        data = json.loads(content)
    except Exception:
        # 内容不是有效 JSON 时，无法提取来源，返回空列表。
        return []

    # 获取来源列表；字段不存在或为空时按空列表处理。
    raw_sources = data.get("sources") or []

    sources = []

    for item in raw_sources:
        # 跳过格式不符合预期的来源条目。
        if not isinstance(item, dict):
            continue

        # 将来源字典转换为 AgentRAGSource 模型。
        sources.append(
            AgentRAGSource(
                document_id=item.get("document_id"),
                chunk_id=item.get("chunk_id"),
                source=item.get("source"),
                content_preview=item.get("content_preview", ""),
            )
        )

    return sources


def parse_agent_rag_result(
    result: dict[str, Any],
) -> AgentRAGRunResponse:
    """将 Agent 执行结果整理为统一的 AgentRAGRunResponse。"""

    # 取出 Agent 执行期间的消息列表。
    messages = result.get("messages", [])

    # 将 LangChain 消息逐条转换为项目自己的消息模型。
    items = [
        message_to_item(message)
        for message in messages
    ]

    # 默认没有最终回答；如果有消息，则取最后一条消息的正文。
    answer = ""
    if messages:
        answer = str(messages[-1].content or "")

    # 汇总所有消息中的工具调用和知识库引用。
    all_tool_calls: list[dict[str, Any]] = []
    sources: list[AgentRAGSource] = []
    used_rag = False

    for message in messages:
        # 收集该消息中的工具调用。
        tool_calls = getattr(message, "tool_calls", None) or []
        all_tool_calls.extend(tool_calls)

        # 工具消息可能包含工具执行结果。
        if message.type == "tool":
            name = getattr(message, "name", None)

            # 如果消息来自知识库工具，标记使用了 RAG 并提取来源。
            if name == "search_knowledge_base":
                # 标记使用了 RAG 并提取来源。
                used_rag = True
                # 从工具调用结果中提取引用来源。
                sources.extend(
                    extract_sources_from_tool_message_content(
                        str(message.content or "")
                    )
                )

    # 组装统一响应，包含回答、工具使用情况、消息、来源和统计信息。
    return AgentRAGRunResponse(
        answer=answer,
        used_tools=bool(all_tool_calls),
        used_rag=used_rag,
        tool_calls=all_tool_calls,
        messages=items,
        sources=sources,
        metadata={
            "message_count": len(messages),
            "tool_call_count": len(all_tool_calls),
            "source_count": len(sources),
        },
    )