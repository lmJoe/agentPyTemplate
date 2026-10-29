from fastapi import APIRouter, Depends
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.conversations import router as conversation_router
from app.api.v1.rag import router as rag_router
from app.api.v1.models import router as models_router
from app.api.v1.agents import router as agents_router
from app.dependencies.auth import verfy_api_key

from app.core.constants import ApiTag

# 统一聚合 v1 版本下所有 router
# main.py 只需要注册一次： app.include_router(api_router, prefix=settings.api_v1_prefix)
# main.py 更干净
# v1 路由集中管理
# 方便以后新增 v2
# 模块边界更清楚


api_router = APIRouter()

# dependencies=[Depends(verfy_api_key)] 给 chat_router 中的所有接口统一添加“验证 API Key”的前置依赖
api_router.include_router(chat_router, tags=[ApiTag.CHAT], dependencies=[Depends(verfy_api_key)])
api_router.include_router(health_router, tags=[ApiTag.HEALTH])
api_router.include_router(conversation_router, tags=[ApiTag.CONVERSATIONS], dependencies=[Depends(verfy_api_key)])
api_router.include_router(rag_router, tags=[ApiTag.RAG], dependencies=[Depends(verfy_api_key)])
api_router.include_router(models_router, tags=[ApiTag.MODELS])
api_router.include_router(agents_router, tags=[ApiTag.AGENTS],dependencies=[Depends(verfy_api_key)])