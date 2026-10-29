# 用于生成会话、消息、链路追踪等唯一 ID
import uuid

# Redis 异步客户端类型
from redis.asyncio import Redis

# SQLAlchemy 异步数据库会话类型
from sqlalchemy.ext.asyncio import AsyncSession

# 项目配置，例如默认模型名称
from app.core.config import settings

# 项目统一业务异常和错误码
from app.core.exceptions import AppException, ErrorCode

# 日志工具
from app.core.logging import get_logger

# 大模型 Provider 的统一抽象接口
from app.llm.base import BaseLLMProvider

# 大模型调用过程中可能抛出的异常
from app.llm.errors import LLMProviderError

# 根据模型名创建 DeepSeek、Qwen 或 OpenAI Provider
from app.llm.factory import LLMProviderFactory

# 大模型层的统一消息、请求和角色模型
from app.llm.schemas import LLMMessage, LLMRequest, LLMRole

# Redis 聊天回答缓存的读写方法
from app.redis.cache import (
    cache_chat_response,
    get_cached_chat_response,
)

# 会话和消息数据库持久化仓库
from app.repositories.conversation_repository import conversation_repository

# 聊天业务层的请求、响应及相关模型
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageRole,
    SourceDocument,
    TokenUsage,
)

# 引入提示词
from app.prompts.base import PromptScenario
from app.service.prompt_service import prompt_service

# 为当前聊天服务文件创建专用日志对象
logger = get_logger(__name__)


