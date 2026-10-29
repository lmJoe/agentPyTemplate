from langchain_openai import ChatOpenAI
from app.core.config import settings
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage,ToolMessage

def create_deepseek_chat_model():
  if not settings.deepseek_api_key:
    raise ValueError("Deepseek API key is not set in the environment variables.")

  return ChatOpenAI(
    model_name="deepseek-chat",
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    temperature=0.7,
  )

def run_chat_with_messages():
  model = create_deepseek_chat_model()
  message = [
    SystemMessage(content="你是一个专业的AI助手，帮助用户解答问题。"),
    HumanMessage(content="MCP 和 tool,多agent有什么区别？"),
  ]
  response = model.invoke(message)
  print(response.content)


def run():
  model = create_deepseek_chat_model()
  response = model.invoke("请用一句话解释什么是Langchain")
  print(response.content)
  print(type(response))

run_chat_with_messages()