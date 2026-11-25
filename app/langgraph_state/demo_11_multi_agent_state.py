import operator
from typing import Annotated, TypedDict

# LangGraph 图的入口、出口和状态图构造器。
from langgraph.graph import END, START, StateGraph


class MultiAgentState(TypedDict):
    """多个工作节点之间共享的任务状态。"""

    task: str

    # 任务计划。operator.add 表示多个节点写入的列表会拼接起来。
    plan: Annotated[list[str], operator.add]

    # 记录当前正在执行的角色或节点名称。
    current_agent: str

    # 各阶段的输出；尚未完成时可以是 None。
    research_result: str | None
    analysis_result: str | None
    review_result: str | None

    # 最终汇总报告。
    final_report: str

    # 执行日志。各节点返回的日志会追加到列表中。
    logs: Annotated[list[str], operator.add]


def planner_node(state: MultiAgentState) -> dict:
    """拆解任务并生成执行计划。"""
    return {
        "current_agent": "planner",
        "plan": [
            "检索行业资料",
            "分析核心趋势",
            "生成总结报告",
            "检查报告质量",
        ],
        "logs": ["planner：完成任务拆解"],
    }


def researcher_node(state: MultiAgentState) -> dict:
    """模拟检索行业资料并记录检索结果。"""
    return {
        "current_agent": "researcher",
        "research_result": "检索到 3 条与 AI Agent 平台相关的行业趋势。",
        "logs": ["researcher：完成资料检索"],
    }


def analyst_node(state: MultiAgentState) -> dict:
    """根据研究结果生成趋势分析。"""
    return {
        "current_agent": "analyst",
        "analysis_result": "核心趋势是企业从单点 Chatbot 转向多 Agent 工作流平台。",
        "logs": ["analyst：完成趋势分析"],
    }


def reviewer_node(state: MultiAgentState) -> dict:
    """模拟检查报告质量。"""
    return {
        "current_agent": "reviewer",
        "review_result": "报告结构完整，可以输出。",
        "logs": ["reviewer：完成质量检查"],
    }


def report_node(state: MultiAgentState) -> dict:
    """汇总各阶段结果，生成最终报告。"""
    return {
        "current_agent": "reporter",
        "final_report": (
            f"任务：{state['task']}\n"
            f"研究结果：{state['research_result']}\n"
            f"分析结论：{state['analysis_result']}\n"
            f"审核意见：{state['review_result']}"
        ),
        "logs": ["reporter：完成最终报告"],
    }


def build_graph():
    """构建并编译多角色协作工作流。"""
    graph = StateGraph(MultiAgentState)

    # 将各角色对应的处理函数注册为图节点。
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("reporter", report_node)

    # 设置固定执行顺序：
    # 规划 -> 检索 -> 分析 -> 审核 -> 汇总报告。
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "reviewer")
    graph.add_edge("reviewer", "reporter")
    graph.add_edge("reporter", END)

    # 编译后返回可通过 invoke() 执行的应用。
    return graph.compile()


def main():
    """运行示例任务并打印报告、计划和日志。"""
    app = build_graph()

    # 传入完整的初始状态，启动工作流。
    result = app.invoke({
        "task": "分析 AI Agent 平台趋势",
        "plan": [],
        "current_agent": "",
        "research_result": None,
        "analysis_result": None,
        "review_result": None,
        "final_report": "",
        "logs": [],
    })

    print("final_report:")
    print(result["final_report"])

    print("=" * 80)
    print("plan:")
    for item in result["plan"]:
        print("-", item)

    print("=" * 80)
    print("logs:")
    for log in result["logs"]:
        print("-", log)


# 直接运行该文件时执行 main()；被导入时不会自动执行。
if __name__ == "__main__":
    main()