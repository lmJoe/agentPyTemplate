from typing import Any  # 用于标注任意类型

from pydantic import BaseModel, Field  # 用于定义数据模型及字段默认值、说明

from app.core.exceptions import AppException, ErrorCode  # 导入应用统一异常类型和错误码
from app.core.logging import get_logger  # 导入日志记录器创建函数
from app.langchain_rag.chains import build_rag_chain  # 导入构建 RAG 问答链的函数
from app.langchain_rag.documents import load_markdown_documents  # 导入加载 Markdown 文档的函数
from app.langchain_rag.splitters import split_documents  # 导入文档切分函数
from app.langchain_rag.vector_store import rebuild_vector_store  # 导入重建向量库的函数


# 根据当前模块名称创建日志记录器
logger = get_logger(__name__)

#   把前面实现的 RAG 功能封装成一个应用服务层，提供两个主要操作：
#   rebuild_index()：加载 Markdown 文档、将文档切分成文本块，并重建向量索引。返回文档数和文本块数。
#   ask()：根据用户问题构建并运行 RAG 链，把链返回的答案和来源转换成 Pydantic 数据模型 RAGAnswer，方便应用统一处理或序列化。



# 定义单条检索来源的数据结构
class RAGSource(BaseModel):
    # 来源文档的 ID；没有值时默认为 None
    document_id: str | None = Field(default=None)

    # 文档文本块的 ID；没有值时默认为 None
    chunk_id: str | None = Field(default=None)

    # 文档来源，例如文件路径；没有值时默认为 None
    source: str | None = Field(default=None)

    # 文本块内容预览；没有值时默认为空字符串
    content_preview: str = Field(default="")


# 定义一次 RAG 问答结果的数据结构
class RAGAnswer(BaseModel):
    # 模型生成的回答；必填字段
    answer: str = Field(..., description="RAG 回答")

    # 检索到的来源列表；默认是空列表
    sources: list[RAGSource] = Field(
        default_factory=list,
        description="引用来源",
    )

    # 问答的扩展信息，例如模型名称和来源数量；默认是空字典
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="扩展信息",
    )


# 定义索引重建结果的数据结构
class RebuildIndexResult(BaseModel):
    # 加载的文档数量
    document_count: int = Field(..., description="文档数量")

    # 切分后的文本块数量
    chunk_count: int = Field(..., description="文本块数量")


# 封装 LangChain RAG 的索引重建和问答功能
class LangChainRAGService:

    # 加载文档、切分文档并重建向量索引
    def rebuild_index(self) -> RebuildIndexResult:
        try:
            # 从配置的位置加载 Markdown 文档
            documents = load_markdown_documents()

            # 将文档拆分成较小的文本块
            chunks = split_documents(documents)

            # 用这些文本块重建向量存储，供 Retriever 后续检索
            rebuild_vector_store(chunks)

        except Exception as exc:
            # 记录异常详情和堆栈信息
            logger.exception("langchain_rag_rebuild_index_failed")

            # 将底层异常包装成应用统一异常，并保留原始异常作为原因
            raise AppException(
                message="RAG 索引重建失败",
                code=ErrorCode.RAG_QUERY_FAILED,
                status_code=500,
                data={
                    "error": repr(exc),  # 保存原始异常的描述
                },
            ) from exc

        # 返回处理的文档数量和文本块数量
        return RebuildIndexResult(
            document_count=len(documents),
            chunk_count=len(chunks),
        )

    # 使用 RAG 链回答问题，并将结果整理为 RAGAnswer
    def ask(
        self,
        question: str,  # 用户提出的问题
        provider: str = "deepseek",  # 模型服务商，默认使用 DeepSeek
        model_name: str = "deepseek-chat",  # 模型名称
        k: int = 4,  # Retriever 最多检索的文本块数量
    ) -> RAGAnswer:
        # 记录本次问答开始的信息
        logger.info(
            f"langchain_rag_ask_start model={model_name} k={k}"
        )

        try:
            # 按指定模型参数和检索数量构建 RAG 链
            chain = build_rag_chain(
                provider=provider,
                model_name=model_name,
                k=k,
            )

            # 执行问答链，输入用户问题
            # 返回结果通常包含 answer 和 sources
            result = chain.invoke({
                "question": question,
            })

        except Exception as exc:
            # 记录异常详情和堆栈信息
            logger.exception("langchain_rag_ask_failed")

            # 将底层异常包装成应用统一异常，并保留原始异常作为原因
            raise AppException(
                message="LangChain RAG 问答失败",
                code=ErrorCode.LLM_CALL_FAILED,
                status_code=500,
                data={
                    "error": repr(exc),  # 保存原始异常的描述
                    "provider": provider,  # 记录使用的模型服务商
                    "model": model_name,  # 记录使用的模型名称
                },
            ) from exc

        # 将链返回的来源字典转换为 RAGSource 对象
        sources = [
            RAGSource(**item)
            for item in result.get("sources", [])
        ]

        # 将答案、来源和调用信息整理成 RAGAnswer 并返回
        return RAGAnswer(
            answer=result["answer"],
            sources=sources,
            metadata={
                "provider": provider,
                "model": model_name,
                "k": k,
                "source_count": len(sources),
            },
        )


# 创建服务实例，供应用的其他模块调用
langchain_rag_service = LangChainRAGService()