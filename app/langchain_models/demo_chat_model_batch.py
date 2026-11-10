
from langchain_core.messages import HumanMessage, SystemMessage

from app.langchain_models.model_factory import LangChainModelFactory

# 批量调用

def main():
  model = LangChainModelFactory.create(
    provider="deepseek",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2048,
  )

  questions = [
    "什么是LangChain？",
    "什么是LangGraph？",
    "什么是RAG？",
  ]

  responses = model.batch(questions)

  for question, response in zip(questions, responses):
    print(f"Question: {question}")
    print("response:", response.content)
    print("-" * 40)

if __name__ == "__main__":
  main()
  