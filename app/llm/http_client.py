# 异步 HTTP 请求库
import httpx


# 统一配置模型请求超时规则的异步 HTTP 客户端，用于调用 DeepSeek 等外部 AP


# timeout_seconds 默认是 60 秒，控制“读取响应”的最长等待时间。
def create_llm_http_client(
    timeout_seconds: float = 60,
) -> httpx.AsyncClient:

    # 配置请求不同阶段的超时时间
    timeout = httpx.Timeout(
        # 建立 TCP/HTTPS 连接最多等待 10 秒
        connect=10,

        # 已连接后，读取服务端响应最多等待 timeout_seconds 秒
        read=timeout_seconds,

        # 向服务端发送请求数据最多等待 10 秒
        write=10,

        # 连接池中没有可用连接时，最多等待 10 秒
        pool=10,
    )

    # 返回配置好的异步 HTTP 客户端
    return httpx.AsyncClient(timeout=timeout)