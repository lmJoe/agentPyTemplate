from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# 顺序图 Sequence Graph
# 这段代码用 LangGraph 按顺序生成一份简单的课程内容：
# 1. 根据 topic 生成课程大纲。
# 2. 根据大纲生成重点内容。
# 3. 生成课程总结。
# 4. main() 调用工作流，并打印包含主题、大纲、重点内容和总结的完整状态。

# 代码执行顺序:START → generate_outline → generate_script → generate_summary → END


class LessonState(TypedDict):
    """定义课程内容生成流程中共享的状态结构。"""

    topic: str     # 课程主题
    outline: str   # 生成的课程大纲
    script: str    # 根据大纲生成的重点内容
    summary: str   # 课程总结


def generate_outline_node(state: LessonState) -> dict:
    """根据课程主题生成大纲，并更新 outline 状态。"""
    return {
        "outline": f"《{state['topic']}》课程大纲：概念、代码、项目、总结。"
    }


def generate_script_node(state: LessonState) -> dict:
    """读取课程大纲，生成课程重点内容。"""
    return {
        "script": f"根据大纲生成重点内容：{state['outline']}"
    }


def generate_summary_node(state: LessonState) -> dict:
    """根据课程主题生成本节课总结。"""
    return {
        "summary": f"本节课围绕 {state['topic']}，完成了大纲和重点内容。"
    }


def build_graph():
    """创建并编译课程内容生成工作流。"""
    graph = StateGraph(LessonState)

    # 注册生成大纲、重点内容和总结这三个节点
    graph.add_node("generate_outline", generate_outline_node)
    graph.add_node("generate_script", generate_script_node)
    graph.add_node("generate_summary", generate_summary_node)

    # 按顺序连接节点：开始 → 大纲 → 重点内容 → 总结 → 结束
    graph.add_edge(START, "generate_outline")
    graph.add_edge("generate_outline", "generate_script")
    graph.add_edge("generate_script", "generate_summary")
    graph.add_edge("generate_summary", END)

    # 编译后返回可以调用的工作流应用
    return graph.compile()


def main():
    """运行工作流，并打印执行后的完整状态。"""
    app = build_graph()

    # 提供初始课程主题，其他字段由工作流节点依次填充
    result = app.invoke({
        "topic": "LangGraph 核心概念",
        "outline": "",
        "script": "",
        "summary": "",
    })

    print(result)


# 直接运行此文件时执行 main()；
# 如果此文件被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()