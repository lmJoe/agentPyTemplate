from app.langchain_models.demo_chat_model_stream import main

import asyncio

if __name__ == "__main__":

    # 同步流式调用
    # main()

    # 异步流式调用
    asyncio.run(main())