# 聊天核心业务方法。
# 流程：
# 1. 查 Redis 缓存
# 2. 缓存未命中时调用真实 LLM
# 3. 写入 Redis 缓存
# 4. 保存聊天记录到 PostgreSQL
# 5. 返回 ChatResponse
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession | None = None,
    redis: Redis | None = None,
    llm_provider: BaseLLMProvider | None = None,
) -> ChatResponse:
    # 获取当前对话中最近的一条用户消息
    latest_user_message = get_latest_user_message(request)

    # 优先使用请求指定的模型；
    # 未指定时使用 settings.default_model。
    model = request.model or settings.default_model

    # 记录聊天开始日志
    logger.info(
        f"chat_start model={model} "
        f"message_count={len(request.messages)}"
    )

    # 如果注入了 Redis 客户端，优先读取回答缓存
    if redis:
        cached_answer = await get_cached_chat_response(
            redis=redis,
            question=latest_user_message,
        )

        # 缓存命中后直接返回，不再调用大模型
        if cached_answer:
            logger.info("chat_response_cache_hit")

            return ChatResponse(
                # 使用缓存中的回答
                answer=cached_answer,

                # 当前请求使用的模型名称
                model=model,

                # 会话 ID 由请求携带
                session_id=request.session_id,

                # 每次响应生成新的消息 ID
                message_id=f"m_{uuid.uuid4().hex[:8]}",

                # 缓存回答没有本次真实模型调用，因此用量为 0
                usage=TokenUsage(),

                # 缓存命中时当前不返回来源文档
                sources=[],

                # 当前请求的链路追踪 ID
                trace_id=f"trace_{uuid.uuid4().hex[:8]}",
            )

    # 若路由层没有注入 Provider，
    # 则根据默认模型自动创建对应 Provider。
    llm_provider = llm_provider or LLMProviderFactory.create()

    # 将聊天接口层 ChatRequest 转换为模型层 LLMRequest
    llm_request = build_llm_request_from_chat_request(request)

    try:
        # 调用真实的大模型：
        # DeepSeekProvider、QwenProvider 或 OpenAIProvider
        llm_response = await llm_provider.chat(llm_request)

    # 捕获大模型供应商统一异常
    except LLMProviderError as exc:
        # 记录异常堆栈和供应商信息
        logger.exception(
            f"chat_llm_provider_error provider={exc.provider} "
            f"status_code={exc.status_code}"
        )

        # 转换为项目统一业务异常；
        # 全局异常处理器会将其包装为统一 API 响应。
        raise AppException(
            message=exc.message,
            code=ErrorCode.LLM_CALL_FAILED,
            status_code=500,
            data={
                "provider": exc.provider,
                "status_code": exc.status_code,
            },
        ) from exc

    # 获取大模型生成的完整回答文本
    answer = llm_response.content

    # 将模型层 Token 用量转换为聊天层 TokenUsage
    usage = TokenUsage(
        prompt_tokens=llm_response.usage.prompt_tokens,
        completion_tokens=llm_response.usage.completion_tokens,
        total_tokens=llm_response.usage.total_tokens,
    )

    # 若 Redis 可用，将最新问题和回答写入缓存
    if redis:
        await cache_chat_response(
            redis=redis,
            question=latest_user_message,
            answer=answer,
        )

    # 若数据库会话和 session_id 都存在，将聊天记录保存到 PostgreSQL
    if db and request.session_id:
        # 保存用户最新提问
        await conversation_repository.add_message(
            db=db,
            conversation_id=request.session_id,
            role=MessageRole.USER.value,
            content=latest_user_message,
            model=model,
            prompt_tokens=usage.prompt_tokens,
        )

        # 保存 AI 回答及其 Token 用量
        await conversation_repository.add_message(
            db=db,
            conversation_id=request.session_id,
            role=MessageRole.ASSISTANT.value,
            content=answer,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    # 记录调用成功日志
    logger.info(
        f"chat_success model={model} "
        f"answer_length={len(answer)} "
        f"total_tokens={usage.total_tokens}"
    )

    # 组装并返回接口响应
    return ChatResponse(
        # 模型回答
        answer=answer,

        # 实际使用的模型
        model=model,

        # 未传 session_id 时临时生成一个会话 ID
        session_id=request.session_id or f"s_{uuid.uuid4().hex[:8]}",

        # 为当前 AI 回答生成唯一消息 ID
        message_id=f"m_{uuid.uuid4().hex[:8]}",

        # 返回 Token 用量
        usage=usage,

        # 当前仅模拟 RAG 文档来源
        sources=build_mock_sources(latest_user_message),

        # 链路追踪 ID
        trace_id=f"trace_{uuid.uuid4().hex[:8]}",
    )


# 将聊天业务层请求 ChatRequest 转换为模型层请求 LLMRequest。
# ChatRequest 面向 API 调用方；
# LLMRequest 面向具体的大模型 Provider。
def build_llm_request_from_chat_request(
    request: ChatRequest,
) -> LLMRequest:
    return LLMRequest(
        # 透传请求指定的模型名称
        model=request.model,
        # 将 ChatMessage 列表转换为 LLMMessage 列表 (内部传递提示词)
        messages = build_prompt_messages_for_chat(request),

        # 将 ChatMessage 列表转换为 LLMMessage 列表
        # messages=[
        #     LLMMessage(
        #         # 将聊天层角色转换为大模型层角色。
        #         # 例如 MessageRole.USER.value == "user"，
        #         # 最终转成 LLMRole.USER。
        #         role=LLMRole(message.role.value),

        #         # 原样保留消息文本
        #         content=message.content,
        #     )
        #     for message in request.messages
        # ],

        # 透传生成随机性参数
        temperature=request.temperature,

        # 透传是否使用流式输出
        stream=request.stream,
    )


# 获取消息列表中最近的一条用户消息。
def get_latest_user_message(
    request: ChatRequest,
) -> str:
    # reversed() 从消息列表末尾向前遍历
    for message in reversed(request.messages):
        # 找到的第一条 USER 消息就是最近用户提问
        if message.role == MessageRole.USER:
            return message.content

    # 理论上 ChatRequest 应至少包含一条消息。
    # 如果没有 USER 角色消息，则退回使用最后一条消息。
    return request.messages[-1].content


# 模拟 RAG 检索来源。
# 当前没有真正查询向量数据库或知识库。
def build_mock_sources(
    question: str,
) -> list[SourceDocument]:
    # 问题不含 RAG 或知识库时，不返回来源
    if "RAG" not in question and "知识库" not in question:
        return []

    # 问题涉及 RAG 或知识库时，返回固定模拟文档
    return [
        SourceDocument(
            # 模拟文档 ID
            document_id="doc_001",

            # 模拟文档标题
            title="企业知识库说明文档",

            # 模拟文档内容
            content=(
                "RAG 是 Retrieval Augmented Generation，"
                "用于结合外部知识增强大模型回答。"
            ),

            # 模拟检索相似度分数
            score=0.89,

            # 额外元数据
            metadata={
                "source": "mock",
                "page": 1,
            },
        )
    ]


# 提示词
def build_prompt_messages_for_chat(request: ChatRequest) -> list[LLMMessage]:
    """
    根据聊天请求构造最终发送给大模型的消息列表。

    规则：
    1. 请求自带 system 消息：直接使用原始消息。
    2. 电商客服场景：使用电商客服 Prompt。
    3. 其他场景：使用通用聊天 Prompt。
    """

    # 判断用户请求中是否已经包含 system 消息
    has_system_message = any(
        message.role == MessageRole.SYSTEM
        for message in request.messages
    )

    # 如果调用方自己提供了 system 消息，
    # 则认为其已自定义模型行为，不再追加默认 Prompt。
    if has_system_message:
        return [
            LLMMessage(
                # 将请求消息的角色枚举转换为 LLMMessage 使用的角色枚举
                role=LLMRole(message.role.value),

                # 直接保留原始消息内容
                content=message.content,
            )
            for message in request.messages
        ]

    # 没有 system 消息时，取出最近一条用户消息作为待处理的问题
    latest_user_message = get_latest_user_message(request)

    # 如果指定了“跨境电商客服”场景，
    # 则使用电商客服专用 Prompt 模板。
    if request.prompt_scenario == PromptScenario.ECOMMERCE_CUSTOMER_SERVICE.value:
        return prompt_service.render_by_scenario(
            scenario=PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,
            variables={
                # 填充用户问题变量 {user_question}
                "user_question": latest_user_message,

                # 从 metadata 中获取业务规则；
                # 若未提供，使用默认提示文本
                "business_rules": request.metadata.get(
                    "business_rules",
                    "暂无额外业务规则。",
                ),

                # 从 metadata 中获取订单信息；
                # 若未提供，使用默认提示文本
                "order_info": request.metadata.get(
                    "order_info",
                    "用户未提供订单信息。",
                ),
            },
        )

    # 其他场景默认使用通用聊天 Prompt
    return prompt_service.render_by_scenario(
        scenario=PromptScenario.GENERAL_CHAT,
        variables={
            # 填充通用聊天 Prompt 中的 {user_question}
            "user_question": latest_user_message,
        },
    )