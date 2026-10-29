import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory


async def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7,
    )

    messages = [
        SystemMessage(content="你是一个专业 AI Agent 课程助教。"),
        HumanMessage(content="请用三句话解释 LangChain 的 ainvoke。"),
    ]

    response = await model.ainvoke(messages)

    print("content:")
    print(response.content)
    print("usage_metadata:")
    print(response.usage_metadata)


if __name__ == "__main__":
    asyncio.run(main())