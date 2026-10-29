from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory


# 演示 LangChain ChatModel 的作用
def main():
  model = LangChainModelFactory.create(
    provider="deepseek",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2048,
  )

  messages = [
    SystemMessage(content="你是一个专业的AI助手，帮助用户解答问题。"),
    HumanMessage(content="请用三句话解释 LangChain ChatModel。"),
  ]

  response = model.invoke(messages)
  
  print("response class:", response.__class__.__name__)
  print("message type:", response.type)
  print("content:")
  print(response.content)
  print("response_metadata:")
  print(response.response_metadata)
  print("usage_metadata:")
  print(response.usage_metadata)

if __name__ == "__main__":
  main()