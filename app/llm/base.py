


# ABC：抽象基类，用于定义统一接口
# 是 Python 代码里的“抽象接口”或“类接口”，用于规定大模型供应商类必须具备哪些能力
# 只要想接入一个新的大模型供应商，
# 就必须提供“完整回答”和“流式回答”两种调用方式。


# abstractmethod：标记“子类必须实现”的方法
from abc import ABC, abstractmethod

# AsyncGenerator：异步生成器的类型标注
from collections.abc import AsyncGenerator

# 项目中定义的大模型请求、普通响应和流式响应分片模型
from app.llm.schemas import LLMRequest, LLMResponse, LLMStreamChunk


# 所有大模型供应商的基础接口。
# 不能直接使用，需要由 DeepSeekProvider、OpenAIProvider 等子类继承并实现。
class BaseLLMProvider(ABC):

    # 非流式聊天接口。
    # 接收 LLMRequest，等待模型生成完成后，
    # 一次性返回完整的 LLMResponse。
    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        pass

    # 流式聊天接口。
    # 接收 LLMRequest，逐段返回模型生成的内容。
    #
    # AsyncGenerator[LLMStreamChunk, None] 表示：
    # - 每次 yield 的数据类型是 LLMStreamChunk
    # - 不接收调用方 send() 传入的数据
    @abstractmethod
    async def stream_chat(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        pass