from pathlib import Path

from app.core.logging import get_logger
from app.langchain_rag.service import langchain_rag_service
from app.langchain_rag.vector_store import CHROMA_DIR


logger = get_logger(__name__)


def ensure_rag_index() -> dict:
    """
    确保本地 RAG 索引存在。

    教学版逻辑：
    1. 如果 Chroma 目录不存在，就 rebuild。
    2. 如果已经存在，就跳过。
    3. 生产环境应该使用文档版本、索引版本和任务状态判断。
    """
    if not Path(CHROMA_DIR).exists():
        logger.info("rag_index_missing_rebuild_start")

        # 重新构建索引 使用rebuild_index重建索引，更新索引版本
        result = langchain_rag_service.rebuild_index()
        logger.info(f"rag_index_rebuild_success result={result}")

        # 返回重建结果，包含文档数量和文本块数量
        return {
            "rebuilt": True,
            **result,
        }

    # 如果索引已存在，返回索引版本
    return {
        "rebuilt": False,
        "message": "RAG 索引已存在",
    }