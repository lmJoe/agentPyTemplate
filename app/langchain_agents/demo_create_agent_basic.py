from langchain.agents import create_agent
from langchain_core.tools import tool

from app.langchain_models.model_factory import LangChainModelFactory

#   演示创建一个基本的 Agent 模型，用于查询课程章节的学习阶段。


@tool
def get_course_progress(chapter: int) -> str:
    """查询 AI Agent 课程指定章节的学习阶段。"""
    if chapter <= 19:
        return "前 19 章属于原生 AI 应用开发和项目一阶段。"

    if 20 <= chapter <= 28:
        return "第 20 到 28 章属于 LangChain 阶段。"

    if 29 <= chapter <= 38:
        return "第 29 到 38 章属于 LangGraph 阶段。"

    return "该章节属于后续高级项目阶段。"


def main():
    # 创建一个 DeepSeek Chat 模型实例。此处用的是 DeepSeek 的基础版本，温度设为0，即不引入随机性。
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0,
    )

    # 创建一个 Agent，它可以调用上面定义的 get_course_progress 工具。
    # - system_prompt 是 Agent 的初始提示，用于引导模型的行为。
    agent = create_agent(
        model=model,
        tools=[get_course_progress],
        system_prompt=(
            "你是一个 AI Agent 课程助教。"
            "当用户询问课程章节、阶段、进度时，可以调用工具查询。"
        ),
    )

    # 调用 Agent 模型，传入用户问题。
    # - messages 是一个包含用户问题的字典列表，每个字典表示一条消息。
    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "第 26 章属于哪个阶段？",
            }
        ]
    })

    #   打印 Agent 返回的消息列表。可以看到，除了用户的提问外，还有模型的回答和工具调用结果。
    # - 每条消息都有一个 type 字段，用于标识消息的类型，如 user、assistant、function_call 等。
    # - content 字段包含了消息的具体内容。
    # - tool_calls 字段是模型在执行过程中发起过的工具调用列表，每个元素是一个字典，包含了工具调用的参数。
    
    for message in result["messages"]:
        print(message.type, ":", message.content)
        print("tool_calls:", getattr(message, "tool_calls", None))
        print("=" * 80)


if __name__ == "__main__":
    main()