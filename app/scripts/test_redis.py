# 导入 asyncio，用于运行异步 main 函数
import asyncio

# 导入全局异步 Redis 客户端和关闭连接的方法
from app.redis.client import redis_client, close_redis


# 用于测试 Redis 是否可连接、写入带过期时间的数据、读取数据，并查看剩余过期时间


async def main():
    try:
        # 测试 Redis 连接。
        # 成功时 pong 的值为 True。
        pong = await redis_client.ping()
        print("PING:", pong)

        # 写入一个键值对：
        # key   = "course:name"
        # value = "AI Agent全栈开发"
        # ex=60 表示 60 秒后自动过期并删除。
        await redis_client.set(
            "course:name",
            "AI Agent全栈开发",
            ex=60,
        )

        # 读取刚刚写入的数据。
        # 因为客户端设置了 decode_responses=True，返回的是 str。
        value = await redis_client.get("course:name")
        print("course:name:", value)

        # 查看此键剩余的过期秒数。
        ttl = await redis_client.ttl("course:name")
        print("ttl:", ttl)

    finally:
        # 无论中间是否报错，最后都关闭 Redis 连接池。
        await close_redis()


# 启动异步程序
asyncio.run(main())