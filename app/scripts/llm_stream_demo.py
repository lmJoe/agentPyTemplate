# 运行异步程序
import asyncio

# 解析接口返回的 JSON 数据
import json

# 异步 HTTP 客户端
import httpx

# 读取 .env 中的配置，例如 API Key、接口地址
from app.core.config import settings


async def main():
    # 未配置 API Key 时，直接终止程序，避免发送无效请求
    if not settings.deepseek_api_key:
        raise RuntimeError("请先在 .env 中配置 DEEPSEEK_API_KEY")

    # 拼出聊天补全接口地址
    url = f"{settings.deepseek_base_url}/chat/completions"

    # 请求头：Bearer Token 身份认证，以及 JSON 请求体类型
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    # 请求体
    payload = {
        # 要使用的模型
        "model": "deepseek-chat",

        # 对话消息列表
        "messages": [
            {
                "role": "user",
                "content": "请用三句话解释什么是 AI Agent。",
            }
        ],

        # 回答随机性；越高越有发散性
        "temperature": 0.7,

        # True：服务端以流式分片持续返回内容
        "stream": True,
    }

    # 拼接所有流式分片，得到最终完整答案
    full_answer = ""

    # 创建异步 HTTP 客户端；60 秒超时
    async with httpx.AsyncClient(timeout=60) as client:
        # 发起 POST 请求，并以流式方式读取响应
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=payload,
        ) as response:
            print("status_code:", response.status_code)

            # 按行持续读取服务端返回的数据
            async for line in response.aiter_lines():
                # 忽略空行
                if not line:
                    continue

                # 流式接口通常使用 SSE 格式，每段数据以 data: 开头
                if not line.startswith("data:"):
                    continue

                # 去掉 data: 前缀
                data = line.removeprefix("data:").strip()

                # [DONE] 表示流结束
                if data == "[DONE]":
                    break

                # 将当前分片 JSON 转成 Python 字典
                chunk = json.loads(data)

                # 从响应中取出本次新增的文本片段
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content")

                if content:
                    # 拼接完整答案
                    full_answer += content

                    # 立即打印当前片段；flush=True 确保终端实时显示
                    print(content, end="", flush=True)

    # 流结束后打印完整答案
    print("\n\nfull_answer:")
    print(full_answer)


# 只有直接运行该文件时才执行 main()
if __name__ == "__main__":
    asyncio.run(main())