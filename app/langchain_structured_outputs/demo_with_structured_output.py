from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_structured_outputs.schemas import IntentClassificationResult

# 示例：使用 with_structured_output 方法获取结构化输出的模型实例

def main():
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0,
    )

    # ChatOpenAI.with_structured_output() 参考文档把它描述为把模型包装成返回匹配给定 schema 的输出；schema 可以是 Pydantic 类、TypedDict、JSON Schema 或 OpenAI function schema 等形式，具体支持取决于模型和方法。
    # with_structured_output 注意事项
    # 第一，不同模型支持情况不一样。
    # OpenAI 官方模型支持的结构化能力，和其他 OpenAI-compatible 服务不一定完全一致。
    # 第二，有些 provider 对 JSON Schema、tool calling、json_object 的支持细节不同。
    # 第三，课程中我们用 DeepSeek / Qwen / OpenAI 都可能通过 ChatOpenAI 接入，但不代表所有结构化输出方法都完全等价。
    # 所以真实项目里
    # 优先写一个统一 Service
    # 先尝试 with_structured_output
    # 失败时 fallback 到 PydanticOutputParser

    # PydanticOutputParser
    # 更像通用方案
    # with_structured_output
    # 更像模型能力优先方案


    structured_model = model.with_structured_output(
        IntentClassificationResult
    )

    result = structured_model.invoke([
        SystemMessage(
            content=(
                "你是一个电商客服意图识别器。\n"
                "请根据用户问题输出结构化分类结果。"
            )
        ),
        HumanMessage(
            content="我的订单怎么还没发货？"
        ),
    ])

    print("result type:", type(result))
    print(result.model_dump())


if __name__ == "__main__":
    main()