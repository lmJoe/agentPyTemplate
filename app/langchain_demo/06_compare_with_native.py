from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.llm.providers.deepseek import DeepSeekProvider
from app.llm.schemas import LLMMessage, LLMRequest, LLMRole


# 原生写法和langchain框架写法对比（真实项目里可以混用）
# 原生写法更底层，控制力强。
# 如
# 业务 API、权限、数据库、缓存
# 继续用我们自己的 FastAPI 架构


# LangChain 写法更简洁，更适合组合 
# 如
# LLM 编排、Prompt 组合、RAG、Agent
# 逐步使用 LangChain / LangGraph




# 原生写法
async def native_version():
    provider = DeepSeekProvider()

    request = LLMRequest(
        model="deepseek-chat",
        messages=[
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="你是一个专业 AI Agent 课程助教。",
            ),
            LLMMessage(
                role=LLMRole.USER,
                content="请用一句话解释 LangChain。",
            ),
        ],
        temperature=0.7,
    )

    response = await provider.chat(request)

    return response.content


# langchain框架写法
def langchain_version():
    model = ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业 AI Agent 课程助教。"),
        ("human", "请用一句话解释 {topic}。"),
    ])

    chain = prompt | model

    response = chain.invoke({
        "topic": "LangChain",
    })

    return response.content