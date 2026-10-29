# 用于启动异步 main() 函数
import asyncio

# 导入 Qwen 供应商实现
from app.llm.providers.qwen import QwenProvider

# 导入统一的大模型消息、请求和角色模型
from app.llm.schemas import LLMMessage, LLMRequest, LLMRole




# 用于直接测试 Qwen Provider 是否能调用通义千问模型



async def main():
    # 创建 Qwen Provider。
    # 它会从 settings / .env 中读取：
    # DASHSCOPE_API_KEY、QWEN_BASE_URL 等配置。
    provider = QwenProvider()

    # 构造一次大模型调用请求
    request = LLMRequest(
        # 指定要使用的 Qwen 模型
        model="qwen-plus",

        # 对话消息列表
        messages=[
            # 系统消息：定义 AI 身份和行为
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="你是一个专业的 AI Agent 课程助教。",
            ),

            # 用户消息：实际向模型提出的问题
            LLMMessage(
                role=LLMRole.USER,
                content="请用一句话解释什么是统一 LLM Provider 架构。",
            ),
        ],

        # 控制生成随机性；0.7 是常见默认值
        temperature=0.7,

        # False 表示非流式调用：
        # 等模型生成完整回答后，一次性返回。
        stream=False,
    )

    # 调用 Qwen API，返回项目统一格式的 LLMResponse
    response = await provider.chat(request)

    # 输出供应商名称，例如 QWEN
    print("provider:", response.provider)

    # 输出实际使用的模型名称
    print("model:", response.model)

    # 输出模型生成的回答
    print("content:", response.content)

    # 输出输入、输出、总 Token 用量
    print("usage:", response.usage.model_dump())


# 仅当直接运行此文件时才执行 main()
if __name__ == "__main__":
    asyncio.run(main())