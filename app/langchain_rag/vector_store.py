from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from app.langchain_rag.embeddings import create_embeddings

#   定义向量数据库的目录和集合名称
CHROMA_DIR = Path("data/chroma_langchain_rag")
COLLECTION_NAME = "ai_agnet_course_kb"


#   创建向量数据库
def create_vector_store() -> Chroma:
    #   创建 Embeddings 对象
    embeddings = create_embeddings()
    #   创建 Chroma 对象，并返回
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

# 定义一个重建向量数据库的函数
def rebuild_vector_store(
    chunks: list[Document],  # 接收文档切分后的文本块列表
) -> Chroma:  # 声明函数返回一个 Chroma 向量数据库对象

    # 检查向量数据库目录是否已经存在
    if CHROMA_DIR.exists():
        # 导入 shutil 模块，用于文件和目录操作
        import shutil

        # 删除整个向量数据库目录及其中的所有文件
        shutil.rmtree(CHROMA_DIR)

    # 创建一个新的向量数据库对象
    vector_store = create_vector_store()

    # 为每个文本块生成一个 ID
    ids = [
        # 优先使用文本块元数据中的 chunk_id；
        # 如果没有，则使用 chunk_加上文本块在列表中的序号
        chunk.metadata.get("chunk_id", f"chunk_{index}")
        # 遍历 chunks，同时获取每个文本块及其序号
        for index, chunk in enumerate(chunks)
    ]

    # 将文本块和对应的 ID 添加到向量数据库中
    vector_store.add_documents(
        documents=chunks,  # 要写入向量数据库的文档列表
        ids=ids,  # 每个文档对应的 ID 列表
    )

    # 返回已写入文档的新向量数据库对象
    return vector_store


# 定义相似度搜索函数，接收查询文本和返回结果数量
def similarity_search(
    query: str,  # 要在向量数据库中搜索的文本
    k: int = 4,  # 最多返回 4 个最相似的文档，可由调用者指定
) -> list[Document]:  # 声明返回值是 Document 对象组成的列表

    # 创建或连接到向量数据库
    vector_store = create_vector_store()

    # 在向量数据库中搜索与 query 最相似的文档
    return vector_store.similarity_search(
        query=query,  # 用 query 作为搜索内容
        k=k,  # 指定返回的相似文档数量
    )