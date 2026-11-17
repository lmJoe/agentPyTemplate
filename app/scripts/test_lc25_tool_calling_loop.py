import asyncio

from app.langchain_tools.demo_tool_calling_loop import main

# 完整实现了 Tool Calling 闭环的示例代码，其中包括了如何初始化模型、工具和执行器，以及如何在对话中循环调用这些工具。
# 第一步：model.bind_tools(tools)
# 第二步：模型返回 AIMessage.tool_calls
# 第三步：后端执行工具
# 第四步：生成 ToolMessage
# 第五步：把 first_response 和 ToolMessage 追加回 messages
# 第六步：再次调用模型生成最终回答


if __name__ == "__main__":
    asyncio.run(main())