from enum import Enum
from pydantic import BaseModel, Field


class UserRole(str,Enum):
  ADMIN = "admin"
  USER = "user"
  GUEST = "guest"

class CurrentUser(BaseModel):
  
  user_id: str = Field(..., description="The user's unique identifier")
  username:str = Field(...,description="用户名")
  role:UserRole = Field(default=UserRole.USER, description="用户角色")
  is_active:bool = Field(default=True,description="判断当前用户是否处于激活状态")