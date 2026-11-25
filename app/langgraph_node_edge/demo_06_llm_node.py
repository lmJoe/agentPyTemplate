import asyncio
from typing import TypedDict

# 用于构造发给模型的系统消息和用户消息。
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

# 项目中的模型工厂，负责创建指定提供商和型号的聊天模型。
from app.langchain_models.model_factory import LangChainModelFactory

# LLM Node
# 演示了一个调用大语言模型的异步 LangGraph 工作流：先让模型根据用户问题生成草稿，再把草稿包装成最终答复。
# draft_answer_node 通过 LangChainModelFactory 创建 DeepSeek 聊天模型。
# 节点向模型发送系统提示和用户问题，并将模型回复写入 draft_answer。
# polish_answer_node 去除草稿首尾空白，添加“【最终回答】”标记。
# main 使用 ainvoke() 异步运行整个图，并打印 final_answer。

class LLMNodeState(TypedDict):
    """模型回答流程中各节点共享的状态。"""

    user_question: str  # 用户提出的问题
    draft_answer: str    # 模型生成的初稿
    final_answer: str    # 整理后的最终答复


async def draft_answer_node(state: LLMNodeState) -> dict:
    """调用聊天模型，根据用户问题生成回答初稿。"""

    # 创建 DeepSeek 聊天模型实例，并设置生成温度。
    model = LangChainModelFactory.create(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.3,
    )

    # ainvoke() 是异步调用模型的方法。
    # SystemMessage 指定模型角色和回答风格，
    # HumanMessage 则提供当前用户的问题。
    response = await model.ainvoke([
        SystemMessage(
            content=(
                "你是一个 AI Agent 课程助教。"
                "回答要简洁、口语化。"
            )
        ),
        HumanMessage(
            content=state["user_question"]
        ),
    ])

    # 将模型返回的消息内容保存为草稿。
    return {
        "draft_answer": str(response.content)
    }


async def polish_answer_node(state: LLMNodeState) -> dict:
    """对草稿添加最终回答标记并去除首尾空白。"""
    return {
        "final_answer": (
            "【最终回答】\n"
            + state["draft_answer"].strip()
        )
    }


def build_graph():
    """构建并编译由两个节点组成的回答流程。"""
    graph = StateGraph(LLMNodeState)

    graph.add_node("draft_answer", draft_answer_node)
    graph.add_node("polish_answer", polish_answer_node)

    # 执行顺序：调用模型生成草稿 -> 整理草稿 -> 结束。
    graph.add_edge(START, "draft_answer")
    graph.add_edge("draft_answer", "polish_answer")
    graph.add_edge("polish_answer", END)

    return graph.compile()


async def main():
    """异步运行工作流，并打印最终回答。"""
    app = build_graph()

    # ainvoke() 异步执行图，因此需要使用 await。
    result = await app.ainvoke({
        "user_question": "为什么复杂 Agent 需要 LangGraph？",
        "draft_answer": "",
        "final_answer": "",
    })

    print(result["final_answer"])


# asyncio.run() 创建事件循环并运行异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())