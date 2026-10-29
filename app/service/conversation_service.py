# 导入 uuid，用于生成唯一的会话 ID
import uuid
# 导入创建会话请求模型、会话响应模型和会话消息响应模型
from app.schemas.conversation import ConversationCreateRequest, ConversationMessagesResponse, ConversationResponse

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.conversation_repository import conversation_repository
from app.redis.cache import (
    get_cached_recent_messages,
    cache_recent_messages
)
from redis.asyncio import Redis

# “会话业务层”（service）：它调用仓库层读写数据库，再把数据库模型转换为接口返回的数据格式
async def create_conversation(
        request: ConversationCreateRequest,
        db:AsyncSession,
        user_id:str | None=None
) -> ConversationResponse:

    # 调用仓库层，向数据库创建一条 Conversation 记录。
    conversation = await conversation_repository.create(
        request,
        db,
        user_id
    )

    # 把数据库中的会话对象包装为接口响应模型，返回给前端/API 调用方
    return ConversationResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

# 根据会话 ID 查询该会话的全部消息；
# 实现缓存优先，数据库兜底（模式常叫 Cache-Aside（旁路缓存）
# 整体流程就是：
# 请求消息
#   ↓
# 先查 Redis
#   ↓
# 命中 → 直接返回
# 未命中 → 查 PostgreSQL
#   ↓
# 将最近 10 条写入 Redis
#   ↓
# 返回查询结果
async def get_conversation(
        db:AsyncSession,
        conversation_id: str ,
        redis:Redis | None = None
) -> ConversationMessagesResponse:
    
    # 这里先查redis，命中则返回（如果没有的话肯定就是第一次，那么第一次就直接先调用数据库，如果有的话就走redis取）
    if redis:
        cached_messages = await get_cached_recent_messages(redis,conversation_id)
        if cached_messages is not None:
            return ConversationMessagesResponse(
                conversation_id=conversation_id,
                messages=cached_messages
            )
    # 从数据库查询该会话下的全部消息，再包装成：
    # ConversationMessagesResponse(
    #     conversation_id=conversation_id,
    #     messages=messages
    # )

    messages = await conversation_repository.get_messages(
        db=db,
        conversation_id=conversation_id
    )

    # 从数据库拿到之后，就存入redis中
    if redis:
        await cache_recent_messages(
            redis=redis,
            conversation_id=conversation_id,
            messages=messages[-10:]   # 只缓存最近10条数据
        )

    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=messages
    )
