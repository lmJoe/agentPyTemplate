import asyncio
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import (
    create_initial_state,
    mock_search_policy,
)
from app.langgraph_routing.schemas import RoutingState

# 根据 RAG 是否命中路由
# RAG 未命中时，不要让模型硬编。
# 应该走 fallback。
# 路由条件可以是：
# rag_hit=True 且 sources 不为空
#   -> answer_with_sources

# 否则
#   -> fallback
# 这样能明显降低知识库问答编造风险。
# START → 生成检索词 → 检索知识库
#                          ├─ 命中且有来源 → 基于知识库回答
#                          └─ 未命中或没有来源 → 返回兜底提示

# build_policy_query_node：把用户问题转换为检索词。当前对“年假”和“退款”做了简单关键词改写。
# retrieve_policy_node：异步调用模拟知识库服务，并保存答案、命中状态和来源。
# route_after_rag：检查是否命中知识库且返回了来源，据此选择后续节点。
# answer_with_sources_node：生成基于检索结果的回答。
# fallback_node：检索无结果时提示用户联系人工客服。
# main()：用两个示例问题运行图并打印结果。

# 根据用户问题生成适合知识库检索的查询内容。
def build_policy_query_node(state: RoutingState) -> dict:
    question = state["user_question"]

    # 对特定关键词做简单改写；其他问题直接作为检索词。
    if "年假" in question:
        query = "员工年假制度"
    elif "退款" in question:
        query = "订单未发货退款规则"
    else:
        query = question

    # 将检索问题写入状态，并记录处理日志。
    return {
        "policy_query": query,
        "logs": [f"build_policy_query：query={query}"],
    }


# 异步查询政策知识库，并将结果保存到状态中。
async def retrieve_policy_node(state: RoutingState) -> dict:
    result = await mock_search_policy(state["policy_query"])

    return {
        "rag_hit": result["hit"],       # 是否检索到相关内容
        "policy_answer": result["answer"], # 检索得到的答案
        "sources": result["sources"],    # 答案对应的来源列表
        "logs": [f"retrieve_policy：rag_hit={result['hit']}"],
    }


# 根据检索结果决定使用知识库答案，还是进入兜底流程。
def route_after_rag(
    state: RoutingState,
) -> Literal["answer_with_sources", "fallback"]:
    # 只有检索命中且存在来源时，才走基于来源的回答分支。
    if state["rag_hit"] and state["sources"]:
        return "answer_with_sources"

    return "fallback"


# 基于知识库检索结果生成回答。
def answer_with_sources_node(state: RoutingState) -> dict:
    return {
        "final_answer": (
            f"{state['policy_answer']} 回答依据来自知识库。"
        ),
        "is_finished": True,  # 标记本次流程结束
        "logs": ["answer_with_sources：基于知识库回答"],
    }


# 知识库未命中时，给出兜底回复。
def fallback_node(state: RoutingState) -> dict:
    return {
        "final_answer": "根据当前知识库无法确认，建议联系人工客服。",
        "is_finished": True,
        "logs": ["fallback：知识库未命中，进入兜底"],
    }


# 构建并编译政策检索流程图。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中共享状态的类型

    # 注册查询改写、知识库检索和两种回答节点。
    graph.add_node("build_policy_query", build_policy_query_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("answer_with_sources", answer_with_sources_node)
    graph.add_node("fallback", fallback_node)

    # 固定流程：先生成检索词，再查询知识库。
    graph.add_edge(START, "build_policy_query")
    graph.add_edge("build_policy_query", "retrieve_policy")

    # 根据检索结果选择回答节点。
    graph.add_conditional_edges(
        "retrieve_policy",
        route_after_rag,
        {
            "answer_with_sources": "answer_with_sources",
            "fallback": "fallback",
        },
    )

    # 两种回答节点执行后都结束流程。
    graph.add_edge("answer_with_sources", END)
    graph.add_edge("fallback", END)

    return graph.compile()  # 编译图，得到可异步调用的应用


# 异步运行示例问题，并打印检索与回答结果。
async def main():
    app = build_graph()

    questions = [
        "订单未发货可以退款吗？",
        "公司下午茶制度是什么？",
    ]

    for question in questions:
        # ainvoke 异步执行图，并返回运行后的完整状态。
        result = await app.ainvoke(create_initial_state(question))

        print("question:", question)
        print("rag_hit:", result["rag_hit"])
        print("final_answer:", result["final_answer"])
        print("sources:", result["sources"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时启动异步 main 函数。
if __name__ == "__main__":
    asyncio.run(main())