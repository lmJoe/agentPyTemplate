import json
from typing import Any



# 用于生成 SSE（Server-Sent Events，服务器发送事件）格式的文本。SSE 常用于大模型流式输出：后端持续推送内容，前端实时接收并显示

def format_sse(
    data: Any,
    event: str | None = None,
    event_id: str | None = None,
    retry: int | None = None,
) -> str:
    """
    将数据格式化为符合 SSE 协议的文本。

    SSE 常见格式：
        id: 1
        event: message
        retry: 3000
        data: 内容

    每一个 SSE 事件必须以两个换行符结尾。
    """
    lines = []

    # 可选：事件唯一 ID。
    # 前端断线重连时可使用该 ID 继续接收后续事件。
    if event_id is not None:
        lines.append(f"id: {event_id}")

    # 可选：事件类型，例如 message、done、error。
    if event is not None:
        lines.append(f"event: {event}")

    # 可选：前端断线后建议的重连等待时间，单位为毫秒。
    if retry is not None:
        lines.append(f"retry: {retry}")

    # 字符串保持原样；字典、列表等其他对象转为 JSON。
    # ensure_ascii=False 可避免中文被转义为 \uXXXX。
    if isinstance(data, str):
        payload = data
    else:
        payload = json.dumps(data, ensure_ascii=False)

    # SSE 的多行数据要求每一行都以 data: 开头。
    for line in payload.splitlines():
        lines.append(f"data: {line}")

    # 两个换行符表示一个 SSE 事件结束。
    return "\n".join(lines) + "\n\n"


def format_done_event(data: dict | None = None) -> str:
    """
    生成“流式响应已结束”的 SSE 事件。

    如果未提供 data，默认返回：
        {"finish_reason": "stop"}
    """
    return format_sse(
        event="done",
        data=data or {
            "finish_reason": "stop",
        },
    )


def format_error_event(
    message: str,
    code: int = 50000,
    detail: dict | None = None,
) -> str:
    """
    生成“发生错误”的 SSE 事件。

    参数：
        message: 错误信息
        code: 业务错误码，默认为 50000
        detail: 可选的错误详情
    """
    return format_sse(
        event="error",
        data={
            "code": code,
            "message": message,
            "detail": detail or {},
        },
    )