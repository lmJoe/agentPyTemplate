# 解析大模型接口返回的 JSON 字符串
import json

# 用于标注“异步流式生成器”的返回类型
from collections.abc import AsyncGenerator

# 异步 HTTP 请求库
import httpx

# 获取项目统一日志记录器
from app.core.logging import get_logger

# 大模型供应商抽象基类
from app.llm.base import BaseLLMProvider

# 项目自定义异常
from app.llm.errors import (
    LLMProviderConfigError,        # API Key、Base URL 等配置问题
    LLMProviderError,              # 通用供应商调用异常
    LLMProviderResponseParseError, # 模型响应结构无法解析
    LLMProviderTimeoutError,       # 请求超时
)

# 创建带统一超时设置的异步 HTTP 客户端
from app.llm.http_client import create_llm_http_client

# 项目内部统一的大模型请求和响应数据模型
from app.llm.schemas import (
    LLMProviderName,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
)


# 使用当前模块名创建日志记录器
logger = get_logger(__name__)


# OpenAI 兼容接口供应商的通用实现。
# DeepSeek、其他兼容 /chat/completions 的服务都可以继承该类。
class OpenAICompatibleProvider(BaseLLMProvider):

    # 子类必须指定具体供应商名称，例如：
    # provider_name = LLMProviderName.DEEPSEEK
    provider_name: LLMProviderName

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        timeout_seconds: float = 60,
    ):
        # 未配置 API Key 时，直接报配置错误
        if not api_key:
            raise LLMProviderConfigError(
                message="LLM API Key 未配置",
                provider=self.provider_name.value,
            )

        # 保存 API Key，用于 HTTP Bearer 认证
        self.api_key = api_key

        # 删除 URL 末尾的 /，避免后续拼接出 //
        self.base_url = base_url.rstrip("/")

        # 请求未传 model 时使用的默认模型
        self.default_model = default_model

        # HTTP 请求超时时间
        self.timeout_seconds = timeout_seconds

    # 非流式调用：
    # 等待模型生成完整回答后，一次性返回 LLMResponse。
    async def chat(self, request: LLMRequest) -> LLMResponse:
        # 构建请求 JSON；stream=False 表示非流式
        payload = self._build_payload(request=request, stream=False)

        # OpenAI 兼容聊天接口地址
        url = f"{self.base_url}/chat/completions"

        # 记录调用开始日志
        logger.info(
            f"llm_chat_start provider={self.provider_name.value} "
            f"model={payload['model']} message_count={len(request.messages)}"
        )

        try:
            # 创建异步客户端；退出 async with 时自动关闭连接
            async with create_llm_http_client(self.timeout_seconds) as client:
                # 发起 POST 请求
                response = await client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )

                # HTTP 状态码非 2xx 时抛出 HTTPStatusError
                response.raise_for_status()

        # 请求超时，例如模型长时间无响应
        except httpx.TimeoutException as exc:
            logger.exception(
                f"llm_chat_timeout provider={self.provider_name.value}"
            )
            raise LLMProviderTimeoutError(
                message="大模型调用超时",
                provider=self.provider_name.value,
            ) from exc

        # HTTP 401、429、500 等状态码错误
        except httpx.HTTPStatusError as exc:
            logger.exception(
                f"llm_chat_http_error provider={self.provider_name.value} "
                f"status_code={exc.response.status_code}"
            )
            raise LLMProviderError(
                message="大模型 HTTP 调用失败",
                provider=self.provider_name.value,
                status_code=exc.response.status_code,
                raw_error=exc.response.text,
            ) from exc

        # 网络、DNS、连接被拒绝等请求错误
        except httpx.RequestError as exc:
            logger.exception(
                f"llm_chat_request_error provider={self.provider_name.value}"
            )
            raise LLMProviderError(
                message="大模型网络请求失败",
                provider=self.provider_name.value,
                raw_error=repr(exc),
            ) from exc

        # 将完整 HTTP 响应 JSON 转为 Python 字典
        data = response.json()

        try:
            # 解析为项目内部统一的 LLMResponse
            llm_response = self._parse_chat_response(data)

        # 响应缺少字段、格式错误等解析问题
        except Exception as exc:
            logger.exception(
                f"llm_chat_parse_error provider={self.provider_name.value}"
            )
            raise LLMProviderResponseParseError(
                message="大模型响应解析失败",
                provider=self.provider_name.value,
                raw_error=json.dumps(data, ensure_ascii=False),
            ) from exc

        # 记录调用成功日志及 Token 总量
        logger.info(
            f"llm_chat_success provider={self.provider_name.value} "
            f"model={llm_response.model} "
            f"total_tokens={llm_response.usage.total_tokens}"
        )

        return llm_response

    # 流式调用：
    # 持续 yield 多个 LLMStreamChunk，而不是一次返回完整回答。
    async def stream_chat(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        # 构建请求 JSON；stream=True 表示流式输出
        payload = self._build_payload(request=request, stream=True)

        # OpenAI 兼容流式聊天接口
        url = f"{self.base_url}/chat/completions"

        logger.info(
            f"llm_stream_start provider={self.provider_name.value} "
            f"model={payload['model']} message_count={len(request.messages)}"
        )

        try:
            async with create_llm_http_client(self.timeout_seconds) as client:
                # 以流式方式发起请求
                async with client.stream(
                    "POST",
                    url,
                    headers=self._headers(),
                    json=payload,
                ) as response:

                    # 非 2xx 状态码时抛出错误
                    response.raise_for_status()

                    # 按行读取 SSE 流式响应
                    async for line in response.aiter_lines():
                        # 跳过空行
                        if not line:
                            continue

                        # 只处理 SSE 的 data: 行
                        if not line.startswith("data:"):
                            continue

                        # 去掉 data: 前缀
                        data = line.removeprefix("data:").strip()

                        # [DONE] 表示模型已经完成输出
                        if data == "[DONE]":
                            break

                        # 当前流式分片 JSON → Python 字典
                        chunk_data = json.loads(data)

                        # 转为项目统一的 LLMStreamChunk
                        chunk = self._parse_stream_chunk(chunk_data)

                        # 逐块返回给调用方
                        yield chunk

        # 流式请求超时
        except httpx.TimeoutException as exc:
            logger.exception(
                f"llm_stream_timeout provider={self.provider_name.value}"
            )
            raise LLMProviderTimeoutError(
                message="大模型流式调用超时",
                provider=self.provider_name.value,
            ) from exc

        # 流式请求 HTTP 状态码错误
        except httpx.HTTPStatusError as exc:
            logger.exception(
                f"llm_stream_http_error provider={self.provider_name.value} "
                f"status_code={exc.response.status_code}"
            )
            raise LLMProviderError(
                message="大模型流式 HTTP 调用失败",
                provider=self.provider_name.value,
                status_code=exc.response.status_code,
                raw_error=exc.response.text,
            ) from exc

        # 流式网络错误
        except httpx.RequestError as exc:
            logger.exception(
                f"llm_stream_request_error provider={self.provider_name.value}"
            )
            raise LLMProviderError(
                message="大模型流式网络请求失败",
                provider=self.provider_name.value,
                raw_error=repr(exc),
            ) from exc

    # 生成请求头
    def _headers(self) -> dict[str, str]:
        return {
            # Bearer API Key 身份认证
            "Authorization": f"Bearer {self.api_key}",

            # 请求体为 JSON
            "Content-Type": "application/json",
        }

    # 将项目内部 LLMRequest 转成供应商 API 所需 JSON
    def _build_payload(
        self,
        request: LLMRequest,
        stream: bool,
    ) -> dict:
        payload = {
            # 请求没有指定模型时使用默认模型
            "model": request.model or self.default_model,

            # 将 LLMMessage 转为 API 所需的 role/content 字典
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in request.messages
            ],

            # 控制生成随机性
            "temperature": request.temperature,

            # 是否流式返回
            "stream": stream,
        }

        # 只有调用方传了 max_tokens 才发送该参数
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        return payload

    # 将非流式响应解析为 LLMResponse
    def _parse_chat_response(self, data: dict) -> LLMResponse:
        # 取第一条候选回答
        choice = data["choices"][0]

        # 非流式回答内容位于 message 中
        message = choice["message"]

        # usage 可能不存在，因此设置空字典兜底
        usage_data = data.get("usage") or {}

        # 统一构造 Token 用量对象
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        # 返回项目统一的完整模型响应
        return LLMResponse(
            provider=self.provider_name,
            model=data.get("model", self.default_model),
            content=message.get("content", ""),
            usage=usage,
            raw_response=data,
        )

    # 将单个流式响应分片解析为 LLMStreamChunk
    def _parse_stream_chunk(self, data: dict) -> LLMStreamChunk:
        # 取第一条候选分片
        choice = data["choices"][0]

        # 流式新增文本通常位于 delta 中
        delta = choice.get("delta") or {}

        # 有些供应商只会在最后一个分片附带 usage
        usage_data = data.get("usage")

        usage = None

        # 存在 Token 用量时进行解析
        if usage_data:
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        # 返回当前流式分片
        return LLMStreamChunk(
            provider=self.provider_name,
            model=data.get("model", self.default_model),
            content=delta.get("content") or "",
            finish_reason=choice.get("finish_reason"),
            usage=usage,
            raw_chunk=data,
        )