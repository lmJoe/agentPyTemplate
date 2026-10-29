# 导入项目配置。
# 配置通常来自 .env，例如 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL。
from app.core.config import settings

# 导入通用的 OpenAI 兼容供应商实现。
# 其中已经实现 chat() 和 stream_chat()。
from app.llm.providers.openai_compatible import OpenAICompatibleProvider

# 导入供应商名称枚举
from app.llm.schemas import LLMProviderName


# DeepSeek 供应商类。
# 继承后自动拥有普通聊天和流式聊天能力。
class DeepSeekProvider(OpenAICompatibleProvider):

    # 指定当前 Provider 对应 DeepSeek。
    # 父类会用它记录日志和构造异常信息。
    provider_name = LLMProviderName.DEEPSEEK

    def __init__(self):
        # 调用父类构造函数，传入 DeepSeek 专属配置。
        super().__init__(
            # DeepSeek API Key，来自 .env 配置
            api_key=settings.deepseek_api_key,

            # DeepSeek API 基础地址
            base_url=settings.deepseek_base_url,

            # 请求未指定模型时使用的默认模型
            default_model="deepseek-chat",

            # 调用模型接口的超时时间
            timeout_seconds=60,
        )