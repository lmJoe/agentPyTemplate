from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def main():
    prompt = ChatPromptTemplate.from_messages([
         (
            "system",
            "你是一个专业 AI Agent 课程助教。",
        ),
        MessagesPlaceholder(
            variable_name="history", # 这里的变量名要和下面的 invoke 方法中的 key 一致
            optional=True, # 表示这个变量是可选的
            n_messages=6, # 表示最多保留6条历史消息,因为历史消息不能无限塞进Prompt中,因为上下文有token限制，也有成本
        ),
        (
            "human",
            "{user_question}",
        ),
    ])

    history = [
        HumanMessage(content="什么是 AI Agent？"),
        AIMessage(content="AI Agent 是可以理解目标、规划步骤并调用工具的智能体。"),
    ]
    
    prompt_value = prompt.invoke({
        "history": history,
        "user_question": "那 LangChain 和 AI Agent 有什么关系？",
    })