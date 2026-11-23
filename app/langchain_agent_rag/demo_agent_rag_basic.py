import json
import asyncio

from app.langchain_agent_rag.factory import (
    build_ecommerce_agent_with_rag,
    parse_agent_rag_result,
)
from app.langchain_agent_rag.index import ensure_rag_index


async def main():

    # 确保 RAG 索引存在
    ensure_rag_index()


    # 创建 RAG 智能体
    agent = build_ecommerce_agent_with_rag(
        provider="deepseek",
        model_name="deepseek-chat",
    )

    # 调用智能体，传入用户问题
    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": "订单未发货时可以退款吗？",
            }
        ]
    })

    # 解析智能体结果，并打印结果
    parsed = parse_agent_rag_result(result)

    print(json.dumps(
        parsed.model_dump(),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    asyncio.run(main())