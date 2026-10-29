# 导入项目配置。
# 包含 DASHSCOPE_API_KEY、QWEN_BASE_URL 等配置。
from app.core.config import settings

# 导入通用 OpenAI 兼容 Provider。
# 已经实现 chat()、stream_chat()、异常处理和响应解析。
from app.llm.providers.openai_compatible import OpenAICompatibleProvider

# 导入供应商名称枚举和请求模型
from app.llm.schemas import LLMProviderName, LLMRequest


# Qwen 供应商实现类
class QwenProvider(OpenAICompatibleProvider):

    # 标记当前 Provider 对应 Qwen
    provider_name = LLMProviderName.QWEN

    def __init__(self):
        # 调用父类初始化方法，传入 Qwen 专属配置
        super().__init__(
            # DashScope API Key
            api_key=settings.dashscope_api_key,

            # Qwen OpenAI 兼容接口的基础地址
            base_url=settings.qwen_base_url,

            # 未指定模型时使用 qwen-plus
            default_model="qwen-plus",

            # 请求超时为 60 秒
            timeout_seconds=60,
        )

    # 重写父类的请求体构建方法
    def _build_payload(
        self,
        request: LLMRequest,
        stream: bool,
    ) -> dict:
        # 先调用父类，生成通用请求体：
        # model、messages、temperature、stream、max_tokens 等
        payload = super()._build_payload(
            request=request,
            stream=stream,
        )

        # 只有流式请求时才额外添加 stream_options
        if stream:
            payload["stream_options"] = {
                # 要求流结束时附带 Token 用量统计
                "include_usage": True,
            }

        return payload