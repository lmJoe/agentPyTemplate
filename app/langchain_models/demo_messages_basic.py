from langchain_core.messages import (
  AIMessage,
  HumanMessage,
  SystemMessage,
  ToolMessage
)


# 演示 LangChain Message 的作用
# python scripts/test_lc22_messages.py

def main():
  messages = [
    SystemMessage(content="你是一个专业的AI助手，帮助用户解答问题。"),
    HumanMessage(content="请解释 LangChain Message 的作用。"),
    AIMessage(content="LangChain Message 是对大模型对话消息的对象化封装。"),
    ToolMessage(
      content="{""order_id"": ""123456"", ""status"": ""已发货"", ""estimated_delivery"": ""3天后"", ""logistics_company"": ""顺丰快递"", ""tracking_number"": ""SF123456789""}",
      tool_call_id="call_query_order_001"
    )
  ]

  for message in messages:
    # 打印消息的类名、类型、内容和模型序列化后的字典表示
    print("class:",message.__class__.__name__)
    print("type:",message.type)
    print("content:",message.content)
    print("model_dump:")
    print(message.model_dump())
    print("=" * 80)

if __name__ == "__main__":
  main()