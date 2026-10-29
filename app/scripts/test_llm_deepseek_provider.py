# 运行异步函数
import asyncio

# 导入 DeepSeek Provider
from app.llm.providers.deepseek import DeepSeekProvider

# 导入统一的大模型消息、请求和角色模型
from app.llm.schemas import LLMMessage, LLMRequest, LLMRole



# 直接测试 DeepSeekProvider 是否能正常调用 DeepSeek 模型的脚本




async def main():
    # 直接创建 DeepSeek Provider。
    # 它会从 settings / .env 中读取 DeepSeek API Key、接口地址等配置。
    provider = DeepSeekProvider()

    # 构造一次大模型请求
    request = LLMRequest(
        # 指定模型
        model="deepseek-chat",

        # 对话消息列表
        messages=[
            # 系统提示词：定义 AI 的身份和行为
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="你是一个专业的 AI Agent 课程助教。",
            ),

            # 用户实际提出的问题
            LLMMessage(
                role=LLMRole.USER,
                content="请用一句话解释什么是 LLM Provider。",
            ),
        ],

        # 控制回答随机性
        temperature=0.7,

        # False 表示非流式：等完整答案生成后一次性返回
        stream=False,
    )

    # 调用 DeepSeek API，获得统一格式的 LLMResponse
    response = await provider.chat(request)

    # 输出供应商名称，例如 DEEPSEEK
    print("provider:", response.provider)

    # 输出实际使用的模型名称
    print("model:", response.model)

    # 输出模型回答内容
    print("content:", response.content)

    # 输出输入、输出、总 Token 用量
    print("usage:", response.usage.model_dump())


# 只有直接运行该 Python 文件时才执行 main()
if __name__ == "__main__":
    asyncio.run(main())