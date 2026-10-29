# 用于执行异步 main() 函数
import asyncio

# 导入 DeepSeek Provider
from app.llm.providers.deepseek import DeepSeekProvider

# 导入统一的大模型消息、请求和角色模型
from app.llm.schemas import LLMMessage, LLMRequest, LLMRole




# 测试 DeepSeek 的流式输出：模型每生成一小段文本，就立刻打印，而不是等全部完成后才显示



async def main():
    # 创建 DeepSeek Provider。
    # 会从 .env 读取 DeepSeek API Key、接口地址等配置。
    provider = DeepSeekProvider()

    # 构造大模型请求
    request = LLMRequest(
        # 使用 DeepSeek 聊天模型
        model="deepseek-chat",

        # 本次只有一条用户消息
        messages=[
            LLMMessage(
                role=LLMRole.USER,
                content="请用三句话解释为什么要封装 LLM Provider。",
            ),
        ],

        # 控制生成随机性
        temperature=0.7,

        # 表示当前请求需要流式输出
        stream=True,
    )

    # 用于把所有流式文本分片拼成完整回答
    full_content = ""

    # 调用流式方法。
    # 模型每返回一个 LLMStreamChunk，就进入一次循环。
    async for chunk in provider.stream_chat(request):

        # chunk.content 是当前新增的一小段文本
        if chunk.content:
            # 拼接到完整答案中
            full_content += chunk.content

            # 立即打印当前文本分片。
            # end=""：不自动换行；
            # flush=True：立即显示到终端。
            print(chunk.content, end="", flush=True)

        # usage 通常只会在最后一个或接近最后的分片中出现
        if chunk.usage:
            print("\nusage:", chunk.usage.model_dump())

    # 流式输出结束后，打印最终拼接的完整答案
    print("\n\nfull_content:")
    print(full_content)


# 只有直接运行此文件时才执行 main()
if __name__ == "__main__":
    asyncio.run(main())