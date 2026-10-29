from app.utils.sse import (
    format_done_event,   # 生成流式响应结束事件
    format_error_event,  # 生成流式响应错误事件
    format_sse,          # 生成通用 SSE 事件
)


def main():
    """演示不同 SSE 事件的输出格式。"""

    # 1. 生成普通消息事件
    print("message event:")
    print(
        format_sse(
            # 事件名称；前端可监听该类型，例如 addEventListener("message", ...)
            event="message",

            # 要推送给前端的数据；字典会自动转换为 JSON
            data={
                "content": "AI Agent",
            },
        )
    )

    # 2. 生成流式响应结束事件
    print("done event:")
    print(
        format_done_event()
    )

    # 3. 生成错误事件
    print("error event:")
    print(
        format_error_event(
            # 错误描述，供前端展示
            message="模型调用失败",

            # 自定义业务错误码
            code=50002,
        )
    )


# 仅在当前文件被直接运行时执行示例代码
if __name__ == "__main__":
    main()