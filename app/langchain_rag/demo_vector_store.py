from app.langchain_rag.documents import load_markdown_documents
from app.langchain_rag.splitters import split_documents
from app.langchain_rag.vector_store import rebuild_vector_store


#   测试向量数据库的相似度搜索功能
def main():
    # 加载文档，并分割成文本块
    documents = load_markdown_documents()
    chunks = split_documents(documents)
    # 重建向量数据库，并返回新对象
    vector_store = rebuild_vector_store(chunks)

    query = "员工年假有几天？"
    #   执行相似度搜索，返回 3 个最相似的文档
    #   similarity_search 是 向量数据库的相似度搜索方法，把查询文本转换为向量，再与数据库中已保存的文档向量比较，找出语义上最接近的文档
    results = vector_store.similarity_search(
        query=query,
        k=3,
    )

    print("query:", query)
    print("=" * 80)

    for doc in results:
        print("metadata:", doc.metadata)
        print("content:")
        print(doc.page_content)
        print("=" * 80)


if __name__ == "__main__":
    main()