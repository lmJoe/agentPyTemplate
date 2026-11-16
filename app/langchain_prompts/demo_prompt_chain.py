from langchain_core.output_parsers import StrOutputParser

from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_prompts.templates import GENERAL_CHAT_PROMPT


# 演示如何使用通用聊天 Prompt 模板。`demo_prompt_chain.py` 用于生成普通文本回答

def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7,
    )

    parser = StrOutputParser()

    # 创建一个 LangChain Chain，它将使用 GENERAL_CHAT_PROMPT 作为 Prompt 模板。
    chain = GENERAL_CHAT_PROMPT | model | parser

    # 调用 chain 的 invoke 方法，传入用户的问题。
    result = chain.invoke({
        "history": [],
        "user_question": "请用三句话解释 LangChain Prompt 的作用。",
    })

    print(result)


if __name__ == "__main__":
    main()