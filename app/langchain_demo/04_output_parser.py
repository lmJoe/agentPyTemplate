from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings

# 定义一个 Pydantic 模型，用于解析用户意图识别的输出
class IntentResult(BaseModel):
    intent: Literal[
        "query_order", # 查询订单
        "refund", # 申请退款
        "product_question", # 产品问题
        "other", # 其他
    ] = Field(..., description="用户意图")

    # 置信度，表示模型对意图识别的信心程度，范围在0到1之间
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="置信度",
    )


def create_model():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )


def run_parser_chain():

    # 创建一个 Pydantic 输出解析器，指定要解析的 Pydantic 模型为 IntentResult
    parser = PydanticOutputParser(pydantic_object=IntentResult)

    # 创建一个聊天提示模板，包含系统消息和用户消息
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "你是一个电商客服意图识别器。\n"
                "你必须按照下面的格式要求输出。\n"
                "{format_instructions}"
            ),
        ),
        (
            "human",
            "用户问题：{question}",
        ),
    ])

    # 使用 partial 方法将格式化指令传递给提示模板，以便在生成提示时包含输出格式要求
    prompt = prompt.partial(
        format_instructions=parser.get_format_instructions()
    )

    model = create_model()

    chain = prompt | model | parser

    result = chain.invoke({
        "question": "我的订单怎么还没发货？",
    })

    print(type(result))
    print(result.model_dump())


if __name__ == "__main__":
    run_parser_chain()