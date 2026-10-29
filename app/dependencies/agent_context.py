import uuid
from fastapi import Depends, Query

from app.dependencies.auth import get_current_user
from app.schemas.user import CurrentUser

# 封装一次 Agent 请求运行时所需的“上下文信息"


class AgentContext:
  def __init__(
      self,

      # 当前请求的用户信息,Agent 可以根据它做权限判断、记录操作人或隔离用户数据
      # 例如:
      # CurrentUser(
      #     user_id="u_001",
      #     username="alice",
      #     role=UserRole.USER,
      #     is_active=True,
      # )
      current_user:CurrentUser, 

      # 本次请求的唯一链路追踪 ID  如trace_a1b2c3d4,它用于把一次请求经过 API、Agent、LLM、数据库等环节的日志关联起来，方便排错
      trace_id:str,

      # 是否开启调试模式
      debug:bool
  ):
    self.current_user = current_user
    self.trace_id = trace_id
    self.debug = debug

## 获取agent上下文
# get_agent_context有两个参数

async def get_agent_context(
    # 参数1:current_user,当前用户依赖注入当前用户,FastAPI 会先执行 get_current_user()
    # 从请求头读取 x-user-id、x-username；
    # 校验用户信息；
    # 成功后返回 CurrentUser；
    # 失败时返回 401，后续不会创建 AgentContext。
    current_user: CurrentUser = Depends(get_current_user), 

    # 参数2:debug 是否返回日志
    debug: bool = Query(default=False, description="是否开启调试模式")
) -> AgentContext:
  # 最终返回这个类
  return AgentContext(
    current_user = current_user,
    trace_id=f"trace_{uuid.uuid4().hex[:8]}",
    debug=debug
  )

# 调用run_agent -> get_agent_context -> get_current__user -> verfy_api_key