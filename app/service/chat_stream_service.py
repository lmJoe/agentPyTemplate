# 当前文件仅准备了流式聊天所需的依赖和日志对象，尚未实现流式聊天业务。

# Python 标准库：生成随机 UUID，可用于构造会话、消息或链路追踪 ID。
import uuid

# 异步生成器类型标注，例如 AsyncGenerator[str, None]：
# 通过 yield 逐段输出字符串，不接收调用方通过 asend() 传入的数据。
from collections.abc import AsyncGenerator

# Redis 异步客户端类型，供后续缓存读写等操作使用；导入本身不会建立连接。
from redis.asyncio import Redis

# SQLAlchemy 异步数据库会话类型，用于执行查询、保存消息和提交事务。
from sqlalchemy.ext.asyncio import AsyncSession

# 项目统一业务错误码，例如 LLM_CALL_FAILED，可用于流式错误事件。
from app.core.exceptions import ErrorCode

# 获取日志记录器，供当前模块记录模型调用、流式输出和异常信息。
from app.core.logging import get_logger

# 大模型供应商的统一抽象接口；stream_chat() 按块返回模型生成的内容。
from app.llm.base import BaseLLMProvider

# 模型供应商异常的基类，携带错误说明、供应商、状态码及原始错误信息。
from app.llm.errors import LLMProviderError

# 模型层统一请求结构，包含模型名称、消息列表、温度和是否流式输出等参数。
from app.llm.schemas import LLMRequest

# 会话仓库实例，封装会话创建、历史消息查询和消息保存等数据库操作。
from app.repositories.conversation_repository import conversation_repository

from app.schemas.chat import (
    # 聊天接口的请求模型，校验消息、模型名称、会话 ID 等输入字段。
    ChatRequest,
    # 聊天消息角色枚举，包括 system、user、assistant 和 tool。
    MessageRole,
    # 聊天层 Token 用量模型，记录输入、输出及总 Token 数。
    TokenUsage,
)

# 复用普通聊天服务的请求转换和消息提取逻辑；项目目录名为 service。
from app.service.chat_service import (
    # 将 ChatRequest 转为 LLMRequest，并按场景构造提示词消息。
    build_llm_request_from_chat_request,
    # 从后往前查找最近的用户消息；没有用户消息时返回最后一条消息内容。
    get_latest_user_message,
)

from app.utils.sse import (
    # 生成 event: done 的 SSE 文本，表示本次流式响应结束。
    format_done_event,
    # 生成 event: error 的 SSE 文本，携带业务错误码、说明和详情。
    format_error_event,
    # 将数据及可选事件类型、事件 ID、重连间隔格式化为 SSE 协议文本。
    format_sse,
)

# __name__ 是当前模块名，用它命名日志记录器，便于定位日志来源。
logger = get_logger(__name__)


