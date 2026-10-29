# 项目配置，包含 default_model
from app.core.config import settings

# 所有 Provider 的统一抽象接口
from app.llm.base import BaseLLMProvider

# 三个具体供应商实现
from app.llm.providers import (
    DeepSeekProvider,
    OpenAIProvider,
    QwenProvider,
)

# 供应商名称枚举
from app.llm.schemas import LLMProviderName


# 大模型供应商工厂类
class LLMProviderFactory:

    # 静态方法：不依赖类实例，
    # 可直接调用 LLMProviderFactory.create()
    @staticmethod
    def create(
        provider: LLMProviderName | str | None = None,
    ) -> BaseLLMProvider:

        # 如果调用方没指定 Provider，
        # 根据默认模型名推断供应商。
        provider_name = (
            provider
            or infer_provider_from_model(settings.default_model)
        )

        # 若传入的是字符串，例如 "deepseek"，
        # 则转换为 LLMProviderName 枚举。
        if isinstance(provider_name, str):
            provider_name = LLMProviderName(provider_name)

        # 根据供应商名称，创建对应 Provider 实例。
        if provider_name == LLMProviderName.DEEPSEEK:
            return DeepSeekProvider()

        if provider_name == LLMProviderName.QWEN:
            return QwenProvider()

        if provider_name == LLMProviderName.OPENAI:
            return OpenAIProvider()

        # 未支持的供应商名称会报错。
        raise ValueError(
            f"不支持的 LLM Provider：{provider_name}"
        )


# 根据模型名称前缀推断对应供应商。
def infer_provider_from_model(
    model: str,
) -> LLMProviderName:

    # 例如 deepseek-chat、deepseek-reasoner
    if model.startswith("deepseek"):
        return LLMProviderName.DEEPSEEK

    # 例如 qwen-plus、qwen-turbo
    if model.startswith("qwen"):
        return LLMProviderName.QWEN

    # 例如 gpt-4.1-mini
    if model.startswith("gpt"):
        return LLMProviderName.OPENAI

    # 无法识别时，当前代码默认使用 DeepSeek
    return LLMProviderName.DEEPSEEK