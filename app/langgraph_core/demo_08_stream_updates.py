# 导入前面定义的课程内容生成工作流
from app.langgraph_core.demo_03_sequence_graph import build_graph


# 这段代码调用 build_graph() 创建课程内容生成工作流，并用 app.stream() 逐步输出执行过程。它演示了两种流式输出模式：
# - stream_mode="updates"：每个节点执行后，输出该节点更新的状态字段。例如，大纲节点只会输出 outline 的更新。
# - stream_mode="values"：每个节点执行后，输出当时的完整状态，包含已经生成的内容和仍为空的字段。
# 工作流预计按“大纲 → 重点内容 → 总结”的顺序执行。每次 app.stream() 都会独立运行一次工作流。



def main():
    """运行工作流，并分别演示两种流式输出模式。"""
    app = build_graph()

    # 准备工作流的初始状态
    input_state = {
        "topic": "LangGraph Streaming",
        "outline": "",
        "script": "",
        "summary": "",
    }

    # updates 模式：输出每个节点执行后产生的状态更新
    print("stream_mode=updates")
    print("=" * 80)

    for chunk in app.stream(
        input_state,
        stream_mode="updates",
    ):
        print(chunk)

    print("=" * 80)

    # values 模式：输出工作流每一步执行后的完整状态
    print("stream_mode=values")
    print("=" * 80)

    for chunk in app.stream(
        input_state,
        stream_mode="values",
    ):
        print(chunk)
        print("-" * 80)


# 直接运行此文件时执行 main()；
# 如果此文件被其他模块导入，则不会自动运行。
if __name__ == "__main__":
    main()