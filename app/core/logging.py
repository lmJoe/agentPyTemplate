# 日志记录

import logging
import sys

from app.core.request_context import get_trace_id,get_user_id


# 请求上下文的日志过滤器
class RequestContextFilter(logging.Filter):
  def filter(self, record:logging.LogRecord) -> bool:

    # 每次打印之前都会执行,下面两个方法,为当前日志补上两个字段
    # trace_id：本次请求的链路追踪 ID
    # user_id：当前请求用户的 ID
    record.trace_id = get_trace_id() or "-"
    record.user_id = get_user_id() or "-"
    return True

def setup_logging() -> None:
  # 获取日志
  logger = logging.getLogger()

  # 设置这个 Logger 只处理 INFO 级别及以上的日志
  # DEBUG    调试细节
  # INFO     正常运行信息
  # WARNING  警告
  # ERROR    错误
  # CRITICAL 严重错误
  # 如果开发时需要看到更详细的日志，可以改为：logger.setLevel(logging.DEBUG)
  logger.setLevel(logging.INFO)

  # 清除已有 Handler，避免重复输出日志
  logger.handlers.clear()

  # 控制台的输出
  handler = logging.StreamHandler(sys.stdout)

  # 设置输出的日志格式,如2026-09-20 10:30:00 | INFO | trace_id=trace_a1b2c3d4 | user_id=u_001 | app.service.chat_service : 25 | Chat completed
  formatter = logging.Formatter(
    fmt = (
      "%(asctime)s | %(levelname)s | "
      "trace_id=%(trace_id)s | user_id=%(user_id)s | "
      "%(name)s : %(lineno)d | %(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
  )

  handler.setFormatter(formatter)
  handler.addFilter(RequestContextFilter())

  logger.addHandler(handler)

# 获取日志
def get_logger(name:str) -> logging.Logger:
  return logging.getLogger(name)