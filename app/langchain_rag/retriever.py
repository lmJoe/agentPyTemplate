# 从 LangChain 导入文档类型，用于表示检索到的文档
from langchain_core.documents import Document

# 导入检索器基类，用于标注检索器的返回类型
from langchain_core.retrievers import BaseRetriever

# 导入创建向量存储的函数
from app.langchain_rag.vector_store import create_vector_store


# 定义创建检索器的函数，k 表示每次检索返回的文档数量，默认是 4
def create_retriever(
    k: int = 4,
) -> BaseRetriever:
    # 创建向量存储对象
    vector_store = create_vector_store()

    # 将向量存储转换为 Retriever，并设置检索参数
    return vector_store.as_retriever(
        search_kwargs={
            # 设置最多检索 k 个相关文档
            "k": k,
        }
    )


# 定义检索文档的函数，接收查询文本和文档数量，返回文档列表
def retrieve_documents(
    query: str,
    k: int = 4,
) -> list[Document]:
    # 创建 Retriever，并传入要返回的文档数量
    retriever = create_retriever(k=k)

    # 把查询文本传给 Retriever，执行检索并返回相关文档
    return retriever.invoke(query)