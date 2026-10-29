from fastapi import APIRouter, HTTPException, Depends
from app.core.config import Settings
from app.dependencies.settings import get_app_settings
from redis.asyncio import Redis
from app.dependencies.redis import get_redis_client

router = APIRouter()


async def get_request_source() -> str:
    return "我有一个请求源"

# @router.get("/health")
# async def health(source:str = Depends(get_request_source)):
#     return {
#         "status":"ok", 
#         "version":settings.app_version,
#         "service":settings.app_name,
#         "env":settings.app_env,
#         "source":source
#     }


# 依赖注入的核心目的不是“让接口参数变多”，而是把通用逻辑——如读取配置、身份认证、获取请求来源、数据库连接、权限校验——从接口函数中抽离，接口函数只关注自己的业务响应
# settings: Settings = Depends(get_app_settings), 读取的通常是 .env / 环境变量中的配置
# source:str = Depends(get_request_source) 请求头等请求上下文 → 来源字符串
@router.get("/health")
async def health(settings:Settings = Depends(get_app_settings), source:str = Depends(get_request_source)):
    return {
        "status":"ok", 
        "version":settings.app_version,
        "service":settings.app_name,
        "env":settings.app_env,
        "source":source
    }


@router.get("/health/redis")
async def redis_health(
    redis:Redis = Depends(get_redis_client) 
):
    pong = await redis.ping()
    return {
        "status":"ok" if pong else "error",
        "pong":pong
    }
