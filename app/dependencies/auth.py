# Header：读取 HTTP 请求头。
# HTTPException：中断请求并返回 HTTP 错误响应
# status：FastAPI 提供的 HTTP 状态码常量
from fastapi import Header, HTTPException, status,Depends

# CurrentUser：当前登录用户的数据模型
# UserRole：用户角色枚举
from app.schemas.user import CurrentUser,UserRole

from app.core.config import settings
from app.core.request_context import set_user_id

async def verfy_api_key(
    x_api_key:str | None = Header(default=None)
) -> str:
  if not x_api_key:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing API key")
  if x_api_key != settings.app_api_key:
    # HTTP_403_FORBIDDEN 有认证 但认证不正确或权限有错
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Invalid API key")
  return x_api_key


# FastAPI 会从请求头中读取
# x-user-id: u_001
# x-username: alice
# 赋值为
# x_user_id == "u_001"
# x_username == "alice"

# alias 的作用是：Python 变量采用下划线命名法，但请求头使用连字符命名法
# x_user_id = Header(..., alias="x-user-id")  对应  x-user-id: u_001 而不是 x_user_id: u_001

async def get_current_user(
    # 这里的Depends是子依赖,use_cache=True 的意思是：同一次请求中，若多个地方依赖同一个函数，FastAPI 默认只执行一次并复用结果
    app_api_key:str = Depends(verfy_api_key,use_cache=True),
    x_user_id:str | None = Header(default=None, alias="x-user-id"),
    x_username:str | None = Header(default=None,alias="x-username"),
    x_user_role:str | None = Header(default="user")
) -> CurrentUser:
  # 如果没有传 x-username，直接返回 401 未认证
  if not x_username:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing x_username")

  # 如果没有传 x-user-id，也返回 401。
  if not x_user_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing x_user_id")

  # 管理员角色判断
  role = UserRole.ADMIN if x_user_role == "admin" else UserRole.USER

  # 用户认证通过之后，把user_id 放到整个请求上下文里
  set_user_id(x_user_id)

  return CurrentUser(user_id=x_user_id, username=x_username, is_active=True, role=role)


# 管理员权限依赖
async def require_admin(
    current_user:CurrentUser = Depends(get_current_user)
) -> CurrentUser:
  if current_user.role != UserRole.ADMIN:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not enougt permissions")
  return current_user
