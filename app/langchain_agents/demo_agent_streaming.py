from app.langchain_agents.factory import build_ecommerce_agent
import asyncio

async def main():
    agent = build_ecommerce_agent(
        provider="deepseek",
        model_name="deepseek-chat",
    )

    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "帮我查一下订单 10001 到哪了？",
                }
            ]
        },
        stream_mode="updates",
    ):
        print("chunk:")
        print(chunk)
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())


    {'model': {'messages': [AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 39, 'prompt_tokens': 649, 'total_tokens': 688, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cache_write_tokens': None, 'cached_tokens': 512, 'image_tokens': None, 'text_tokens': None}, 'prompt_cache_hit_tokens': 512, 'prompt_cache_miss_tokens': 137}, 'model_provider': 'openai', 'model_name': 'deepseek-flash', 'system_fingerprint': 'bc19ba97cbe016479903222bb1578db6', 'id': '25a3253b-f6fe-4bbf-b25b-646180a2caf1', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--01a1ed92-3ae0-7243-912f-f155b1edf84d-0', tool_calls=[{'name': 'query_order', 'args': {'order_id': '10001'}, 'id': 'call_00_vO8ucEqFCGpCRnCASkEc8661', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 649, 'output_tokens': 39, 'total_tokens': 688, 'input_token_details': {'cache_read': 512}, 'output_token_details': {}})]}}