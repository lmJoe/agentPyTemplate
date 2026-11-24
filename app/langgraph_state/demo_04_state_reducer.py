from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# 这段代码演示了如何在 LangGraph 中用自定义 reducer 合并多个节点产生的来源：
# 1. retrieve_employee_doc_node 返回 employee_handbook。
# 2. retrieve_policy_doc_node 返回 ecommerce_after_sales 和 employee_handbook。
# 3. sources 字段通过 merge_unique_list 合并新旧列表，并去除重复来源。
# 4. answer_node 读取合并后的列表，将来源名称拼成最终回答。



# merge_unique_list 定义了如何把旧的 sources 与节点返回的新 sources 合并，并去掉重复项。
# `Annotated` 将这个合并规则绑定到 sources 字段上，因此检索节点更新该字段时，LangGraph 会调用这个 reducer。
def merge_unique_list(
    old: list[str],
    new: list[str],
) -> list[str]:
    """合并两个列表，并跳过已存在的元素。"""
    # 复制旧列表，避免直接修改原列表
    result = list(old)

    # 按顺序添加新元素，只添加尚未出现的内容
    for item in new:
        if item not in result:
            result.append(item)

    return result


class SourceState(TypedDict):
    """定义文档检索工作流中共享的状态结构。"""

    question: str  # 用户提出的问题

    # merge_unique_list 是 sources 字段的 reducer：
    # 各节点返回的新来源会与已有来源合并，并去除重复项
    sources: Annotated[list[str], merge_unique_list]

    answer: str  # 最终生成的回答


def retrieve_employee_doc_node(state: SourceState) -> dict:
    """模拟检索员工手册，并返回找到的来源。"""
    return {
        "sources": ["employee_handbook"]
    }


def retrieve_policy_doc_node(state: SourceState) -> dict:
    """模拟检索售后规则文档，并返回找到的来源。"""
    return {
        "sources": ["ecommerce_after_sales", "employee_handbook"]
    }


def answer_node(state: SourceState) -> dict:
    """读取合并后的来源列表，生成最终回答。"""
    return {
        "answer": f"最终引用来源：{', '.join(state['sources'])}"
    }


def build_graph():
    """创建并编译文档检索工作流。"""
    graph = StateGraph(SourceState)

    # 注册两个检索节点和一个回答节点
    graph.add_node("retrieve_employee_doc", retrieve_employee_doc_node)
    graph.add_node("retrieve_policy_doc", retrieve_policy_doc_node)
    graph.add_node("answer", answer_node)

    # 按顺序连接节点：开始 → 检索员工手册 → 检索售后规则 → 生成回答 → 结束
    graph.add_edge(START, "retrieve_employee_doc")
    graph.add_edge("retrieve_employee_doc", "retrieve_policy_doc")
    graph.add_edge("retrieve_policy_doc", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def main():
    """运行文档检索示例，并打印完整状态。"""
    app = build_graph()

    # 提供初始问题和空的来源列表
    result = app.invoke({
        "question": "员工售后规则是什么？",
        "sources": [],
        "answer": "",
    })

    print(result)


# 直接运行此文件时执行示例；被其他模块导入时不自动运行
if __name__ == "__main__":
    main()