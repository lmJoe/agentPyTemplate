from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_structured_outputs.schemas import IntentClassificationResult

# 示例：解释 PydanticOutputParser 的作用
# 第一，生成格式说明：parser.get_format_instructions()
# 第二，把模型输出解析成 Pydantic 对象：
    # 模型输出
    #  ↓
    # PydanticOutputParser
    #  ↓
    # IntentClassificationResult
# PydanticOutputParser 可以解析 LLM 输出为 Pydantic 对象，并提供 get_format_instructions() 返回 JSON 输出的格式说明。



def main():
    # 创建 PydanticOutputParser，指定输出类型为 IntentClassificationResult
    parser = PydanticOutputParser(
        pydantic_object=IntentClassificationResult,
    )
    # 创建 ChatPromptTemplate，指定系统消息和人类消息模板
    # Prompt 明确要求结构化输出
    # Parser 负责解析和校验
    # 失败后做重试或兜底

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "你是一个电商客服意图识别器。\n"
                "你必须根据格式要求输出结构化结果。\n"
                "不要输出 Markdown，不要输出解释。\n"
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

    chain = prompt | model | parser

    result = chain.invoke({
        "user_question": "我的订单怎么还没发货？",
    })

    print("result type:", type(result))
    print(result.model_dump())


if __name__ == "__main__":
    main()