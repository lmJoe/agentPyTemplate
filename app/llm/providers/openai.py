# 用于标注流式方法的返回类型
from collections.abc import AsyncGenerator

# 异步 HTTP 请求库
import httpx

# 项目配置，例如 OPENAI_API_KEY、OPENAI_BASE_URL
from app.core.config import settings

# 日志工具
from app.core.logging import get_logger

# 大模型供应商抽象接口
from app.llm.base import BaseLLMProvider

# 项目自定义异常
from app.llm.errors import (
    LLMProviderConfigError,
    LLMProviderError,
    LLMProviderResponseParseError,
    LLMProviderTimeoutError,
)

# 创建统一超时设置的 HTTP 客户端
from app.llm.http_client import create_llm_http_client

# 大模型请求、响应和 Token 用量数据模型
from app.llm.schemas import (
    LLMProviderName,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
)


# 使用当前文件模块名创建日志记录器
logger = get_logger(__name__)


# OpenAI 的具体 Provider。
# 必须实现 BaseLLMProvider 规定的 chat() 和 stream_chat()。
class OpenAIProvider(BaseLLMProvider):

    # 初始化 OpenAI Provider。
    # 读取 API Key、接口地址、默认模型和超时配置。
    def __init__(self):
        # 没有 API Key 时，立即报配置错误
        if not settings.openai_api_key:
            raise LLMProviderConfigError(
                message="OpenAI API Key 未配置",
                provider=LLMProviderName.OPENAI.value,
            )

        # 标识当前供应商为 OpenAI
        self.provider_name = LLMProviderName.OPENAI

        # 保存 OpenAI API Key
        self.api_key = settings.openai_api_key

        # 删除地址末尾的 /，避免拼接 URL 时出现 //
        self.base_url = settings.openai_base_url.rstrip("/")

        # 请求没有指定模型时使用的默认模型
        self.default_model = "gpt-4.1-mini"

        # HTTP 读取超时时间
        self.timeout_seconds = 60

    # 非流式聊天：
    # 等待模型完整生成回答后，一次性返回 LLMResponse。
    async def chat(self, request: LLMRequest) -> LLMResponse:
        # Responses API 的地址
        url = f"{self.base_url}/responses"

        # 构造发送给 OpenAI 的请求体
        payload = {
            # 优先使用请求中指定的模型，否则用默认模型
            "model": request.model or self.default_model,

            # 将项目消息列表转换为 Responses API 的 input
            "input": self._messages_to_input(request),
        }

        # 记录调用开始日志
        logger.info(
            f"llm_chat_start provider=openai model={payload['model']} "
            f"message_count={len(request.messages)}"
        )

        try:
            # 创建异步 HTTP 客户端
            async with create_llm_http_client(self.timeout_seconds) as client:
                # 向 OpenAI 发送 POST 请求
                response = await client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )

                # 状态码不是 2xx 时抛出 HTTPStatusError
                response.raise_for_status()

        # 请求超时，例如网络慢或模型生成时间过长
        except httpx.TimeoutException as exc:
            logger.exception("llm_chat_timeout provider=openai")
            raise LLMProviderTimeoutError(
                message="OpenAI 调用超时",
                provider=self.provider_name.value,
            ) from exc

        # HTTP 401、429、500 等错误
        except httpx.HTTPStatusError as exc:
            logger.exception(
                f"llm_chat_http_error provider=openai "
                f"status_code={exc.response.status_code}"
            )
            raise LLMProviderError(
                message="OpenAI HTTP 调用失败",
                provider=self.provider_name.value,
                status_code=exc.response.status_code,
                raw_error=exc.response.text,
            ) from exc

        # 网络、DNS、连接被拒绝等请求错误
        except httpx.RequestError as exc:
            logger.exception("llm_chat_request_error provider=openai")
            raise LLMProviderError(
                message="OpenAI 网络请求失败",
                provider=self.provider_name.value,
                raw_error=repr(exc),
            ) from exc

        # 将 HTTP 响应 JSON 转为 Python 字典
        data = response.json()

        try:
            # 解析成项目统一的 LLMResponse
            return self._parse_response(data)

        # JSON 结构不符合预期时，转换为项目异常
        except Exception as exc:
            logger.exception("llm_chat_parse_error provider=openai")
            raise LLMProviderResponseParseError(
                message="OpenAI 响应解析失败",
                provider=self.provider_name.value,
                raw_error=str(data),
            ) from exc

    # 流式聊天接口。
    # 当前仅为了满足父类接口而保留，尚未实现。
    async def stream_chat(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        raise NotImplementedError(
            "OpenAI Responses API streaming 会在后续 Streaming 章节单独完善"
        )

    # 生成 OpenAI API 请求头。
    def _headers(self) -> dict[str, str]:
        return {
            # Bearer Token 身份认证
            "Authorization": f"Bearer {self.api_key}",

            # 请求体格式为 JSON
            "Content-Type": "application/json",
        }

    # 将项目中的多条 LLMMessage 转换为一个 input 字符串。
    def _messages_to_input(self, request: LLMRequest) -> str:
        lines = []

        # 例如：
        # system: 你是一个助手
        # user: 什么是 AI Agent？
        for message in request.messages:
            lines.append(
                f"{message.role.value}: {message.content}"
            )

        # 用换行拼成一个完整字符串
        return "\n".join(lines)

    # 将 OpenAI Responses API 的完整响应转换为项目统一响应。
    def _parse_response(self, data: dict) -> LLMResponse:
        # 读取模型最终文本内容
        content = data.get("output_text", "")

        # usage 不存在时用空字典兜底
        usage_data = data.get("usage") or {}

        # 将 OpenAI 的 Token 字段映射到项目统一 LLMUsage
        usage = LLMUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # 返回项目统一格式
        return LLMResponse(
            provider=self.provider_name,
            model=data.get("model", self.default_model),
            content=content,
            usage=usage,
            raw_response=data,
        )