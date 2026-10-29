from fastapi import FastAPI, Query
from app.api.v1.api import api_router as chat_router
from app.core.config import settings
from app.core.middleware import register_middleware
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from contextlib import asynccontextmanager
from app.redis.client import close_redis,redis_client


# 使用asynccontextmanager 把一个异步函数变成异步的上下文管理器
@asynccontextmanager
async def lifespan(app:FastAPI):
    await redis_client.ping()  # 启动时检查 Redis
    print("redis应用启动")
    # yield 前：应用启动阶段
    yield
    # yield 后：应用关闭阶段
    print("redis应用关闭")
    await close_redis()


# 创建 app
# 注册 api_router
# 定义根路由

def create_app() -> FastAPI:

    # 初始化日志配置
    setup_logging()

    app = FastAPI(
        title=settings.app_name,
        description="FastAPI frameword, high performance, easy to learn, fast to code, read...",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan    # 应用关闭时，关闭 Redis 客户端和连接池
    )

    # 注册日志中间件（启动之后，每次请求都会经过这个日志中间件）
    register_middleware(app)
    # 注册异常处理
    register_exception_handlers(app)

    # 进行api版本管理
    app.include_router(chat_router,prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root():
        return {
            "message": settings.app_name,
            "version": settings.app_version,
            "env":settings.app_env
        }

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {
            "id": user_id,
            "name": f"User {user_id}"
        }

    @app.get("/search")
    async def search(
        q: str = Query(...,min_length=1,max_length=100,description="查询内容，必填"), 
        page: int = Query(default=1,ge=1,description="页码"), 
        size: int = Query(default=10,ge=1,len=100,description="一页的数量")
    ):
        return {
            "q": q,
            "page": page,
            "size": size
        }


    return app

app = create_app()

