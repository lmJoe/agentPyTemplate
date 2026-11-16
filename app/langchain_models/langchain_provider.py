from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessageChunk

from app.langchain_models.message_adapter import (
    to_langchain_messages,
    to_llm_response,
)
from app.langchain_models.model_factory import LangChainModelFactory
from app.llm.base import BaseLLMProvider
from app.llm.schemas import (
    LLMProviderName,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
)


class LangChainLLMProvider(BaseLLMProvider):
    def __init__(
        self,
        provider: str = "deepseek",
        model: str = "deepseek-chat",
    ):
        """
        初始化 LangChain LLM 提供商

        Args:
            provider: 模型提供商名称，可选 "deepseek"、"qwen"、"openai"，默认 "deepseek"
            model: 默认使用的模型名称，未在请求中指定时使用，默认 "deepseek-chat"
        """
        self.provider = provider
        self.model = model

    @property
    def provider_name(self) -> LLMProviderName:
        """
        获取当前提供商对应的枚举名称

        根据 provider 字符串映射到 LLMProviderName 枚举值：
        "deepseek" -> DEEPSEEK，"qwen" -> QWEN，"openai" -> OPENAI，
        未识别的提供商返回 MOCK。

        Returns:
            LLMProviderName: 对应的提供商枚举值，无法识别时为 MOCK
        """
        if self.provider == "deepseek":
            return LLMProviderName.DEEPSEEK

        if self.provider == "qwen":
            return LLMProviderName.QWEN

        if self.provider == "openai":
            return LLMProviderName.OPENAI

        return LLMProviderName.MOCK

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """
        以非流式方式调用大模型并返回完整响应

        根据请求参数创建 LangChain 模型实例，将统一消息格式转换为
        LangChain 消息格式；若请求中包含工具定义则进行绑定，
        调用模型后将结果转换为统一的 LLMResponse。

        Args:
            request: 大模型请求体，包含模型名称、消息列表、温度参数及工具定义等

        Returns:
            LLMResponse: 统一格式的模型响应，包含提供商、模型名称、输出内容、
                用量统计及原始响应数据
        """
        model = LangChainModelFactory.create(
            provider=self.provider,
            model=request.model or self.model,
            temperature=request.temperature,
            streaming=False,
        )

        messages = to_langchain_messages(request.messages)

        if request.tools:
            model = model.bind_tools(request.tools)

        ai_message = await model.ainvoke(messages)

        return to_llm_response(
            ai_message=ai_message,
            provider=self.provider_name,
            model=request.model or self.model,
        )

    async def stream_chat(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """
        以流式方式调用大模型并逐块返回响应

        根据请求参数创建流式 LangChain 模型实例，将统一消息格式转换为
        LangChain 消息格式，随后异步迭代模型输出，将每个 AIMessageChunk
        转换为统一的流式响应块并逐个产出。

        Args:
            request: 大模型请求体，包含模型名称、消息列表、温度参数及工具定义等

        Yields:
            LLMStreamChunk: 统一格式的流式响应块，包含提供商、模型名称、
                增量内容、用量统计及原始分片数据
        """
        model = LangChainModelFactory.create(
            provider=self.provider,
            model=request.model or self.model,
            temperature=request.temperature,
            streaming=True,
        )

        messages = to_langchain_messages(request.messages)

        async for chunk in model.astream(messages):
            yield self._to_stream_chunk(
                chunk=chunk,
                model=request.model or self.model,
            )

    def _to_stream_chunk(
        self,
        chunk: AIMessageChunk,
        model: str,
    ) -> LLMStreamChunk:
        """
        将 LangChain 的消息分片转换为统一的流式响应块

        提取分片中的文本内容、消息 ID 及响应元数据，封装为
        LLMStreamChunk；当前不从分片中解析用量统计与结束原因。

        Args:
            chunk: LangChain 流式输出的消息分片 AIMessageChunk
            model: 本次请求实际使用的模型名称

        Returns:
            LLMStreamChunk: 统一格式的流式响应块，包含提供商、模型名称、
                增量内容及原始分片数据
        """
        return LLMStreamChunk(
            provider=self.provider_name,
            model=model,
            content=str(chunk.content or ""),
            usage=LLMUsage(),
            finish_reason=None,
            raw_chunk={
                "id": chunk.id,
                "content": chunk.content,
                "response_metadata": chunk.response_metadata,
            },
        )