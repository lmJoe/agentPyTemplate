from langchain_core.prompts import ChatPromptTemplate



def main():
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是一个专业的 {role_name}。",
        ),
        (
            "human",
            "请回答用户问题：{user_question}",
        ),
    ])

    # 打印输入的变量
    print("input_variables:", prompt.input_variables)
    # 打印选择的变量
    print("optional_variables:", prompt.optional_variables)
    # 打印类型的变量
    print("partial_variables:", prompt.partial_variables)

    # 测试 prompt 的生成效果

    prompt_value = prompt.invoke({
        "role_name": "AI Agent 课程助教",
        "user_question": "LangChain Prompt 是什么",
    })

    print("prompt_value type:", type(prompt_value))
    print("messages:")

    for message in prompt_value.messages:
        print(message.type, ":", message.content)
        print("-" * 80)


if __name__ == "__main__":
    main()