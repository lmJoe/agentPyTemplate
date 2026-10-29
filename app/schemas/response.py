from typing import Any, Generic, TypeVar
from pydantic import BaseModel,Field


# 创建泛型数据模型
# ApiResponse中 data 的具体类型暂时不固定，它由使用 ApiResponse 时决定
# T 是一个可替换的“数据类型变量”，让同一个 ApiResponse 可以复用来包装字符串、列表、聊天响应、用户信息等不同类型的数据。
T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
  code: int = Field(default=200, description="业务状态码")
  message: str = Field(default="success", description="提示消息")
  data: T | None = Field(default=None, description="返回数据") 
  trace_id: str | None = Field(default=None, description="请求追踪ID")

class ErrorDetail(BaseModel):
  field: str | None = Field(default=None, description="错误字段名")
  message: str = Field(...,description="错误消息")

class ErrorResponse(BaseModel):
  code: int = Field(default=500,description="错误码")
  message: str = Field(default="error", description="错误消息")
  data: dict | list | None = Field(default=None, description="错误详情")
  trace_id: str | None = Field(default=None,description="请求追踪ID")