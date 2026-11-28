from app.langgraph_persistence.graph_factory import (
    add_user_message_to_state,
    build_memory_graph,
)
from app.langgraph_persistence.schemas import create_initial_state

# 方法作用
# - build_thread_id：组合租户、用户和会话 ID，形成会话线程标识。
# - build_config：构造 LangGraph 需要的线程配置。
# - start_refund_flow：创建初始状态并启动退款流程。
# - continue_flow：向已有线程提交新消息并继续执行流程。
# - get_current_state：读取线程当前的状态快照。


class LangGraphPersistenceService:
    def __init__(self):
        # 教学示例使用内存检查点存储器。
        # 应用退出后，内存中的状态通常不会保留。
        # 生产环境可根据需要替换为 PostgresSaver 或 AsyncPostgresSaver。
        self.graph = build_memory_graph()

    def build_thread_id(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> str:
        # 将租户、用户和会话 ID 组合起来，
        # 为每个租户下的每个用户会话生成独立的线程标识。
        return f"{tenant_id}:{user_id}:{conversation_id}"

    def build_config(self, thread_id: str) -> dict:
        # LangGraph 通过 configurable.thread_id 找到对应的线程状态。
        return {
            "configurable": {
                "thread_id": thread_id
            }
        }

    def start_refund_flow(
        self,
        user_question: str,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> dict:
        # 根据租户、用户和会话信息生成线程 ID
        thread_id = self.build_thread_id(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        # 构造本次图执行所需的配置
        config = self.build_config(thread_id)

        # 创建初始状态并执行图，启动一轮新的退款流程。
        # 返回值是图执行结束后的状态。
        return self.graph.invoke(
            create_initial_state(user_question),
            config=config,
        )

    def continue_flow(
        self,
        user_question: str,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> dict:
        # 生成与之前相同的线程 ID，以便找到该会话已有的状态
        thread_id = self.build_thread_id(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        config = self.build_config(thread_id)

        # 将新用户消息追加到已有状态，并继续执行图。
        # 是否正确追加消息，取决于 add_user_message_to_state 的实现
        # 以及图状态中消息字段配置的更新方式。
        return self.graph.invoke(
            add_user_message_to_state(user_question),
            config=config,
        )

    def get_current_state(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> dict:
        # 定位要查询的会话线程
        thread_id = self.build_thread_id(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        config = self.build_config(thread_id)

        # 获取该线程最近一次保存的状态快照
        snapshot = self.graph.get_state(config)

        # 整理并返回常用状态信息
        return {
            "thread_id": thread_id,    # 当前线程标识
            "values": snapshot.values,  # 图中保存的状态数据
            "next": snapshot.next,      # 接下来待执行的节点
            "config": snapshot.config,  # 快照关联的配置
        }


# 创建服务实例，供应用其他部分导入并调用
langgraph_persistence_service = LangGraphPersistenceService()