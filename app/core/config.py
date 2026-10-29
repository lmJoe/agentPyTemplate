from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict


# 集中管理项目配置，并从 .env 文件读取配置值

class Settings(BaseSettings):
  app_name:str=Field(default="AI Agent Course API")
  app_env:str=Field(default="development")
  app_version:str=Field(default="0.1.0")
  api_v1_prefix: str = Field(default="/api/v1")
  debug:bool=Field(default=True)

  default_model:str=Field(default="deepseek-chat")
  
  default_llm_provider: str = Field(default="deepseek")

  app_api_key:str=Field(default="dev-api-key-123")
  # 以逗号分隔的字符串保存支持的模型
  supported_models:str=Field(default="deepseek-chat,qwen-plus,gpt-4o-mini")

  database_url:str = Field(
    default = "postgresql+asyncpg://postgres:l123456@localhost:5432/ai_agent"
  )
  redis_url: str = Field(default="redis://:redis123@localhost:6379/0")
  redis_default_ttl_seconds: int = Field(default=300)
  rate_limit_window_seconds: int = Field(default=60)
  rate_limit_max_requests: int = Field(default=20)

  openai_api_key: str = Field(default="")
  openai_base_url: str = Field(default="https://api.openai.com/v1")

  deepseek_api_key: str = Field(default="")
  deepseek_base_url: str = Field(default="https://api.deepseek.com")

  dashscope_api_key: str = Field(default="")
  qwen_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")


  model_config=SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
  )


  # supported_model_list 再把supported_models转换为真正的列表
  # 如["deepseek-chat", "qwen-plus", "gpt-4o-mini"] 
  @property
  def supported_model_list(self) -> list[str]:
    return [
      model.strip() # 去掉模型名称两边的空格
      for model in self.supported_models.split(",")
      if model.strip() # 过滤空字符串
    ]


# @lru_cache 会缓存 Settings() 创建的结果。也就是说，项目中无论调用多少次get_settings()，通常都会得到同一个配置对象，不会反复读取 .env 和重复创建实例
@lru_cache
def get_settings() -> Settings:
  return Settings()

settings = get_settings()