from langchain_openai import ChatOpenAI
from app.core.config import settings


# LangChain 模型工厂类，用于创建不同提供商的 LangChain 模型实例
class LangChainModelFactory:
  # 这个工厂类用于创建 LangChain 模型实例，支持不同的提供商和模型配置。
  @staticmethod
  def create(
    provider: str | None = None, # 指定 LLM 提供商，如果为 None，则使用默认提供商。
    model: str | None = None, # 指定模型名称，如果为 None，则使用默认模型。
    temperature: float = 0.7, # 控制生成文本的随机性，范围在0到1之间。
    max_tokens: int = 2048, # 设置生成文本的最大长度，单位为 token。
    streaming: bool = False, # 是否启用流式输出，默认为 False。
  ) -> ChatOpenAI:
    provider = provider or settings.default_llm_provider # 如果未指定提供商，则使用默认提供商。
    model = model or settings.default_model # 如果未指定模型，则使用默认模型。

    if provider == "deepseek":
      return LangChainModelFactory.create_deepseek(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
      )

    if provider == "openai":
      return LangChainModelFactory.create_openai(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
      )

    if provider == "qwen":
      return LangChainModelFactory.create_qwen(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
      )

    raise ValueError(f"不支持的 LangChain 模型供应商：{provider}")


  # 创建 DeepSeek 模型实例
  @staticmethod
  def create_deepseek(
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    streaming: bool = False,
  ) -> ChatOpenAI:
    if not settings.deepseek_api_key:
      raise ValueError("请先配置 DEEPSEEK_API_KEY")
    return ChatOpenAI(
      model=model,
      api_key=settings.deepseek_api_key,
      base_url=settings.deepseek_base_url,
      temperature=temperature,
      max_tokens=max_tokens,
      streaming=streaming,
    )

  # 创建 Qwen 模型实例
  @staticmethod
  def create_qwen(
    model: str = "qwen-plus",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    streaming: bool = False,
  ) -> ChatOpenAI:
    if not settings.dashscope_api_key:
      raise ValueError("请先配置 DASHSCOPE_API_KEY")
    
    return ChatOpenAI(
      model=model,
      api_key=settings.dashscope_api_key,
      base_url=settings.qwen_base_url,
      temperature=temperature,
      max_tokens=max_tokens,
      streaming=streaming,
    )

  # 创建 OpenAI 模型实例
  @staticmethod
  def create_openai(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    streaming: bool = False,
  ) -> ChatOpenAI:
      if not settings.openai_api_key:
          raise RuntimeError("请先配置 OPENAI_API_KEY")

      return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
      )