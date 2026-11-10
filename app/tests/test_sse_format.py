from app.utils.sse import format_sse, format_done_event, format_error_event
def main():
    print("message event:", format_sse(event="message", data={"id": 1, "text": "Hello"}))
    print("done event:")
    print(format_done_event())
    print("error event:")
    print(
        format_error_event(
            message="模型调用失败",
            code=50002,
        )
    )
if __name__ == "__main__":
    main()