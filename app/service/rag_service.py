import uuid
from app.schemas.chat import TokenUsage
from app.schemas.rag import RAGQueryRequest,RAGQueryResponse
from app.repositories.knowledge_repository import knowledge_repository

# 异常日志捕捉
from app.core.exceptions import AppException, ErrorCode
from app.core.logging import get_logger

# 为当前这个聊天业务文件获取一个专用的日志对象，后面可以通过它记录聊天处理过程
logger = get_logger(__name__)


async def query_rag(request:RAGQueryRequest) -> RAGQueryResponse:

  # 这个方法执行之前增加
  logger.info(f"query_rag knowledge_base_id={request.knowledge_base_id},top_k={request.top_k}")

  # 通过 knowledge_repository.search_documents()获取检索结果
  sources = await knowledge_repository.search_documents(
    question=request.question,
    knowledge_base_id=request.knowledge_base_id,
    top_k=request.top_k,
    metadata_filter=request.metadata_filter
  )
  answer = f"根据知识库{request.knowledge_base_id} 的内容，RAG 是检索增强生成。"

  logger.info(f"query_rag_success knowledge_base_id={request.knowledge_base_id},source_count={len(answer)}")

  return RAGQueryResponse(
    answer = answer,
    knowledge_base_id=request.knowledge_base_id,
    sources=sources,
    usage=TokenUsage(
      prompt_tokens=len(request.question),
      completion_tokens=len(answer),
      total_tokens=len(request.question) + len(answer)
    ),
    trace_id = f"trace_{uuid.uuid4().hex[:8]}"
  )