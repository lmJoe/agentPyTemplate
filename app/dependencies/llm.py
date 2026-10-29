from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMProviderFactory





# LLM 模型提供者”的模拟实现，并通过项目配置决定默认使用哪个模型


# 表示一个模拟的 LLM 服务提供者。以后可以替换成 DeepSeek、OpenAI、Qwen 等真实模型客户端
class MockLLMProvider:

  # 创建对象时接收模型名称，并保存下来。
  def __init__(self, model:str):
    self.model = model

  # 模拟调用 AI 模型
  async def chat(self,message:str) -> str:
    return f"模型:{self.model},回答内容:{message}"




# 获取真实大模型 Provider。
# Factory 会根据 settings.default_model 创建：
# DeepSeekProvider、QwenProvider 或 OpenAIProvider。
async def get_llm_provider() -> BaseLLMProvider:
  return LLMProviderFactory.create()

# 整条依赖链路
# 接口请求
#     ↓
# get_llm_provider()
#     ↓
# 从 settings.default_model 获取默认模型
#     ↓
# 创建 MockLLMProvider
#     ↓
# 注入到接口的 llm 参数
#     ↓
# llm.chat(message)