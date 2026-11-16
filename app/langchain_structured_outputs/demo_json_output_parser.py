from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.langchain_models.model_factory import LangChainModelFactory

# 示例：解释 JsonOutputParser 的作用
# 适合场景：
# 1. 临时 JSON 输出
# 2. 字段结构不强
# 3. 探索性原型
# 4. 不需要严格枚举值
# 5. 后续自己再处理 dict

# 不适合场景：
# 1. 意图识别
# 2. 工具参数
# 3. Agent Plan
# 4. RAG 引用
# 5. 需要强校验的业务流程


# JsonOutputParser 适合轻量场景。但是如果模型输出要驱动业务逻辑：比如：
# 是否调用工具
# 是否转人工
# 是否退款
# 是否执行 Agent 步骤
# 就应该用 PydanticOutputParser 或 with_structured_output。因为这些场景需要强校验。

def main():
    parser = JsonOutputParser()

    # .partial(...) 用来预先填入 Prompt 模板中的变量。
    # .partial(...) 返回一个新的 ChatPromptTemplate，其中包含了预先填入变量的模板。
    # 这里使用了 parser.get_format_instructions() 来获取格式化指令，并将其作为变量传递给 prompt 的模板中。
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "你是一个电商客服意图识别器。\n"
                "你必须只输出 JSON，不要输出 Markdown，不要解释。\n"
                "{format_instructions}"
            ),
        ),
        (
            "human",
            "用户问题：{user_question}",
        ),
    ]).partial( 
        format_instructions=parser.get_format_instructions()  # 这里的 format_instructions 是从 parser 获取的格式化指令，用于指导模型输出 JSON 格式的数据。
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
    print(result)


if __name__ == "__main__":
    main()