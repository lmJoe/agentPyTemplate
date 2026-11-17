# 工具调用流程示例（langchain_tools）

用户问题
 ↓
后端发送 messages + tools 给模型
 ↓
模型判断需要调用 query_order
 ↓
模型返回 tool_calls
 ↓
后端解析 tool_calls
 ↓
后端校验 arguments
 ↓
后端执行 query_order
 ↓
工具返回真实结果
 ↓
后端把 tool result 追加到 messages
 ↓
再次调用模型
 ↓
模型生成最终回复