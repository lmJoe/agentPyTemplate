from app.langchain_rag.documents import load_markdown_documents
from app.langchain_rag.splitters import split_documents

#   加载文档并分割为段落，然后打印相关信息
def main():
    documents = load_markdown_documents()
    chunks = split_documents(documents)

    print("documents count:", len(documents))
    print("chunks count:", len(chunks))
    print("=" * 80)

    for chunk in chunks:
        print("metadata:", chunk.metadata)
        print("content:")
        print(chunk.page_content[:300])
        print("=" * 80)


if __name__ == "__main__":
    main()