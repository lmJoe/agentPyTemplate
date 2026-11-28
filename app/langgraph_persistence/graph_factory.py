from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.langgraph_persistence.schemas import PersistenceState


# 代码构建了一个用于订单退款咨询的 LangGraph 工作流：
# 1. add_user_message_to_state 将用户问题转换为初始状态。
# 2. classify_intent_node 判断问题意图。
# 3. extract_order_id_node 尝试提取订单号。
# 4. route_after_extract_order_id 根据是否有订单号进行分支：
#    - 缺少订单号：`ask_order_id_node` 请求用户补充，并结束本轮运行。
#    - 已有订单号：查询订单、判断售后规则，再生成最终答复。
# 5. build_persistence_graph 注册节点和连线，并编译工作流。
# 6. build_memory_graph 使用 InMemorySaver 保存运行检查点，可用于同一进程中的多轮交互演示。



def classify_intent_node(state: PersistenceState) -> dict:
    """根据用户问题判断意图，并把结果和日志写入图状态。"""
    question = state["user_question"]

    # 用关键词做简单分类；已有退款意图时，即使当前问题没有“退款”二字也保留该意图
    if "退款" in question or state.get("intent") == "refund":
        intent = "refund"
    elif "订单" in question:
        intent = "query_order"
    elif "人工" in question:
        intent = "human_service"
    else:
        intent = "general"

    # 节点只返回需要更新的字段，由 LangGraph 合并到当前状态
    return {
        "intent": intent,
        "logs": [f"classify_intent：intent={intent}"],
    }


def extract_order_id_node(state: PersistenceState) -> dict:
    """从问题中提取示例订单号；没有提取到时沿用状态中已有的订单号。"""
    question = state["user_question"]

    # 示例代码只识别两个固定订单号，实际项目中可替换为正则或专门的提取逻辑
    if "10001" in question:
        order_id = "10001"
    elif "10002" in question:
        order_id = "10002"
    else:
        order_id = state.get("order_id")

    return {
        "order_id": order_id,
        "logs": [f"extract_order_id：order_id={order_id}"],
    }


def route_after_extract_order_id(
    state: PersistenceState,
) -> Literal["ask_order_id", "query_order"]:
    """根据订单号是否已知，决定接下来询问用户还是查询订单。"""
    if not state["order_id"]:
        return "ask_order_id"

    return "query_order"


def ask_order_id_node(state: PersistenceState) -> dict:
    """订单号缺失时，请用户补充订单号，并将流程标记为等待输入。"""
    answer = "请您提供订单号，我才能继续处理退款申请。"

    return {
        # 标记当前正在等待用户补充订单号
        "need_user_input": True,
        "waiting_for": "order_id",
        "final_answer": answer,
        # 当前轮结束，但整个对话任务尚未完成
        "is_finished": False,
        # 将回复加入对话消息历史
        "messages": [
            AIMessage(content=answer)
        ],
        "logs": ["ask_order_id：等待用户补充订单号"],
    }


def query_order_node(state: PersistenceState) -> dict:
    """根据订单号查询订单状态；这里使用固定数据模拟查询结果。"""
    order_id = state["order_id"]

    if order_id == "10001":
        order_status = "已发货"
    elif order_id == "10002":
        order_status = "已付款，待发货"
    else:
        order_status = "未查询到订单"

    return {
        "order_status": order_status,
        # 查询完成后，不再等待用户提供信息
        "need_user_input": False,
        "waiting_for": None,
        "logs": [f"query_order：order_status={order_status}"],
    }


def retrieve_policy_node(state: PersistenceState) -> dict:
    """根据订单状态匹配退款或售后规则说明。"""
    order_status = state["order_status"]

    if order_status == "已付款，待发货":
        policy_answer = "根据售后规则，订单未发货时可以申请取消订单并退款。"
    elif order_status == "已发货":
        policy_answer = "根据售后规则，订单已发货后，需要收到商品后再发起退货退款申请。"
    else:
        policy_answer = "当前订单状态无法确认退款规则，建议联系人工客服。"

    return {
        "policy_answer": policy_answer,
        "logs": ["retrieve_policy：完成售后规则判断"],
    }


def generate_answer_node(state: PersistenceState) -> dict:
    """组合订单状态和规则说明，生成最终答复并结束流程。"""
    answer = (
        f"您的订单当前状态是：{state['order_status']}。"
        f"{state['policy_answer']}"
    )

    return {
        "final_answer": answer,
        "is_finished": True,
        # 把最终答复加入对话消息历史
        "messages": [
            AIMessage(content=answer)
        ],
        "logs": ["generate_answer：最终回答完成"],
    }


def build_persistence_graph(
    checkpointer=None,
):
    """创建并编译订单退款处理图；可传入检查点保存器以启用状态持久化。"""
    graph = StateGraph(PersistenceState)

    # 注册各个处理节点
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_order_id", extract_order_id_node)
    graph.add_node("ask_order_id", ask_order_id_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("generate_answer", generate_answer_node)

    # 设定主流程：开始 → 意图分类 → 提取订单号
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "extract_order_id")

    # 提取订单号后进行条件路由：缺少订单号就询问，否则查询订单
    graph.add_conditional_edges(
        "extract_order_id",
        route_after_extract_order_id,
        {
            "ask_order_id": "ask_order_id",
            "query_order": "query_order",
        },
    )

    # 订单查询后判断规则，再生成答复
    graph.add_edge("query_order", "retrieve_policy")
    graph.add_edge("retrieve_policy", "generate_answer")

    # 两条分支各自在对应节点结束
    graph.add_edge("ask_order_id", END)
    graph.add_edge("generate_answer", END)

    # 编译工作流；如果提供了 checkpointer，图运行时会保存检查点
    return graph.compile(checkpointer=checkpointer)


def build_memory_graph():
    """构建使用内存检查点的图，适合演示或单进程内的短期状态保存。"""
    checkpointer = InMemorySaver()

    return build_persistence_graph(
        checkpointer=checkpointer,
    )


def add_user_message_to_state(
    user_question: str,
) -> dict:
    """把用户问题转换成图的初始状态更新，包含问题文本和人类消息。"""
    return {
        "user_question": user_question,
        "messages": [
            HumanMessage(content=user_question)
        ],
    }