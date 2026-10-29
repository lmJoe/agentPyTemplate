
# 一组 Redis Key 生成函数。它们统一键名格式，避免不同功能的数据互相冲突，也便于按前缀查询和清理

# 根据问题哈希生成“聊天回答缓存”的 Redis Key。
# 示例：chat:response:a1b2c3
def chat_response_cache_key(question_hash: str) -> str:
    return f"chat:response:{question_hash}"


# 根据接口名和用户 ID 生成“限流计数器”的 Key。
# 示例：rate_limit:chat:u_10001
def rate_limit_key(user_id: str, api_name: str) -> str:
    return f"rate_limit:{api_name}:{user_id}"


# 根据 API Key 的哈希值生成 API Key 缓存 Key。
# 示例：api_key:8f14e45f
# 使用哈希而不是原始 API Key，避免敏感信息直接出现在 Redis 中。
def api_key_cache_key(api_key_hash: str) -> str:
    return f"api_key:{api_key_hash}"


# 根据会话 ID 生成“最近消息缓存”的 Key。
# 示例：conversation:c_a1b2c3d4:recent_messages
def conversation_recent_messages_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:recent_messages"


# 根据 Agent 运行 ID 生成“运行状态”的 Key。
# 示例：agent:run:run_123:state
def agent_run_state_key(run_id: str) -> str:
    return f"agent:run:{run_id}:state"