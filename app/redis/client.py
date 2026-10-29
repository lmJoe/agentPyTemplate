# 导入 redis-py 提供的异步 Redis 客户端模块
import redis.asyncio as redis

# 导入项目配置；其中包含 redis_url，例如：
# redis://default:redis123@127.0.0.1:6379/0
from app.core.config import settings

# 创建了全局异步 Redis 客户端，供 FastAPI 的其他模块复用


# 根据配置中的 Redis URL 创建异步客户端。
# 此时通常不会立刻建立连接，而是在第一次执行 Redis 命令时连接。
redis_client = redis.from_url(
    settings.redis_url,

    # 读取 Redis 字符串时使用 UTF-8 编码
    encoding="utf-8",

    # True：Redis 返回 Python 字符串 str；
    # False：Redis 返回字节数据 bytes。
    # 项目处理文本、JSON 时通常建议设为 True。
    decode_responses=True,
)


# 在应用关闭时关闭 Redis 客户端及其连接池，
# 防止连接资源残留。
async def close_redis():
    await redis_client.aclose()