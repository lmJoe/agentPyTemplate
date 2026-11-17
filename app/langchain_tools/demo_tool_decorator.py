import asyncio

from app.langchain_tools.tools import query_order_simple


async def main():
    print("tool name:")
    print(query_order_simple.name)

    print("=" * 80)
    print("tool description:")
    print(query_order_simple.description)

    print("=" * 80)
    print("tool args:")
    print(query_order_simple.args)

    print("=" * 80)
    print("tool result:")
    result = await query_order_simple.ainvoke({
        "order_id": "10001",
    })
    print(result)


if __name__ == "__main__":
    asyncio.run(main())