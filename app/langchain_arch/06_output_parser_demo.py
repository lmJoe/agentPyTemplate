from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings

# 演示 LangChain OutputParser 的作用 输出解析器

def create_model():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
    )

def main():
    # 创建一个输出解析器，指定输出类型为字符串
    parser = StrOutputParser()

    # 创建一个聊天提示模板，包含系统消息和用户消息
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是一个专业 AI Agent 课程助教。",
        ),
        (
            "human",
            "请用一句话解释：{topic}",
        ),
    ])

    model = create_model()

    # 把前prompt组件的输出作为后model组件的输入，形成一个简单的链式调用。 管道组合写法
    chain = prompt | model | parser

    response = chain.invoke({
        "topic": "LangChain 的价值",
    })

    print("response class:", response.__class__.__name__)
    print("content:")
    print(response)

if __name__ == "__main__":
    main()  