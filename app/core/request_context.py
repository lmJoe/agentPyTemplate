from contextvars import ContextVar

# ContextVar 保存当前请求上下文里的变量,保证每一次请求都有自己的上下文
# 为什么不能用全局变量保存:原因
# fastApi是并发请求,同一时间可能有多个用户发送多次请求
# 按普通全局变量的话,会出现覆盖的情况
trace_id_var:ContextVar[str] = ContextVar("trace_id")
user_id_var:ContextVar[str] = ContextVar("user_id")

def set_trace_id(trace_id:str) -> None:
  trace_id_var.set(trace_id)

def set_user_id(user_id:str) -> None:
  user_id_var.set(user_id)

def get_trace_id() -> str:
  return trace_id_var.get()

def get_user_id() -> str:
  return user_id_var.get()