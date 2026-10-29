


# 大模型供应商的基础异常类



class LLMProviderError(Exception):
    def __init__(
        self,
        message: str,
        provider: str,
        status_code: int | None = None,
        raw_error: str | None = None,
    ):
        # 适合展示或记录的错误说明
        self.message = message

        # 出错的供应商，例如 "deepseek"、"openai"
        self.provider = provider

        # HTTP 状态码，例如 401、429、500；不一定存在
        self.status_code = status_code

        # 原始错误内容，方便排查问题
        self.raw_error = raw_error

        # 调用 Exception 的初始化方法，
        # 这样 print(error) 时会显示 message
        super().__init__(message)


# 配置错误：
# 例如 API Key 未配置、Base URL 错误、模型名未配置
class LLMProviderConfigError(LLMProviderError):
    pass


# 请求超时：
# 例如模型响应太慢、网络连接长时间无响应
class LLMProviderTimeoutError(LLMProviderError):
    pass


# 返回解析错误：
# 例如服务商返回的 JSON 格式不符合预期
class LLMProviderResponseParseError(LLMProviderError):
    pass