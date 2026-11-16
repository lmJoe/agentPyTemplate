from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.langchain_models.model_factory import LangChainModelFactory

# `demo_prompt_parser_chain.py` 用于生成符合指定数据结构的结果，更适合意图分类等需要程序读取字段的场景


# 定义输出格式 IntentResult
# 这是模型回答的数据结构，规定结果必须包含：
# - intent：用户意图，只能是列出的几个字符串之一，例如 "query_order"、`"refund"或"logistics"`。
# - confidence：置信度，必须在 0 到 1 之间。
# - reason：判断原因，字符串类型。
# 如果模型输出不符合这些类型或限制，解析时可能报错。
class IntentResult(BaseModel):
    intent: Literal[
        "query_order",
        "refund",
        "logistics",
        "product_question",
        "human_service",
        "other",
    ] = Field(..., description="用户意图")

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="置信度",
    )

    reason: str = Field(..., description="判断原因")


def main():
    # 告诉 LangChain：模型的回答要解析为 IntentResult。解析器也会提供相应的格式说明，提示模型按要求返回结果。
    parser = PydanticOutputParser(
        pydantic_object=IntentResult,
    )

    # 提示词包含两部分：
    # - system 消息：告诉模型它是电商客服意图识别器，并附上解析器生成的格式要求。
    # - human 消息：把 {user_question} 替换成实际用户问题。
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "你是一个电商客服意图识别器。\n"
                "你必须根据格式要求输出。\n"
                "{format_instructions}"
            ),
        ),
        (
            "human",
            "用户问题：{user_question}",
        ),
    ]).partial(
        format_instructions=parser.get_format_instructions()
    )

    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0,
    )

    # 串联并运行链
    # 用输入变量生成提示词；
    # 调用模型生成回答；
    # 把回答解析并校验成 IntentResult。
    chain = prompt | model | parser

    result = chain.invoke({
        "user_question": "我的订单怎么还没发货？",
    })

    print(result.model_dump())


if __name__ == "__main__":
    main()