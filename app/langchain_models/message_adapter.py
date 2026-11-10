# 适配器

from langchain_core.messages import (
  AIMessage,
  BaseMessage,
  HumanMessage,
  SystemMessage,
  ToolMessage
)

from app.llm.schemas import (
  LLMMessage,
  LLMResponse,
  LLMRole,
  LLMToolCall,
  LLMUsage
)

from app.llm.schemas import LLMProviderName

# 
def to_langchain_message(message:LLMMessage) -> BaseMessage:
  if message.role == LLMRole.SYSTEM:
    return SystemMessage(content=message.content)

  if message.role == LLMRole.USER:
    return HumanMessage(content=message.content)

  if message.role == LLMRole.ASSISTANT:
    return AIMessage(content=message.content)

  if message.role == LLMRole.TOOL:
    if not message.tool_call_id:
      raise ValueError("ToolMessage 必须提供 Tool_call_id")

    return ToolMessage(
      content=message.content,
      tool_call_id=message.tool_call_id
    )
  
  raise ValueError(f"不支持的消息角色：{message.role}")

def to_langchain_messages(messages:list[LLMMessage]) -> list[BaseMessage]:
  return [
    to_langchain_message(messages)
    for message in messages
  ]

def to_llm_usage(ai_message: AIMessage) -> LLMUsage:
  usage = ai_message.usage_metadata or {}
  return LLMUsage(
    prompt_tokens=usage.get("input_tokens", 0)
    
  )
    