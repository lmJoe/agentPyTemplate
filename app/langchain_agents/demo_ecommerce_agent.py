import json
import asyncio

from app.langchain_agents.factory import (
    build_ecommerce_agent,
    parse_agent_result,
)

#   运行电商 Agent 模型，查询订单状态

async def main():
    agent = build_ecommerce_agent(
        provider="deepseek",
        model_name="deepseek-chat",
    )

    #   调用 Agent 模型，传入用户问题。
    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": "帮我查一下订单 10001 到哪了？",
            }
        ]
    })

    #   解析 Agent 返回的消息列表。可以看到，除了用户的提问外，还有模型的回答和工具调用结果。
    parsed = parse_agent_result(result)

    #   打印解析后的结果。可以看到，除了模型的回答外，还有工具调用参数和返回的工具输出。
    print(json.dumps(
        parsed.model_dump(),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    asyncio.run(main())