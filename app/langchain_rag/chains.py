# 导入 Any，用于标注字典中值的类型不固定
from typing import Any

# 导入字符串输出解析器：将模型输出解析为普通字符串
from langchain_core.output_parsers import StrOutputParser

# 导入 RunnableLambda：将普通 Python 函数包装成 LangChain Runnable
from langchain_core.runnables import RunnableLambda

# 导入模型工厂，用于根据 provider 和 model_name 创建聊天模型
from app.langchain_models.model_factory import LangChainModelFactory

# 导入 RAG 提示模板，模板中会使用问题和检索到的上下文
from app.langchain_rag.prompts import RAG_PROMPT

# 导入创建 Retriever 的函数
from app.langchain_rag.retriever import create_retriever

# 导入文档格式化函数，用于将检索到的文档整理成上下文文本
from app.langchain_rag.splitters import format_docs


# 构建 RAG 链 用于构建一个 RAG 问答链：用户提出问题后，系统先从向量库中检索相关文档，再把问题和文档内容交给大语言模型生成答案，最后一并返回答案和来源信息。
# provider：模型服务商，默认使用 deepseek
# model_name：模型名称，默认使用 deepseek-chat
# k：每次检索返回的相关文档数量，默认是 4
def build_rag_chain(
    provider: str = "deepseek",
    model_name: str = "deepseek-chat",
    k: int = 4,
):
    # 创建 Retriever，用于根据问题从向量库中检索最多 k 个相关文档
    retriever = create_retriever(k=k)

    # 使用模型工厂创建聊天模型
    # temperature=0 表示降低随机性，让回答更稳定
    model = LangChainModelFactory.create(
        provider=provider,
        model=model_name,
        temperature=0,
    )

    # 创建输出解析器，将模型结果转换成字符串
    parser = StrOutputParser()

    # 定义检索上下文的函数
    # 输入是包含 question 的字典；输出包含问题、格式化后的上下文和原始文档
    def retrieve_context(inputs: dict[str, Any]) -> dict[str, Any]:
        # 从输入字典中取出用户问题
        question = inputs["question"]

        # 根据问题检索相关文档
        docs = retriever.invoke(question)

        # 返回后续链需要的数据
        return {
            "question": question,          # 保留原始问题
            "context": format_docs(docs),  # 将检索结果整理成提示词所需的上下文
            "docs": docs,                  # 保留原始文档，供后续提取来源信息
        }

    # 定义附加来源信息的函数
    # 当前实现只是原样返回输入，没有额外处理
    def attach_sources(answer_inputs: dict[str, Any]) -> dict[str, Any]:
        return answer_inputs

    # 将检索函数包装成 LangChain Runnable，以便加入链式流程
    retrieve_runnable = RunnableLambda(retrieve_context)

    # 组合提示模板、模型和输出解析器，形成回答链
    answer_chain = RAG_PROMPT | model | parser

    # 定义生成答案并整理来源信息的函数
    def run_answer(inputs: dict[str, Any]) -> dict[str, Any]:
        # 将问题和检索到的上下文传给回答链，生成答案
        answer = answer_chain.invoke({
            "question": inputs["question"],
            "context": inputs["context"],
        })

        # 初始化来源列表
        sources = []

        # 遍历检索到的原始文档，提取来源元数据
        for doc in inputs["docs"]:
            sources.append({
                # 获取文档 ID；若元数据中不存在则返回 None
                "document_id": doc.metadata.get("document_id"),

                # 获取文本块 ID；若元数据中不存在则返回 None
                "chunk_id": doc.metadata.get("chunk_id"),

                # 获取来源信息，例如文件名或路径；若不存在则返回 None
                "source": doc.metadata.get("source"),

                # 取文档内容的前 160 个字符作为预览
                "content_preview": doc.page_content[:160],
            })

        # 返回模型答案和对应的来源列表
        return {
            "answer": answer,
            "sources": sources,
        }

    # 先执行检索上下文，再生成答案并整理来源
    # 返回的 Runnable 接收包含 question 的输入，并输出 answer 和 sources
    return retrieve_runnable | RunnableLambda(run_answer)