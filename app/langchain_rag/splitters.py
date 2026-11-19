from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 创建递归字符文本分割器
def create_default_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=500,       # 每个文本块的目标最大长度，按字符计算
        chunk_overlap=80,     # 相邻文本块之间保留的重叠字符数
        separators=[          # 按优先级尝试这些分隔符，尽量在自然边界处分割
            "\n## ",          # 二级标题
            "\n# ",           # 一级标题
            "\n\n",           # 空行，通常表示段落边界
            "\n",             # 换行
            "。",             # 中文句号
            "，",             # 中文逗号
            " ",              # 空格
            "",               # 前面的分隔符都不适用时，逐字符分割
        ],
    )


# 将文档拆分为文本块，并为每个文本块补充编号元数据
def split_documents(
    documents: list[Document],
) -> list[Document]:
    # 创建文本分割器
    splitter = create_default_text_splitter()

    # 分割文档；每个文本块会继承原文档的元数据
    chunks = splitter.split_documents(documents)

    # 为每个文本块添加 chunk_id 和 chunk_index
    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,  # 保留继承来的元数据，例如 document_id 和 source
            # 根据 document_id 和当前结果列表中的序号生成文本块 ID
            "chunk_id": f"{chunk.metadata.get('document_id', 'doc')}_chunk_{index}",
            # 记录该文本块在本次分割结果中的序号，从 0 开始
            "chunk_index": index,
        }

    # 返回拆分后的文本块列表
    return chunks


# 将文档列表整理成带有来源信息的文本，供后续提示词使用
def format_docs(docs: list[Document]) -> str:
    lines = []

    # 按检索结果的顺序处理文档，编号从 1 开始
    for index, doc in enumerate(docs, start=1):
        # 从元数据中读取来源信息；对应字段不存在时使用 "unknown"
        document_id = doc.metadata.get("document_id", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        source = doc.metadata.get("source", "unknown")

        # 将元数据和文本块内容组合成一段字符串
        lines.append(
            f"[{index}] document_id={document_id}, chunk_id={chunk_id}, source={source}\n"
            f"{doc.page_content}"
        )

    # 用空行分隔各个文本块，返回一个完整的上下文字符串
    return "\n\n".join(lines)