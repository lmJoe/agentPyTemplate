from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.langgraph_routing.mock_services import create_initial_state
from app.langgraph_routing.schemas import RoutingState


# 缺少订单号路由
# 这段代码展示了一个“提取订单号，再根据结果分流”的流程：
# START → 提取订单号 → 找到订单号：进入查询分支
#                      → 没找到：请用户提供订单号
# route_after_extract_order_id 会读取状态中的 order_id，并返回分支名称。LangGraph 再根据 add_conditional_edges 中的映射，跳转到对应节点。



# 从用户问题中提取订单号。
# 此示例只识别 10001 和 10002，实际项目中可以改用正则表达式或专门的提取逻辑。
def extract_order_id_node(state: RoutingState) -> dict:
    question = state["user_question"]

    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = None  # 没找到支持的订单号

    # 返回要更新的状态字段，并记录提取结果。
    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：order_id={order_id}"],
    }


# 根据是否成功提取订单号，决定下一步走哪个分支。
def route_after_extract_order_id(
    state: RoutingState,
) -> Literal["ask_order_id", "query_order"]:
    if not state["order_id"]:
        return "ask_order_id"  # 没有订单号，向用户追问

    return "query_order"  # 找到订单号，进入订单查询分支


# 缺少订单号时，提示用户补充。
def ask_order_id_node(state: RoutingState) -> dict:
    return {
        "final_answer": "请您提供订单号，我才能继续查询。",
        "is_finished": True,  # 本轮流程已结束，等待用户补充信息
        "logs": ["ask_order_id：缺少订单号，追问用户"],
    }


# 找到订单号后的占位节点。
# 当前只提示订单号已提取，尚未实际调用订单查询服务。
def query_order_entry_node(state: RoutingState) -> dict:
    return {
        "final_answer": f"已提取订单号 {state['order_id']}，下一步可以查询订单。",
        "logs": ["query_order_entry：进入订单查询流程"],
    }


# 构建并编译订单号提取流程。
def build_graph():
    graph = StateGraph(RoutingState)  # 指定图中使用的共享状态结构

    # 注册节点及其处理函数。
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("ask_order_id", ask_order_id_node)
    graph.add_node("query_order_entry", query_order_entry_node)

    # 设置入口，从订单号提取节点开始。
    graph.add_edge(START, "extract_order_id")

    # 根据提取结果选择后续节点。
    graph.add_conditional_edges(
        "extract_order_id",
        route_after_extract_order_id,
        {
            "ask_order_id": "ask_order_id",
            "query_order": "query_order_entry",
        },
    )

    # 两个分支处理完后都结束本次流程。
    graph.add_edge("ask_order_id", END)
    graph.add_edge("query_order_entry", END)

    return graph.compile()  # 编译图，得到可调用的应用


# 运行示例问题并打印提取结果。
def main():
    app = build_graph()

    questions = [
        "帮我查一下订单 10001。",
        "帮我查一下订单。",
    ]

    for question in questions:
        # 为当前问题创建初始状态并运行图。
        result = app.invoke(create_initial_state(question))

        print("question:", question)
        print("order_id:", result["order_id"])
        print("final_answer:", result["final_answer"])
        print("logs:", result["logs"])
        print("=" * 80)


# 直接运行此文件时执行示例；被导入时不自动运行。
if __name__ == "__main__":
    main()