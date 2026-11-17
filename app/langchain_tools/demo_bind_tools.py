from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_tools.registry import langchain_tool_registry


# 定义主函数，用于演示绑定工具到模型中并调用模型
def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0,
    )

    # 获取工具实例
    tools = langchain_tool_registry.get_many([
        "query_order",
        "query_logistics",
        "transfer_human",
    ])
    # 绑定工具到模型中  
    model_with_tools = model.bind_tools(tools)

    # 调用模型，传入对话历史和工具列表
    response = model_with_tools.invoke([
        SystemMessage(
            content=(
                "你是一个跨境电商客服助手。\n"
                "当用户询问订单状态时，优先调用工具查询真实信息。\n"
                "不要编造订单状态。"
            )
        ),
        HumanMessage(
            content="帮我查一下订单 10001 到哪了？"
        ),
    ])

    print("content:")
    print(response.content)
    print("=" * 80)

    print("tool_calls:")
    print(response.tool_calls)
    # 打印出来结构是
    # [
    #     {
    #         "name": "query_order",
    #         "args": {
    #             "order_id": "10001",
    #         },
    #         "id": "call_xxx",
    #         "type": "tool_call",
    #     }
    # ]

    #   如果模型认为需要调用工具，结果会出现在response.tool_calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print("tool name:", tool_call["name"])
            print("tool args:", tool_call["args"])
            print("tool id:", tool_call["id"])


if __name__ == "__main__":
    main()