async def stream_chat_with_ai(
    request: ChatRequest,
    llm_provider: BaseLLMProvider,
    redis_client: Redis,
    db: AsyncSession | None = None,
    redis: Redis | None = None,
) -> AsyncGenerator[str, None]:
    """
    流式返回 AI 生成的聊天内容。

    Args:
        request (ChatRequest): 聊天请求对象。
        llm_provider (BaseLLMProvider): LLM 提供者实例。
        redis_client (Redis): Redis 客户端实例。
        db (AsyncSession | None, optional): 数据库会话实例。
        redis (Redis | None, optional): Redis 客户端实例。

    Yields:
        str: 格式化的 SSE 事件字符串。
    """
    # 查找最近一次用户消息，用于构造提示词；没有用户消息时返回最后一条消息内容。
    latest_user_message = get_latest_user_message(request)

    # 构造 LLMRequest，包含模型名称、消息列表、温度和是否流式输出等参数。
    llm_request: LLMRequest = build_llm_request_from_chat_request(request)
    llm_request.stream = True

    # 组装并返回接口响应，包含模型回答、实际使用的模型等字段。
    message_id = f"m_{uuid.uuid4().hex[:8]}"

    # 初始化空字符串，用于存储模型生成的完整回答。
    full_answer = ""

    # 初始化 Token 用量模型，用于存储模型调用后的 Token 数。
    final_usage = TokenUsage()

    # 记录模型调用开始时间，用于计算耗时。
    logger.info(
        f"chat_stream_start model={llm_request.model} "
        f"message_count={len(llm_request.messages)}"
    )

    # 调用模型流式生成回答，并逐块返回。
    yield format_sse(
        event = "satrt",
        data = {
            "message_id": message_id,
            "model": llm_request.model,
            "session_id": request.session_id,
        }
    )

    try:
        async for chunk in llm_provider.stream_chat(llm_request):
            if chunk.content:
                # 累加模型生成的回答。
                full_answer += chunk.content

                # 逐块返回模型生成的回答。
                yield format_sse(
                    event="message",
                    data={
                        "content": chunk.content,
                        "message_id": message_id,

                    }
                )

            # 如果当前块包含 Token 用量信息，则更新 final_usage。
            if chunk.usage:
                final_usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens, # 提示词 Token 数。
                    completion_tokens=chunk.usage.completion_tokens, # 回答 Token 数。
                    total_tokens=chunk.usage.total_tokens, # 总 Token 数。
                )
        # 保存流式消息到数据库。
        if db and request.session_id:
            await save_stream_message(
                db=db,                              # 数据库会话实例。
                session_id=request.session_id,      # 会话 ID。
                user_message=latest_user_message,   # 用户最近一次发送的消息，传给保存函数的 user_message 参数
                assistant_message=full_answer,      # AI 流式输出拼接后的完整回答。
                model=llm_request.model,            # 使用的模型。
                usage=final_usage,                  # Token 用量。
            )

        # 记录模型调用结束时间，并返回接口响应。
        logger.info(
            f"chat_stream_success model={llm_request.model} "
            f"answer_length={len(full_answer)} "
            f"total_tokens={final_usage.total_tokens}"
        )

        # 返回接口响应，包含模型回答、实际使用的模型等字段。
        yield format_done_event(
            {
                "message_id": message_id,
                "finish_reason": "stop",
                "usage": final_usage.model_dump(),
            }
        )

    # 捕获模型供应商异常，记录错误信息并返回。
    except LLMProviderError as ex:
        logger.exception(
            f"chat_stream_llm_error provider={exc.provider} "
            f"status_code={exc.status_code}"
        )

        # 返回接口响应，包含模型调用失败的错误信息。
        yield format_error_event(
            message=exc.message,
            code=int(ErrorCode.LLM_CALL_FAILED),
            details={
                "provider": exc.provider,
                "status_code": exc.status_code,
            },
        )


    # 捕获未预料的异常，记录错误信息并返回。
    except Exception as exc:
        logger.exception(
            f"chat_stream_unhandled_error error={repr(exc)}"
        )

        yield format_error_event(
            message="流式输出失败",
            code=int(ErrorCode.INTERNAL_ERROR),
        )


# save_stream_message() 用于在流式回答结束后，把本轮用户提问和 AI 的完整回答保存到数据库，方便后续查询聊天记录、恢复对话上下文
async def save_stream_message(
    db: AsyncSession,
    session_id: str,
    user_message: Message | None = None,
    assistant_message: str | None = None,
    model: str | None = None,
    usage: TokenUsage | None = None,
):
    """
    保存流式消息到数据库。

    Args:
        db (AsyncSession): 数据库会话实例。
        session_id (str): 会话 ID。
        user_message (Message | None, optional): 用户最近一次发送的消息，默认为 None。
        assistant_message (str | None, optional): AI 流式输出拼接后的完整回答，默认为 None。
        model (str | None, optional): 使用的模型，默认为 None。
        usage (TokenUsage | None, optional): Token 用量，默认为 None。

    Returns:
        None
    """ 

    # 保存用户消息到数据库。用户最近一次的提问 user_message
    await conversation_repository.add_message(
        db=db,
        conversation_id=session_id,
        role=MessageRole.USER.value,
        content=user_message,
        model=model,
        prompt_tokens=usage.prompt_tokens,
    )

    # 保存 AI 回答到数据库。 AI 拼接后的完整回答 assistant_message
    await conversation_repository.add_message(
        db=db,
        conversation_id=session_id,
        role=MessageRole.ASSISTANT.value,
        content=assistant_message,
        model=model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )





