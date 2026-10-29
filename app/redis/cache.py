# 用于把 Python 列表/字典转换成 JSON 字符串
import json
import hashlib
# Redis 异步客户端类型，仅用于类型标注
from redis.asyncio import Redis

# 项目配置，包含默认 Redis 缓存过期时间
from app.core.config import settings

# 生成“会话最近消息”对应的 Redis Key
from app.redis.keys import conversation_recent_messages_key

# 聊天消息的数据模型
from app.schemas.chat import ChatMessage, MessageRole

from app.redis.keys import chat_response_cache_key


async def cache_recent_messages(
    redis: Redis,
    conversation_id: str,
    messages: list[ChatMessage],
    ttl_seconds: int | None = None,
):
    # 生成 Redis Key。
    # 示例：conversation:c_ab12cd34:recent_messages
    key = conversation_recent_messages_key(conversation_id)

    # 将 Pydantic ChatMessage 对象转换为可 JSON 序列化的字典列表。
    data = [
        {
            # 如果 role 是枚举，使用 .value 才最安全。
            # 例如 MessageRole.USER -> "user"
            "role": message.role.value,
            "content": message.content,
        }
        for message in messages
    ]

    # 将消息列表写入 Redis。
    # ensure_ascii=False：中文会直接保存，不会变成 \uXXXX。
    # ex：过期秒数；未传 ttl_seconds 时使用项目默认 TTL。
    await redis.set(
        key,
        json.dumps(data, ensure_ascii=False),
        ex=ttl_seconds or settings.redis_default_ttl_seconds,
    )


# 运行后大致为
# Key:
# conversation:c_ab12cd34:recent_messages

# Value:
# [{"role":"user","content":"你好"},{"role":"assistant","content":"你好，有什么可以帮你？"}]


# 获取最近的几条redis消息
async def get_cached_recent_messages(
    redis: Redis,
    conversation_id: str,
) -> list[ChatMessage] | None:
    # 根据会话 ID 生成缓存 Key
    key = conversation_recent_messages_key(conversation_id)

    # 从 Redis 读取缓存值。
    # 因为 Redis 客户端设置了 decode_responses=True，
    # value 是 str，而不是 bytes。
    value = await redis.get(key)

    # Key 不存在、已过期时，redis.get() 返回 None。
    # 返回 None 表示“缓存未命中”。
    if not value:
        return None

    # 将 JSON 字符串还原为 Python 列表。
    data = json.loads(value)

    # 将字典列表还原为 ChatMessage 模型列表。
    return [
        ChatMessage(
            # 将 "user" / "assistant" 等字符串还原为 MessageRole 枚举
            role=MessageRole(item["role"]),
            content=item["content"],
        )
        for item in data
    ]


# 例如 Redis 中存的是
# [
#   {"role": "user", "content": "你好"},
#   {"role": "assistant", "content": "你好，有什么可以帮你？"}
# ]
# 返回后会变成：
# [
#     ChatMessage(role=MessageRole.USER, content="你好"),
#     ChatMessage(role=MessageRole.ASSISTANT, content="你好，有什么可以帮你？"),
# ]


# 生成hash,此处用于上下文中重复问题
def hash_text(text:str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

async def get_cached_chat_response(
        redis:Redis,
        question:str
) -> str | None:
    key = chat_response_cache_key(hash_text(question))
    return await redis.get(key)

async def cache_chat_response(
        redis:Redis,
        question:str,
        answer:str,
        ttl_seconds:int =300
):
    key = chat_response_cache_key(hash_text(question))
    await redis.set(key,answer,ex=ttl_seconds)
