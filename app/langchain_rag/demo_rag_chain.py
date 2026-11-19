import json  # 用于将结果转换为格式化的 JSON 字符串

# 导入构建 RAG 问答链的函数
from app.langchain_rag.chains import build_rag_chain

# 导入加载 Markdown 文档的函数
from app.langchain_rag.documents import load_markdown_documents

# 导入将文档拆分为文本块的函数
from app.langchain_rag.splitters import split_documents

# 导入重建向量存储的函数
from app.langchain_rag.vector_store import rebuild_vector_store


#一个 RAG 流程的运行入口。它先加载 Markdown 文档，将文档切分成文本块，再用这些文本块重建向量库。随后创建 RAG 问答链，针对“员工入职满一年后年假有几天？”检索最多 3 个相关文本块并生成回答，最后以格式化的 JSON 输出答案和来源信息

# 程序入口函数：加载文档、建立向量库并执行一次 RAG 问答
def main():
    # 从指定位置加载 Markdown 文档
    documents = load_markdown_documents()

    # 将文档拆分为较小的文本块，供向量化和检索使用
    chunks = split_documents(documents)

    # 根据文本块重新构建向量存储,为了让刚加载并切分好的 Markdown 文档能被后面的 RAG 问答检索到
    rebuild_vector_store(chunks)

    # 创建 RAG 问答链
    # 使用 DeepSeek 的 deepseek-chat 模型，每次检索 3 个相关文本块
    chain = build_rag_chain(
        provider="deepseek",
        model_name="deepseek-chat",
        k=3,
    )

    # 调用 RAG 链，传入用户问题
    # 链会检索相关文本块，并将问题和上下文交给模型生成答案
    result = chain.invoke({
        "question": "员工入职满一年后年假有几天？"
    })

    # 将问答结果转换成易读的 JSON 字符串并打印
    # ensure_ascii=False 用于保留中文字符
    # indent=2 用于设置缩进，让输出更易阅读
    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    ))


# 只有直接运行此文件时才执行 main()
# 如果该文件被其他模块导入，则不会自动运行
if __name__ == "__main__":
    main()