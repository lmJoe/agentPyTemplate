import json  # 用于将问答结果转换成 JSON 字符串

# 导入 LangChain 的结构化工具类型
from langchain_core.tools import StructuredTool

# 导入 Pydantic 数据模型和字段定义工具
from pydantic import BaseModel, Field

# 导入封装好的 RAG 知识库问答服务实例
from app.langchain_rag.service import langchain_rag_service


# 定义知识库搜索工具的输入参数结构
class SearchKnowledgeBaseArgs(BaseModel):
    # query 是必填字符串，至少包含 1 个字符
    query: str = Field(
        ...,
        min_length=1,
        description="用户问题或检索关键词",
    )


# 定义异步知识库搜索函数，供 LangChain 工具调用
async def search_knowledge_base(query: str) -> str:
    """
    搜索企业知识库，并返回基于知识库的回答和引用来源。
    """
    # 调用 RAG 服务，根据 query 检索知识库并生成回答
    result = langchain_rag_service.ask(
        question=query,
        provider="deepseek",
        model_name="deepseek-chat",
        k=4,  # 最多检索 4 个相关文本块
    )

    # 将 Pydantic 结果转换成字典，再序列化为 JSON 字符串
    # ensure_ascii=False 可保留中文字符
    return json.dumps(
        result.model_dump(),
        ensure_ascii=False,
    )


# 将函数包装成 LangChain 可调用的结构化工具
# StructuredTool.from_function() 是 LangChain 提供的类方法，用于把普通 Python 函数包装成一个 LangChain 工具，并描述工具的名称、用途和输入参数。
search_knowledge_base_tool = StructuredTool.from_function(
    coroutine=search_knowledge_base,  # 指定异步工具执行函数
    name="search_knowledge_base",  # 工具名称，模型可据此选择工具
    description=(  # 工具说明，帮助模型判断何时调用以及如何使用结果
        "搜索企业知识库。当用户询问公司制度、售后规则、课程阶段、内部文档内容时使用。"
        "如果知识库没有相关内容，应说明无法从知识库确认，不要编造。"
    ),
    args_schema=SearchKnowledgeBaseArgs,  # 指定工具参数的校验结构
)