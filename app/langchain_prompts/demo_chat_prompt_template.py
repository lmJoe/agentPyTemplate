from langchain_core.prompts import ChatPromptTemplate


# 定义 LangChain Prompt 模板并生成 prompt 对象

def main():
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是一个专业的 AI Agent 课程助教。",
        ),
        (
            "human",
            "请用三句话解释：{topic}",
        ),
    ])

    prompt_value = prompt.invoke({
        "topic": "LangChain Prompt",
    })

    print("prompt_value type:", type(prompt_value))
    print("messages:")

    for message in prompt_value.messages:
        print(message.type, ":", message.content)
        print("-" * 80)


if __name__ == "__main__":
    main()