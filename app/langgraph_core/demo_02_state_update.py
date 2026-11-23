from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ProfileState(TypedDict):
    """定义个人简介工作流中共享的状态结构。"""

    user_name: str  # 用户姓名
    role: str       # 用户角色
    intro: str      # 生成的个人简介


def fill_role_node(state: ProfileState) -> dict:
    """设置用户角色，并将其写入工作流状态。"""
    return {
        "role": "AI Agent 全栈课程学员"
    }


def generate_intro_node(state: ProfileState) -> dict:
    """读取姓名和角色，生成个人简介。"""
    return {
        "intro": f"{state['user_name']} 是一名 {state['role']}。"
    }


def build_graph():
    """创建并编译个人简介工作流。"""
    graph = StateGraph(ProfileState)

    # 注册设置角色和生成简介两个节点
    graph.add_node("fill_role", fill_role_node)
    graph.add_node("generate_intro", generate_intro_node)

    # 设置执行顺序：开始 → 设置角色 → 生成简介 → 结束
    graph.add_edge(START, "fill_role")
    graph.add_edge("fill_role", "generate_intro")
    graph.add_edge("generate_intro", END)

    # 编译后返回可调用的工作流应用
    return graph.compile()


def main():
    """运行工作流并打印处理后的完整状态。"""
    app = build_graph()

    # 传入初始状态；role 和 intro 会由后续节点填充
    result = app.invoke({
        "user_name": "小陈",
        "role": "",
        "intro": "",
    })

    print(result)


# 直接运行此文件时执行 main()；
# 如果此文件被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()