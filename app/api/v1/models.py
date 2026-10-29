# 模型列表接口

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.response import ApiResponse
from app.dependencies.auth import require_admin
from app.schemas.user import CurrentUser
router = APIRouter()

class ModelInfo(BaseModel):
    name: str = Field(..., description="模型名称")
    provider: str = Field(default="mock", description="模型厂商")
    support_stream: bool = Field(default=True, description="是否支持流式输出")

class ModelListResponse(BaseModel):
    models: list[ModelInfo] = Field(default_factory=list, description="模型列表")

# 返回当前系统支持哪些模型
@router.get("/models", response_model=ApiResponse[ModelListResponse])

# admin_user: CurrentUser = Depends(require_admin) 用户调用这个方法的时候,需要管理员权限,得先通过他的验证
async def list_models(admin_user: CurrentUser = Depends(require_admin)) -> ApiResponse[ModelListResponse]:
    models = [
        ModelInfo(
            name=model,
            provider=get_provider_name(model),
            support_stream=True
        )
        for model in settings.supported_model_list
    ]
    return ApiResponse[ModelListResponse](
        data=ModelListResponse(models=models)
    )

def get_provider_name(model:str) -> str:
    if model.startswith("deepseek"):
        return "deepseek"
    if model.startswith("qwen"):
        return "qwen"
    if model.startswith("gpt"):
        return "openai"
    return "unknown"