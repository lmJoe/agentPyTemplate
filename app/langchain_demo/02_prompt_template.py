from langchain_core.prompts import ChatPromptTemplate

def run_prompt_template():
  # 创建一个聊天提示模板
  prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的{role_name}开发助手，帮助用户解答问题。"),
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
  run_prompt_template()
