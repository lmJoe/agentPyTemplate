from langchain_core.prompts import ChatPromptTemplate


# 演示 LangChain PromptTemplate 的作用 提示词模板


def main():
  # 创建一个聊天提示模板
  prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的{role_name}开发助手，帮助用户解答问题。"
     "回答要求：\n"
     "1. 回答内容必须是中文。\n"
     "2. 回答内容必须简明扼要，控制在100字以内。\n"
     "3. 回答内容必须包含示例代码。\n"),
    ("human","请用一句话解释：{question}")
  ])

  res = prompt.invoke({
    "role_name":"Langchain",
    "question":"什么是Langchain"
  })

  print(type(res))
  print("message:",res)
  print(res)

  for msg in res.messages:
    print(msg.type, ":", msg.content)

if __name__ == "__main__":
  main()