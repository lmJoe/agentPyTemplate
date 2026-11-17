import asyncio

from app.langchain_tools.tools import (
    query_logistics_tool,
    query_order_tool,
    transfer_human_tool,
)


async def main():
    tools = [
        query_order_tool,
        query_logistics_tool,
        transfer_human_tool,
    ]

    for tool_item in tools:
        print("tool name:", tool_item.name)
        print("description:", tool_item.description)
        print("args:", tool_item.args)
        print("=" * 80)

    result = await query_order_tool.ainvoke({
        "order_id": "10001",
    })

    print("query_order result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())