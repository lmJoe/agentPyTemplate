# 导入 asyncio，用于线程池调用和并发限制
import asyncio

# 导入 FastAPI 的路由器和依赖注入函数
from fastapi import APIRouter, Depends

# 导入 Pydantic 的数据模型基类和字段定义工具
from pydantic import BaseModel, Field

# 导入获取当前登录用户的依赖函数
from app.dependencies.auth import get_current_user

# 导入 RAG 回答数据模型、索引重建结果模型和 RAG 服务实例
from app.langchain_rag.service import (
    RAGAnswer,
    RebuildIndexResult,
    langchain_rag_service,
)

# 导入统一 API 响应模型
from app.schemas.response import ApiResponse

# 导入当前用户的数据模型
from app.schemas.user import CurrentUser


# 创建路由器，供应用注册这些 API 路由
router = APIRouter()

# 限制本进程内同时执行的 RAG 问答数量
# 同一时间最多 10 个请求进入问答服务，其他请求等待名额释放
RAG_ASK_CONCURRENCY_LIMIT = 10
rag_ask_semaphore = asyncio.Semaphore(RAG_ASK_CONCURRENCY_LIMIT)


# 定义“提问”接口的请求体结构
class RAGAskRequest(BaseModel):
    # 用户问题，必填且至少包含 1 个字符
    question: str = Field(..., min_length=1, description="用户问题")

    # 模型供应商，默认使用 DeepSeek
    provider: str = Field(default="deepseek", description="模型供应商")

    # 模型名称，默认使用 deepseek-chat
    model: str = Field(default="deepseek-chat", description="模型名称")

    # 检索文本块数量，默认为 4，范围限制为 1 到 10
    k: int = Field(default=4, ge=1, le=10, description="检索数量")


# 注册重建 RAG 向量索引的 POST 接口
@router.post(
    "/langchain/rag/rebuild-index",
    response_model=ApiResponse[RebuildIndexResult],
)
async def rebuild_rag_index(
    # 通过依赖注入获取当前用户；通常用于身份验证
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[RebuildIndexResult]:
    # 在线程池执行索引重建，避免同步操作阻塞事件循环
    result = await asyncio.to_thread(langchain_rag_service.rebuild_index)

    # 将重建结果放入统一 API 响应中返回
    return ApiResponse[RebuildIndexResult](
        data=result
    )


# 注册 RAG 问答的 POST 接口
@router.post(
    "/langchain/rag/ask",
    response_model=ApiResponse[RAGAnswer],
)
async def rag_ask(
    # 从请求体中解析问题、模型参数和检索数量
    request: RAGAskRequest,

    # 通过依赖注入获取当前用户；通常用于身份验证
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[RAGAnswer]:
    # 获取一个并发名额；如果当前已有 10 个问答在执行，则在这里等待
    async with rag_ask_semaphore:
        # 在线程池执行同步的 RAG 问答，避免阻塞事件循环
        result = await asyncio.to_thread(
            langchain_rag_service.ask,
            question=request.question,
            provider=request.provider,
            model_name=request.model,
            k=request.k,
        )

    # 将问答结果放入统一 API 响应中返回
    return ApiResponse[RAGAnswer](
        data=result
    )