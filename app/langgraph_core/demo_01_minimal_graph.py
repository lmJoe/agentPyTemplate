from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 这段代码用 LangGraph 创建了一个最简单的问候流程：
# 1. HelloState 定义流程中共享的数据：用户姓名和问候语。
# 2. greeting_node 读取姓名，生成问候语并写入状态。
# 3. build_graph 将节点连接成 START → greeting → END 的工作流。
# 4. main 传入姓名，调用工作流并打印执行结果。


class HelloState(TypedDict):
    """定义这个工作流共享的状态结构。"""

    user_name: str  # 用户姓名
    greeting: str   # 生成的问候语


def greeting_node(state: HelloState) -> dict:
    """读取用户姓名，生成问候语并更新状态。"""
    user_name = state["user_name"]

    return {
        "greeting": f"你好，{user_name}，欢迎进入 LangGraph 阶段。"
    }


def build_graph():
    """创建并编译问候语工作流。"""
    graph = StateGraph(HelloState)

    # 注册问候语处理节点
    graph.add_node("greeting", greeting_node)

    # 设置流程：从 START 开始，执行 greeting，然后到 END 结束
    graph.add_edge(START, "greeting")
    graph.add_edge("greeting", END)

    # 编译后返回可调用的工作流应用
    return graph.compile()


def main():
    """运行工作流并打印结果。"""
    app = build_graph()

    # 将初始状态传入工作流
    result = app.invoke({
        "user_name": "大伟",
        "greeting": "",
    })

    # 打印工作流执行后的完整状态
    print(result)


# 直接运行此文件时执行 main()；
# 如果被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()