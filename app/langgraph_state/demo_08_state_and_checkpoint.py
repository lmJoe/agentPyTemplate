from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

# State + Checkpoint
# 这段代码演示了如何用 LangGraph 创建一个简单的“用户资料记忆”流程：
# 1. UserProfileState 描述图中共享状态，包含姓名、关注话题和回复。
# 2. remember_name_node 根据姓名生成一条回复。
# 3. remember_topic_node 如果发现关注话题，就把回复更新为话题相关内容；如果没有话题，则不修改回复。
# 4. build_graph() 将两个节点按顺序连接，并配置 InMemorySaver 保存状态。
# 5. main() 用同一个 thread_id 调用图两次：第一次提交姓名，第二次补充关注话题。
# 因此，第一次调用的回复会提到“大伟”；第二次调用补充话题后，流程会重新运行，最终回复会提到“LangGraph State 设计”。

# 注意：第二次运行时，姓名也会从同一条线程的检查点状态中保留；不过话题节点会更新 answer，所以最终的 answer 主要显示关注话题。



# 定义图中共享状态的结构。
# TypedDict 只提供类型提示，不会在运行时强制校验字段。
class UserProfileState(TypedDict):
    user_name: str | None       # 用户姓名；可以暂时没有
    favorite_topic: str | None  # 用户关注的话题；可以暂时没有
    answer: str                 # 节点生成的回复


# 检查状态中是否已经有用户姓名，并生成相应回复。
def remember_name_node(state: UserProfileState) -> dict:
    if state.get("user_name"):
        return {
            # 节点返回的字典会更新图的共享状态
            "answer": f"我记住你的名字了：{state['user_name']}"
        }

    return {
        "answer": "你还没有告诉我你的名字。"
    }


# 检查状态中是否有用户关注的话题。
def remember_topic_node(state: UserProfileState) -> dict:
    if state.get("favorite_topic"):
        return {
            # 有话题时，更新 answer
            "answer": (
                f"我记住了，你关注的话题是：{state['favorite_topic']}。"
            )
        }

    # 没有话题时返回空字典，不更新状态。
    # 因此 answer 会保留上一个节点写入的内容。
    return {}


# 创建并编译 LangGraph 工作流。
def build_graph():
    graph = StateGraph(UserProfileState)

    # 注册两个节点及其对应函数
    graph.add_node("remember_name", remember_name_node)
    graph.add_node("remember_topic", remember_topic_node)

    # 设置执行顺序：开始 → 记住姓名 → 记住话题 → 结束
    graph.add_edge(START, "remember_name")
    graph.add_edge("remember_name", "remember_topic")
    graph.add_edge("remember_topic", END)

    # 使用内存检查点保存每个 thread 的状态。
    # 数据只保存在当前 Python 进程内，进程结束后不会持久保留。
    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


def main():
    app = build_graph()

    # thread_id 用于标识同一条对话/状态轨迹。
    # 第二次调用使用相同的 thread_id，就可以从此前保存的状态继续。
    config = {
        "configurable": {
            "thread_id": "state_checkpoint_demo"
        }
    }

    # 首次调用提供完整的初始状态
    first_result = app.invoke(
        {
            "user_name": "大伟",
            "favorite_topic": None,
            "answer": "",
        },
        config=config,
    )

    print("first_result:")
    print(first_result)

    # 第二次调用只提供要更新的 favorite_topic。
    # 同一 thread_id 会让 LangGraph 基于已保存的状态继续执行。
    second_result = app.invoke(
        {
            "favorite_topic": "LangGraph State 设计",
        },
        config=config,
    )

    print("second_result:")
    print(second_result)


if __name__ == "__main__":
    main()