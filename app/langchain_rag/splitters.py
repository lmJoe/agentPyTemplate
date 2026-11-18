from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 文本分割器，用于将文档内容分割成多个段落

# 创建默认的文本分割器
def create_default_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=[
            "\n## ",
            "\n# ",
            "\n\n",
            "\n",
            "。",
            "，",
            " ",
            "",
        ],
    )

#   将文档分割成多个段落，并为每个段落生成新的元数据信息
def split_documents(
    documents: list[Document],
) -> list[Document]:
    # 创建默认的文本分割器
    splitter = create_default_text_splitter()
    # 使用默认的文本分割器将文档分割成多个段落
    chunks = splitter.split_documents(documents)

    # 为每个段落生成新的元数据信息
    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,
            "chunk_id": f"{chunk.metadata.get('document_id', 'doc')}_chunk_{index}",
            "chunk_index": index,
        }

    return chunks


#   格式化文档列表，包括元数据和内容预览
def format_docs(docs: list[Document]) -> str:
    lines = []

    # 遍历每个文档，并生成格式化的字符串
    for index, doc in enumerate(docs, start=1):
        document_id = doc.metadata.get("document_id", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        source = doc.metadata.get("source", "unknown")

        lines.append(
            f"[{index}] document_id={document_id}, chunk_id={chunk_id}, source={source}\n"
            f"{doc.page_content}"
        )

    return "\n\n".join(lines)