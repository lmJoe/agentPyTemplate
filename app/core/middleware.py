import time
import uuid

from fastapi import FastAPI, Request, Response

from app.core.logging import get_logger
from app.core.request_context import set_trace_id, set_user_id




# 这段代码注册了一个全局 HTTP 中间件，用于为每个请求完成四件事：
# 1. 生成或读取 trace_id；
# 2. 读取用户 ID，并写入请求上下文；
# 3. 记录请求开始、结束和异常日志；
# 4. 统计耗时，并把追踪 ID、耗时写回响应头。

## 完整链路
# HTTP 请求到达
#     ↓
# 开始计时
#     ↓
# 读取 x-trace-id；未传则生成 trace_xxx
#     ↓
# 读取 x-user-id；未传则使用 "-"
#     ↓
# 写入 request_context
#     ↓
# 记录 request_start 日志
#     ↓
# call_next(request)：执行路由、依赖、Service 等后续逻辑
#     ↓
# 成功：计算耗时，写响应头，记录 request_end 日志
# 失败：记录完整异常日志，再继续抛出异常



logger = get_logger(__name__)

def register_middleware(app:FastAPI) -> None:
  @app.middleware("http")
  async def middleware_add_request_context(request:Request, call_next):

    # 记录高精度、单调递增的开始时间，用于计算耗时
    start_time = time.perf_counter()

    # 若客户端传了x-trace-id: trace_frontend_001 这种,沿用该 ID,否则自动生成trace_a1b2c3d4e5f6
    trace_id = request.headers.get("x-trace-id") or f"trace_{uuid.uuid4().hex[:12]}"
    user_id = request.headers.get("x-user-id") or "-"

    # 把数据写入请求上下文。前面定义的日志过滤器就可以自动将它们输出到每条日志中
    set_trace_id(trace_id)
    set_user_id(user_id)

    logger.info(
      f"request_start method={request.method} path={request.url.path}"
    )

    # 把请求交给后续 FastAPI 流程，包括路由匹配、依赖注入、接口函数和 Service。
    try:
      response:Response = await call_next(request)

    except Exception as e:
      cost_ms = (time.perf_counter() - start_time) * 1000

      # 记录异常日志和完整堆栈
      logger.exception(
        f"request_exception method={request.method}"
        f"path={request.url.path} cost_ms={cost_ms:.2f}"
      )
      raise

    cost_ms = (time.perf_counter() - start_time) * 1000

    # 把追踪 ID 和耗时回传给调用方，例如响应头
    # x-trace-id: trace_a1b2c3d4e5f6
    # x-process-time-ms: 38.46
    response.headers["x-trace-id"] = trace_id
    response.headers["x-process-time-ms"] = f"{cost_ms:.2f}" 

    # 记录一条 INFO 级别的日志
    logger.info(
      f"request_end method={request.method}"
      f"path={request.url.path}"
      f"status_code={response.status_code}"
      f"cost_ms={cost_ms:.2f}"
    )

    return response


# 最终日志打印
# 2026-09-20 14:04:54             请求时间
# INFO                            日志级别
# trace_id=trace_2084e7c40b51     日志ID
# user_id                         用户id
# app.core.middleware ：55        记录日志的 Python 模块名，即 app/core/middleware.py 的代码行号
# request_start                   请求刚进入中间件、尚未执行具体接口时的开始日志
# request_end：                   接口处理完成后的结束日志
# method=GET                      请求类型
# path=/api/v1/health             请求接口
# status_code=200                 HTTP 响应成功
# cost_ms=1.22                    后端处理该请求耗时约 1.22 毫秒

# 2026-09-20 14:04:54 | INFO | trace_id=trace_2084e7c40b51 | user_id=- | app.core.middleware : 55 | request_start method=GET path=/api/v1/health
# 2026-09-20 14:04:54 | 
# INFO | trace_id=trace_2084e7c40b51 | user_id=- | app.core.middleware : 82 | request_end method=GETpath=/api/v1/health status_code=200cost_ms=1.22