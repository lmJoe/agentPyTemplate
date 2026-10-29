from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory

import asyncio


# 演示 LangChain ChatModel 的流式输出

# 同步流式调用
# def main():

# 异步流式调用方法
async def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7,
        streaming=True, # 启用流式输出
    )

    messages = [
        SystemMessage(content="你是一个专业 AI Agent 课程助教。"),
        HumanMessage(content="请用三句话解释 LangChain 的 stream。"),
    ]

    full_text = ""

    # 使用异步流式输出的方式调用模型
    async for chunk in model.astream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_text += chunk.content

    
    # 使用流式输出的方式调用模型
    # for chunk in model.stream(messages):
    #     if chunk.content:
    #         print(chunk.content, end="", flush=True)
    #         full_text += chunk.content

    print()
    print("=" * 80)
    print("full_text:")
    print(full_text)


if __name__ == "__main__":
    # 同步流式调用
    # main()

    # 异步流式调用
    asyncio.run(main())