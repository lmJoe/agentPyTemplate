import asyncio

from app.langchain_agents.service import langchain_agent_service

#   演示处理 Agent 执行时的异常。

async def main():
    try:
        result = await langchain_agent_service.run_ecommerce_agent(
            user_question="帮我查一下订单 unknown_999 到哪了？",
            provider="deepseek",
            model_name="deepseek-chat",
        )

        print(result.model_dump())

    except Exception as exc:
        print("Agent 执行失败：")
        print(repr(exc))


if __name__ == "__main__":
    asyncio.run(main())