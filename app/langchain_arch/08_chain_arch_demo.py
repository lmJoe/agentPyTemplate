from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from langchain_openai import ChatOpenAI

from app.core.config import settings

def create_model():
  return ChatOpenAI(
    model_name="deepseek-chat",
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    temperature=0.7,
  )

# 这里可以添加业务逻辑处理 （添加前缀，格式转换，字段的提取等等）
def add_prefix(text: str) -> str:
  return f"Langchain 架构解释: {text}"

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
  chain = prompt | model | RunnableLambda(add_prefix) | parser

  response = chain.invoke({
      "topic": "LangChain 的价值",
  })

  print(response)

if __name__ == "__main__":
  main()