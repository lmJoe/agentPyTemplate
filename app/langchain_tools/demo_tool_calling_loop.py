import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_tools.executor import langchain_tool_executor
from app.langchain_tools.registry import langchain_tool_registry


# 工具调用闭环示例，演示模型如何调用工具查询真实信息，然后根据工具返回结果生成最终回答

async def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0,
    )

    tools = langchain_tool_registry.get_many([
        "query_order",
        "query_logistics",
        "transfer_human",
    ])

    model_with_tools = model.bind_tools(tools)

    messages = [
        SystemMessage(
            content=(
                "你是一个跨境电商客服助手。\n"
                "当用户询问订单、物流、发货状态时，必须优先调用工具查询真实信息。\n"
                "工具返回结果后，请用礼貌、简洁的中文回复用户。\n"
                "不要编造订单状态、物流公司或物流单号。"
            )
        ),
        HumanMessage(
            content="帮我查一下订单 10001 到哪了？"
        ),
    ]

    first_response = await model_with_tools.ainvoke(messages)

    print("first_response content:")
    print(first_response.content)
    print("=" * 80)

    print("tool_calls:")
    print(first_response.tool_calls)
    print("=" * 80)

    if not first_response.tool_calls:
        print("模型没有请求工具，直接回答：")
        print(first_response.content)
        return

    # 执行模型请求的工具，并获取工具结果消息
    tool_messages = await langchain_tool_executor.execute_tool_calls(
        first_response.tool_calls
    )

    # 加入模型的回复，其中包含它请求调用的工具信息。这里为什么要append first_response
    # 原因在于：工具调用后，messages 顺序应该是：
    # SystemMessage
    # HumanMessage
    # AIMessage(tool_calls=[...])
    # ToolMessage(tool_call_id=...)
    # AIMessage(final answer)

    # 如果模型第一次返回 tool_calls 后，直接 append ToolMessage。，少了AIMessage(tool_calls)
    # 正确流程必须把第一次模型返回的 AIMessage 也放进 messages。
    # 因为 ToolMessage 是回应这个 AIMessage 里的 tool_call。
    # 如果缺了 AIMessage，模型可能不知道 ToolMessage 是从哪来的。



    messages.append(first_response)
    # 加入每个工具执行后的结果消息。
    messages.extend(tool_messages)

    # 将完整对话交给模型，让模型根据工具结果生成最终答复
    final_response = await model.ainvoke(messages)

    print("final answer:")
    print(final_response.content)


if __name__ == "__main__":
    asyncio.run(main())